"""Inspect source files and rank candidate brands without selecting one silently."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data_loader import discover_files, read_many
from src.preprocessing import detect_columns


def build_report(input_path: str, sample_rows: int | None) -> dict[str, object]:
    files = discover_files(input_path)
    frame = read_many(files, nrows=sample_rows)
    detected = detect_columns([str(column) for column in frame.columns])
    report: dict[str, object] = {
        "input_files": [str(path) for path in files],
        "rows_loaded": int(len(frame)),
        "columns": [str(column) for column in frame.columns],
        "detected_columns": detected,
        "candidate_brands": [],
    }
    brand_columns = detected["brand"]
    if brand_columns:
        series = frame[brand_columns[0]].fillna("<missing>").astype(str)
        counts = series.value_counts().head(50)
        report["candidate_brands"] = [
            {"value": str(value), "rows": int(count)}
            for value, count in counts.items()
        ]
    elif detected["author_id"] and detected["inbound"]:
        # TWCS commonly identifies brands indirectly: outbound authors are support accounts.
        inbound = frame[detected["inbound"][0]].astype(str).str.lower()
        outbound = frame[inbound.isin({"false", "0", "no"})]
        authors = detected["author_id"][0]
        counts = outbound[authors].fillna("<missing>").astype(str).value_counts().head(50)
        report["candidate_brands"] = [
            {"value": str(value), "outbound_rows": int(count), "basis": "outbound_author_id"}
            for value, count in counts.items()
        ]
        report["brand_selection_note"] = "These are candidate support-account IDs; map IDs to brand names only when the source provides that mapping."
    else:
        report["warning"] = "No direct brand column or inbound/outbound author pattern was detected; inspect the schema manually."
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw")
    parser.add_argument("--output", default="reports/brand_census.json")
    parser.add_argument("--sample-rows", type=int, default=None)
    args = parser.parse_args()
    report = build_report(args.input, args.sample_rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()