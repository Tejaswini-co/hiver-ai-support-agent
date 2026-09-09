"""Evaluate escalation only when independent expected decisions are supplied."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True, help="CSV with example_id, expected_decision, predicted_decision")
    parser.add_argument("--output", default="reports/escalation_results.json")
    args = parser.parse_args()
    frame = pd.read_csv(args.labels, dtype=str, keep_default_na=False)
    required = {"example_id", "expected_decision", "predicted_decision"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if frame.empty or frame[["expected_decision", "predicted_decision"]].eq("").any().any():
        raise ValueError("Independent expected escalation labels are required")
    valid = {"AUTO_HANDLE", "ESCALATE"}
    if not set(frame["expected_decision"]).issubset(valid) or not set(frame["predicted_decision"]).issubset(valid):
        raise ValueError("Decisions must be AUTO_HANDLE or ESCALATE")
    actual = frame["expected_decision"]
    predicted = frame["predicted_decision"]
    result = {
        "examples": len(frame),
        "accuracy": accuracy_score(actual, predicted),
        "per_class": classification_report(actual, predicted, labels=sorted(valid), output_dict=True, zero_division=0),
        "confusion_matrix_labels": sorted(valid),
        "confusion_matrix": confusion_matrix(actual, predicted, labels=sorted(valid)).tolist(),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()