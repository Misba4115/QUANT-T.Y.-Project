"""End-to-end checks for the private holdout packaging workflow."""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from benchmarking.generate_synthetic_stress import generate
from benchmarking.holdout.evaluate_holdout import evaluate
from benchmarking.holdout.prepare_holdout import REQUIRED, prepare


def _reviewed_csv(path: Path, rows: int = 40) -> Path:
    fields = sorted(REQUIRED)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index in range(rows):
            anomaly = index == rows - 1
            writer.writerow({
                "record_id": f"holdout_{index:03d}",
                "account_id": "acct_private_a",
                "tx_date": f"2026-01-{index % 28 + 1:02d}",
                "occurred_at": f"2026-01-{index % 28 + 1:02d}T10:30:00+05:30",
                "description": f"Independent merchant alpha {index}",
                "amount": "50000" if anomaly else str(100 + index),
                "tx_type": "debit",
                "expected_category": "Other",
                "is_anomaly": str(anomaly).lower(),
                "anomaly_type": "amount_spike" if anomaly else "",
                "label_confidence": "high",
                "reviewer_id": "reviewer_external",
                "reviewer_independent": "true",
                "adjudication_status": "adjudicated",
                "consent_confirmed": "true",
                "data_origin": "real_deidentified",
            })
    return path


def test_prepare_and_evaluate_diagnostic_package(tmp_path: Path):
    source = _reviewed_csv(tmp_path / "reviewed.csv")
    package = tmp_path / "sealed"
    manifest_path = prepare(source, package, allow_small=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["record_count"] == 40
    assert manifest["diagnostic_only"] is True

    result_path = evaluate(package, tmp_path / "result.json", diagnostic=True)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["evaluation_type"] == "diagnostic_holdout"
    assert result["cashflow_categorization"]["total"] == 40
    assert result["guardian"]["account_count"] == 1
    assert "false_alerts_per_1000_normal_transactions" in result["guardian"]


def test_tampered_labels_are_rejected(tmp_path: Path):
    source = _reviewed_csv(tmp_path / "reviewed.csv")
    package = tmp_path / "sealed"
    prepare(source, package, allow_small=True)
    with (package / "labels.csv").open("a", encoding="utf-8") as handle:
        handle.write("tampered,Other,false,\n")
    with pytest.raises(ValueError, match="locked manifest"):
        evaluate(package, tmp_path / "result.json", diagnostic=True)


def test_direct_identifiers_are_rejected(tmp_path: Path):
    source = _reviewed_csv(tmp_path / "reviewed.csv")
    text = source.read_text(encoding="utf-8").replace(
        "Independent merchant alpha 0", "send to person@example.com"
    )
    source.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="may contain"):
        prepare(source, tmp_path / "sealed", allow_small=True)


def test_synthetic_generator_is_seeded_and_marks_origin():
    first = generate(42, 2, 20, date(2025, 1, 1))
    second = generate(42, 2, 20, date(2025, 1, 1))
    assert first == second
    assert all(row["data_origin"] == "synthetic" for row in first)
    assert {row["anomaly_type"] for row in first if row["is_anomaly"] == "true"} >= {
        "amount_spike", "duplicate_transaction", "odd_hour"
    }
