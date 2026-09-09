"""Compare real human and judge ratings; empty/template files are rejected."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score


def compare(path: str) -> dict[str, float | int]:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"example_id", "human_score", "judge_score"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    scored = frame[(frame["human_score"] != "") & (frame["judge_score"] != "")].copy()
    if scored.empty:
        raise ValueError("Real human and judge ratings are required before agreement can be calculated.")
    if not scored["human_score"].isin({"1", "2", "3", "4", "5"}).all() or not scored["judge_score"].isin({"1", "2", "3", "4", "5"}).all():
        raise ValueError("Ratings must be integers from 1 to 5")
    human = scored["human_score"].astype(int)
    judge = scored["judge_score"].astype(int)
    return {
        "examples": len(scored),
        "total_rating_rows": len(frame),
        "excluded_missing_judge_scores": int(len(frame) - len(scored)),
        "exact_agreement": float((human == judge).mean()),
        "cohen_kappa": float(cohen_kappa_score(human, judge)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", required=True)
    args = parser.parse_args()
    print(compare(args.ratings))


if __name__ == "__main__":
    main()
