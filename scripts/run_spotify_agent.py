"""Run the local SpotifyCares classifier + historical-evidence agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.agent import run_agent
from src.intent_classifier import IntentClassifier
from src.retriever import HistoricalCase, TfidfRetriever


def load_cases(path: Path) -> list[HistoricalCase]:
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        cases.append(
            HistoricalCase(
                case_id=row["case_id"],
                customer_text=row["customer_text"],
                agent_text=row["agent_text"],
                conversation_id=str(row["conversation_id"]),
            )
        )
    return cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True)
    parser.add_argument("--labels", default="data/golden/spotifycares_intent_golden.csv")
    parser.add_argument("--cases", default="data/processed/spotifycares_cases.jsonl")
    parser.add_argument("--exclude-case-id", action="append", default=[])
    args = parser.parse_args()
    labels = pd.read_csv(args.labels, dtype=str, keep_default_na=False)
    classifier = IntentClassifier().fit(labels["customer_text"].tolist(), labels["intent"].tolist())
    retriever = TfidfRetriever().fit(load_cases(Path(args.cases)))
    result = run_agent(args.message, classifier, retriever, exclude_case_ids=set(args.exclude_case_id))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()