"""Generate leakage-safe agent outputs for later response-quality judging."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.run_spotify_agent import load_cases
from src.agent import run_agent
from src.intent_classifier import IntentClassifier
from src.intent_data import group_split
from src.retriever import TfidfRetriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", default="data/golden/spotifycares_intent_golden.csv")
    parser.add_argument("--cases", default="data/processed/spotifycares_cases.jsonl")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--output", default="reports/response_evaluation_outputs.jsonl")
    parser.add_argument("--ids-file", default="", help="Optional CSV containing example_id/message_id")
    args = parser.parse_args()
    labels = pd.read_csv(args.labels, dtype=str, keep_default_na=False)
    train, test = group_split(labels)
    if args.ids_file:
        ids_frame = pd.read_csv(args.ids_file, dtype=str, keep_default_na=False)
        id_column = "example_id" if "example_id" in ids_frame else "message_id"
        wanted = set(ids_frame[id_column].astype(str))
        selected = labels[labels["message_id"].astype(str).isin(wanted)]
        # This path prepares human-review material, not benchmark metrics.
        # Keep the exact requested IDs even when they are outside the held-out split.
        train = labels
        test = selected
    classifier = IntentClassifier().fit(train["customer_text"].tolist(), train["intent"].tolist())
    cases = load_cases(Path(args.cases))
    retriever = TfidfRetriever().fit(cases)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for row in test.head(args.limit).to_dict("records"):
        case_id = f"spotifycares-{row['message_id']}"
        result = run_agent(row["customer_text"], classifier, retriever, exclude_case_ids={case_id})
        rows.append({
            "example_id": row["message_id"],
            "conversation_id": row["conversation_id"],
            "customer_text": row["customer_text"],
            "expected_intent": row["intent"],
            "agent_output": result,
        })
    output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"outputs": len(rows), "output": str(output), "leakage_exclusion": "target case ID excluded"}, indent=2))


if __name__ == "__main__":
    main()