"""Complete only missing human-review judge scores with cached-result reuse."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import pandas as pd

from evaluation.llm_judge import JUDGE_JSON_SCHEMA, build_prompt, validate_result
from scripts.run_llm_judge import judge_request, load_env
from scripts.run_spotify_agent import load_cases
from src.agent import run_agent
from src.intent_classifier import IntentClassifier
from src.retriever import TfidfRetriever


def valid_cached_results(paths: list[Path]) -> dict[str, dict[str, object]]:
    cached: dict[str, dict[str, object]] = {}
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if "judge" in row:
                try:
                    validate_result(row["judge"])
                except (TypeError, ValueError):
                    continue
                cached[str(row["message_id"])] = row["judge"]
    return cached


def average_score(judge: dict[str, object]) -> str:
    return str(round(sum(int(value["score"]) for value in judge.values()) / len(judge)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", default="reports/human_ratings.csv")
    parser.add_argument("--outputs", default="reports/human_review_outputs.jsonl")
    parser.add_argument("--result-files", nargs="*", default=["reports/human_judge_results.jsonl", "reports/missing_judge_results.jsonl"])
    parser.add_argument("--output", default="reports/human_judge_results.jsonl")
    parser.add_argument("--model", default="", help="Override LLM_MODEL only when intentionally changing providers")
    parser.add_argument("--retry-per-example", type=int, default=2)
    parser.add_argument("--target-valid", type=int, default=11)
    args = parser.parse_args()
    load_env(Path(".env"))
    api_key = os.environ.get("LLM_API_KEY", "")
    if not api_key:
        raise ValueError(".env must contain LLM_API_KEY")
    model = args.model or os.environ.get("LLM_MODEL", "")
    if not model:
        raise ValueError(".env must contain LLM_MODEL")
    ratings = pd.read_csv(args.ratings, dtype=str, keep_default_na=False)
    outputs = {
        str(json.loads(line)["example_id"]): json.loads(line)
        for line in Path(args.outputs).read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    cached = valid_cached_results([Path(path) for path in args.result_files])
    valid_ids = set(cached)
    missing = [str(example_id) for example_id in ratings["example_id"] if str(example_id) not in valid_ids]
    if len(valid_ids) >= args.target_valid:
        rating_rows = ratings.to_dict("records")
        for row in rating_rows:
            key = str(row["example_id"])
            if key in cached:
                row["judge_score"] = average_score(cached[key])
        with Path(args.ratings).open("w", newline="", encoding="utf-8") as destination:
            writer = csv.DictWriter(destination, fieldnames=list(ratings.columns))
            writer.writeheader()
            writer.writerows(rating_rows)
        print(json.dumps({"valid_before_calls": len(valid_ids), "calls_made": 0, "target_reached": True}, indent=2))
        return

    labels = pd.read_csv("data/golden/spotifycares_intent_golden.csv", dtype=str, keep_default_na=False)
    classifier = IntentClassifier().fit(labels["customer_text"].tolist(), labels["intent"].tolist())
    retriever = TfidfRetriever().fit(load_cases(Path("data/processed/spotifycares_cases.jsonl")))
    new_results: dict[str, dict[str, object]] = {}
    calls = 0
    failures = 0
    for example_id in missing:
        if len(valid_ids) >= args.target_valid:
            break
        row = labels[labels["message_id"].astype(str) == example_id].iloc[0].to_dict()
        agent = run_agent(row["customer_text"], classifier, retriever, exclude_case_ids={f"spotifycares-{example_id}"})
        prompt = build_prompt(row["customer_text"], agent["retrieved_cases"], str(agent["response_draft"]), str(agent["decision"]))
        for _ in range(args.retry_per_example + 1):
            calls += 1
            try:
                judge = judge_request(prompt, model, api_key, json_schema=JUDGE_JSON_SCHEMA)
                new_results[example_id] = judge
                valid_ids.add(example_id)
                break
            except Exception:
                failures += 1

    merged = dict(cached)
    merged.update(new_results)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps({"message_id": key, "judge": value}, ensure_ascii=False) for key, value in sorted(merged.items())) + "\n", encoding="utf-8")

    rating_rows = ratings.to_dict("records")
    for row in rating_rows:
        key = str(row["example_id"])
        if key in merged:
            row["judge_score"] = average_score(merged[key])
    with Path(args.ratings).open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(ratings.columns))
        writer.writeheader()
        writer.writerows(rating_rows)
    print(json.dumps({"valid_before_calls": len(cached), "valid_after_calls": len(merged), "calls_made": calls, "failed_attempts": failures, "missing_after": 13 - len(merged), "model": model}, indent=2))


if __name__ == "__main__":
    main()
