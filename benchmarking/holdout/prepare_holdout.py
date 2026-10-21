"""Validate reviewed records and create an immutable private holdout package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEV_CASHFLOW = ROOT / "benchmarking" / "cashflow_categorization_test_set.json"

CATEGORIES = {
    "Food & Dining", "Groceries", "Transport", "Shopping", "Utilities",
    "Entertainment", "Healthcare", "Investment", "Rent", "Salary/Income",
    "Transfer", "Other", "EMI",
}
ANOMALY_TYPES = {
    "amount_spike", "duplicate_transaction", "large_round_transfer",
    "odd_hour", "unusual_category_first_seen", "other_confirmed",
}
REQUIRED = {
    "record_id", "account_id", "tx_date", "occurred_at", "description",
    "amount", "tx_type", "expected_category", "is_anomaly", "anomaly_type",
    "label_confidence", "reviewer_id", "reviewer_independent",
    "adjudication_status", "consent_confirmed", "data_origin",
}
FEATURE_FIELDS = (
    "record_id", "account_id", "tx_date", "occurred_at", "description",
    "amount", "tx_type",
)
LABEL_FIELDS = ("record_id", "expected_category", "is_anomaly", "anomaly_type")

PII_PATTERNS = {
    "email": re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b", re.I),
    "upi_handle": re.compile(r"\b[a-z0-9._-]{2,}@[a-z][a-z0-9.-]{1,}\b", re.I),
    "phone": re.compile(r"(?<!\d)(?:\+?91[- ]?)?[6-9]\d{9}(?!\d)"),
    "pan": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.I),
    "long_number": re.compile(r"(?<!\d)\d{10,18}(?!\d)"),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalise_description(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _boolean(value: str, field: str, row_number: int) -> bool:
    lowered = value.strip().casefold()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    raise ValueError(f"row {row_number}: {field} must be true or false")


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED - fields
        if missing:
            raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
        rows = [{key: str(value or "").strip() for key, value in row.items()} for row in reader]
    if not rows:
        raise ValueError("input contains no records")
    return rows


def _development_descriptions() -> set[str]:
    data = json.loads(DEV_CASHFLOW.read_text(encoding="utf-8"))
    return {
        _normalise_description(str(row["raw_description"]))
        for row in data.get("transactions", [])
    }


def _validate(rows: list[dict[str, str]], allow_small: bool) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    ids: set[str] = set()
    accounts: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    anomalies: Counter[str] = Counter()
    overlap = 0
    low_confidence = 0
    single_review = 0
    synthetic_rows = 0
    development_descriptions = _development_descriptions()

    for number, row in enumerate(rows, start=2):
        rid = row["record_id"]
        if not rid or rid == "EXAMPLE_REMOVE_ME":
            errors.append(f"row {number}: replace the template example with a unique record_id")
        elif rid in ids:
            errors.append(f"row {number}: duplicate record_id {rid!r}")
        ids.add(rid)

        account = row["account_id"]
        if not re.fullmatch(r"acct_[A-Za-z0-9_-]+", account):
            errors.append(f"row {number}: account_id must be a pseudonym beginning with acct_")
        accounts[account] += 1

        try:
            datetime.strptime(row["tx_date"], "%Y-%m-%d")
        except ValueError:
            errors.append(f"row {number}: tx_date must use YYYY-MM-DD")

        parsed_time = None
        if row["occurred_at"]:
            try:
                parsed_time = datetime.fromisoformat(row["occurred_at"].replace("Z", "+00:00"))
                if parsed_time.utcoffset() is None:
                    raise ValueError
            except ValueError:
                errors.append(f"row {number}: occurred_at must be ISO 8601 with a timezone offset")

        try:
            if float(row["amount"]) <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"row {number}: amount must be a positive number")
        if row["tx_type"] not in {"debit", "credit"}:
            errors.append(f"row {number}: tx_type must be debit or credit")

        category = row["expected_category"]
        if category not in CATEGORIES:
            errors.append(f"row {number}: unsupported expected_category {category!r}")
        categories[category] += 1

        try:
            is_anomaly = _boolean(row["is_anomaly"], "is_anomaly", number)
            consent = _boolean(row["consent_confirmed"], "consent_confirmed", number)
            independent = _boolean(row["reviewer_independent"], "reviewer_independent", number)
        except ValueError as exc:
            errors.append(str(exc))
            is_anomaly, consent, independent = False, False, False
        if not consent:
            errors.append(f"row {number}: consent_confirmed must be true")
        if not independent:
            errors.append(f"row {number}: final labels require an independent reviewer")
        anomaly_type = row["anomaly_type"]
        if is_anomaly and anomaly_type not in ANOMALY_TYPES:
            errors.append(f"row {number}: positive anomaly requires a supported anomaly_type")
        if not is_anomaly and anomaly_type:
            errors.append(f"row {number}: normal record must leave anomaly_type blank")
        if anomaly_type in {"odd_hour", "duplicate_transaction"} and parsed_time is None:
            errors.append(f"row {number}: {anomaly_type} requires occurred_at with timezone")
        if is_anomaly:
            anomalies[anomaly_type] += 1

        if row["label_confidence"] not in {"high", "medium", "low"}:
            errors.append(f"row {number}: label_confidence must be high, medium, or low")
        if row["label_confidence"] == "low":
            low_confidence += 1
        if row["adjudication_status"] not in {"single_review", "adjudicated"}:
            errors.append(f"row {number}: invalid adjudication_status")
        if row["adjudication_status"] == "single_review":
            single_review += 1
        if not re.fullmatch(r"reviewer_[A-Za-z0-9_-]+", row["reviewer_id"]):
            errors.append(f"row {number}: reviewer_id must be a pseudonym beginning with reviewer_")
        if row["data_origin"] not in {"real_deidentified", "synthetic"}:
            errors.append(f"row {number}: data_origin must be real_deidentified or synthetic")
        if row["data_origin"] == "synthetic":
            synthetic_rows += 1

        description = row["description"]
        if not description:
            errors.append(f"row {number}: description is required")
        for pii_name, pattern in PII_PATTERNS.items():
            if pattern.search(description):
                errors.append(f"row {number}: description may contain {pii_name}; redact it")
        if _normalise_description(description) in development_descriptions:
            overlap += 1

    if any(count < 20 for count in accounts.values()):
        warnings.append("one or more accounts have fewer than 20 records; Guardian will use its small-sample rule")
    if overlap:
        warnings.append(f"{overlap} rows exactly match descriptions in the exposed synthetic development set")
    if len(rows) < 500:
        warnings.append(f"only {len(rows)} records supplied; 500 or more are recommended for a final paper run")
    if sum(anomalies.values()) < 30:
        warnings.append("fewer than 30 confirmed anomalies supplied")
    if low_confidence:
        warnings.append(f"{low_confidence} rows have low-confidence labels")
    if single_review:
        warnings.append(f"{single_review} rows have not been adjudicated")
    if synthetic_rows:
        warnings.append(f"{synthetic_rows} rows are synthetic; this package cannot establish real-world accuracy")
    low_support = sorted(name for name, count in categories.items() if count < 20)
    if low_support:
        warnings.append("category support below 20: " + ", ".join(low_support))

    if errors:
        raise ValueError("holdout validation failed:\n- " + "\n- ".join(errors))
    if warnings and not allow_small:
        raise ValueError(
            "holdout has quality warnings; address them or use --allow-small for a diagnostic-only package:\n- "
            + "\n- ".join(warnings)
        )
    return {
        "record_count": len(rows),
        "account_count": len(accounts),
        "records_per_account": dict(sorted(accounts.items())),
        "category_support": dict(sorted(categories.items())),
        "anomaly_support": dict(sorted(anomalies.items())),
        "development_description_overlap_count": overlap,
        "synthetic_row_count": synthetic_rows,
        "warnings": warnings,
        "diagnostic_only": bool(warnings),
    }


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows)


def prepare(input_path: Path, output_dir: Path, allow_small: bool = False) -> Path:
    rows = _read_rows(input_path)
    summary = _validate(rows, allow_small)
    output_dir.mkdir(parents=True, exist_ok=False)
    features_path = output_dir / "features.csv"
    labels_path = output_dir / "labels.csv"
    _write_csv(features_path, FEATURE_FIELDS, rows)
    _write_csv(labels_path, LABEL_FIELDS, rows)
    manifest = {
        "format_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_file_sha256": _sha256(input_path),
        "features_sha256": _sha256(features_path),
        "labels_sha256": _sha256(labels_path),
        "category_taxonomy": sorted(CATEGORIES),
        "anomaly_taxonomy": sorted(ANOMALY_TYPES),
        **summary,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-small", action="store_true", help="create a diagnostic-only package despite support warnings")
    args = parser.parse_args()
    manifest = prepare(args.input.resolve(), args.output.resolve(), args.allow_small)
    print(f"Locked holdout package created: {manifest.parent}")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
