"""Validate manually supplied labels without modifying the annotation file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from src.label_validation import validate_labels


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.labels, dtype=str, keep_default_na=False)
    config = yaml.safe_load(Path("config/brand.yaml").read_text(encoding="utf-8"))
    result = validate_labels(frame, set(config["intents"]))
    output = {
        "rows": result.row_count,
        "empty_rows": result.empty_rows,
        "invalid_labels": result.invalid_labels,
        "duplicate_message_ids": result.duplicate_message_ids,
        "duplicate_texts": result.duplicate_texts,
        "suspicious_rows": result.suspicious_rows,
        "valid": result.valid,
    }
    print(json.dumps(output, indent=2))
    if not result.valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()