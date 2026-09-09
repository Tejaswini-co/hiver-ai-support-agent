"""Create a blank human-rating form from actual judge/output IDs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = ["example_id", "human_score", "judge_score", "annotator_id", "annotated_at", "notes"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge-results", default="reports/llm_judge_results.jsonl")
    parser.add_argument("--output", default="reports/human_ratings.csv")
    args = parser.parse_args()
    ids = []
    judge_scores: dict[str, int] = {}
    for line in Path(args.judge_results).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if "judge" in row:
            ids.append(str(row["message_id"]))
            scores = [value["score"] for value in row["judge"].values()]
            judge_scores[str(row["message_id"])] = round(sum(scores) / len(scores))
        elif "message_id" in row:
            ids.append(str(row["message_id"]))
    with Path(args.output).open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=FIELDS)
        writer.writeheader()
        for example_id in ids:
            writer.writerow({"example_id": example_id, "human_score": "", "judge_score": judge_scores.get(example_id, ""), "annotator_id": "", "annotated_at": "", "notes": ""})
    print(json.dumps({"examples": len(ids), "output": args.output, "status": "PENDING_HUMAN_RATINGS"}, indent=2))


if __name__ == "__main__":
    main()