"""Evaluate a sealed holdout package against production component code."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from services.guardian_detector import detect_anomalies  # noqa: E402
from services.statement_parser import categorise  # noqa: E402

CATEGORY_ALIASES = {"Food": "Food & Dining", "Salary": "Salary/Income"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _git_state() -> dict[str, object]:
    def git(*args: str) -> str:
        result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    return {
        "commit": git("rev-parse", "HEAD"),
        "working_tree_dirty": bool(git("status", "--porcelain")),
    }


def _wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    if total == 0:
        return None
    rate = successes / total
    denominator = 1 + z * z / total
    centre = (rate + z * z / (2 * total)) / denominator
    spread = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / denominator
    return [round(max(0.0, centre - spread), 4), round(min(1.0, centre + spread), 4)]


def _safe_rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def _f1(tp: int, fp: int, fn: int) -> float | None:
    denominator = 2 * tp + fp + fn
    return round(2 * tp / denominator, 4) if denominator else None


def _categorization(features: list[dict[str, str]], labels: dict[str, dict[str, str]]) -> dict[str, object]:
    pairs = []
    for row in features:
        expected = labels[row["record_id"]]["expected_category"]
        raw_prediction = categorise(row["description"])
        predicted = CATEGORY_ALIASES.get(raw_prediction, raw_prediction)
        pairs.append((expected, predicted))

    classes = sorted({expected for expected, _ in pairs})
    per_class: dict[str, dict[str, object]] = {}
    f1_values = []
    weighted_sum = 0.0
    for category in classes:
        tp = sum(expected == category and predicted == category for expected, predicted in pairs)
        fp = sum(expected != category and predicted == category for expected, predicted in pairs)
        fn = sum(expected == category and predicted != category for expected, predicted in pairs)
        support = tp + fn
        score = _f1(tp, fp, fn)
        if score is not None:
            f1_values.append(score)
            weighted_sum += score * support
        per_class[category] = {
            "support": support,
            "precision": _safe_rate(tp, tp + fp),
            "recall": _safe_rate(tp, support),
            "f1": score,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }
    correct = sum(expected == predicted for expected, predicted in pairs)
    return {
        "total": len(pairs),
        "correct": correct,
        "accuracy": _safe_rate(correct, len(pairs)),
        "accuracy_95ci": _wilson(correct, len(pairs)),
        "macro_f1_supported_classes": round(sum(f1_values) / len(f1_values), 4) if f1_values else None,
        "weighted_f1": round(weighted_sum / len(pairs), 4) if pairs else None,
        "per_class": per_class,
    }


def _guardian(features: list[dict[str, str]], labels: dict[str, dict[str, str]]) -> dict[str, object]:
    accounts: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in features:
        accounts[row["account_id"]].append(row)

    outcomes = []
    modes: Counter[str] = Counter()
    versions: Counter[str] = Counter()
    for account_id, rows in sorted(accounts.items()):
        rows.sort(key=lambda item: (item["occurred_at"] or item["tx_date"], item["record_id"]))
        records = []
        for row in rows:
            predicted_category = categorise(row["description"])
            detector_row: dict[str, object] = {
                "tx_date": row["tx_date"],
                "description": row["description"],
                "amount": float(row["amount"]),
                "account_id": account_id,
                "category": CATEGORY_ALIASES.get(predicted_category, predicted_category),
            }
            if row["occurred_at"]:
                parsed = datetime.fromisoformat(row["occurred_at"].replace("Z", "+00:00"))
                detector_row["occurred_at"] = row["occurred_at"]
                detector_row["occurred_local_hour"] = parsed.hour
            records.append(("bank_transactions", detector_row, float(row["amount"])))
        flags, scores, _reasons, mode, version = detect_anomalies(records)
        modes[mode] += 1
        versions[version] += 1
        for row, flag, score in zip(rows, flags.tolist(), scores.tolist()):
            label = labels[row["record_id"]]
            truth = label["is_anomaly"].casefold() == "true"
            outcomes.append((truth, bool(flag), float(score), label["anomaly_type"] or "normal"))

    tp = sum(truth and predicted for truth, predicted, _, _ in outcomes)
    fp = sum(not truth and predicted for truth, predicted, _, _ in outcomes)
    fn = sum(truth and not predicted for truth, predicted, _, _ in outcomes)
    tn = sum(not truth and not predicted for truth, predicted, _, _ in outcomes)
    anomaly_types = sorted({kind for _, _, _, kind in outcomes if kind != "normal"})
    per_type = {}
    for kind in anomaly_types:
        supported = [(truth, predicted) for truth, predicted, _, actual_kind in outcomes if actual_kind == kind]
        detected = sum(predicted for _, predicted in supported)
        per_type[kind] = {
            "support": len(supported),
            "detected": detected,
            "recall": _safe_rate(detected, len(supported)),
            "recall_95ci": _wilson(detected, len(supported)),
        }
    return {
        "total": len(outcomes),
        "account_count": len(accounts),
        "accounts_by_detector_mode": dict(modes),
        "model_versions": dict(versions),
        "confusion_counts": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": _safe_rate(tp, tp + fp),
        "precision_95ci": _wilson(tp, tp + fp),
        "recall": _safe_rate(tp, tp + fn),
        "recall_95ci": _wilson(tp, tp + fn),
        "f1": _f1(tp, fp, fn),
        "false_positive_rate": _safe_rate(fp, fp + tn),
        "false_positive_rate_95ci": _wilson(fp, fp + tn),
        "false_alerts_per_1000_normal_transactions": round(1000 * fp / (fp + tn), 2) if fp + tn else None,
        "per_anomaly_type": per_type,
    }


def evaluate(package: Path, output: Path, diagnostic: bool = False) -> Path:
    manifest_path = package / "manifest.json"
    features_path = package / "features.csv"
    labels_path = package / "labels.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if _sha256(features_path) != manifest["features_sha256"]:
        raise ValueError("features.csv does not match the locked manifest")
    if _sha256(labels_path) != manifest["labels_sha256"]:
        raise ValueError("labels.csv does not match the locked manifest")

    state = _git_state()
    if state["working_tree_dirty"] and not diagnostic:
        raise ValueError("working tree is dirty; commit the frozen implementation or use --diagnostic")
    if manifest.get("diagnostic_only") and not diagnostic:
        raise ValueError("package is marked diagnostic_only; prepare a sufficiently supported final package")

    features = _read_csv(features_path)
    label_rows = _read_csv(labels_path)
    labels = {row["record_id"]: row for row in label_rows}
    feature_ids = {row["record_id"] for row in features}
    if feature_ids != set(labels):
        raise ValueError("feature and label record IDs differ")

    result = {
        "evaluation_type": "diagnostic_holdout" if diagnostic else "independent_locked_holdout",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "implementation": state,
        "package": {
            "manifest_sha256": _sha256(manifest_path),
            "features_sha256": manifest["features_sha256"],
            "labels_sha256": manifest["labels_sha256"],
            "record_count": manifest["record_count"],
            "account_count": manifest["account_count"],
            "development_description_overlap_count": manifest["development_description_overlap_count"],
            "synthetic_row_count": manifest["synthetic_row_count"],
            "warnings": manifest["warnings"],
        },
        "cashflow_categorization": _categorization(features, labels),
        "guardian": _guardian(features, labels),
        "limitations": [
            "Guardian is evaluated as one retrospective production-style scan per account, not as a prospective online trial.",
            "Confidence intervals are Wilson intervals for binomial proportions and do not model account-level clustering.",
            "Results are publishable as independent holdout evidence only if collection, consent, label freezing, and no-tuning requirements were followed.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic", action="store_true", help="allow a dirty tree or small diagnostic package")
    args = parser.parse_args()
    result = evaluate(args.package.resolve(), args.output.resolve(), args.diagnostic)
    print(f"Holdout evaluation written to: {result}")


if __name__ == "__main__":
    main()
