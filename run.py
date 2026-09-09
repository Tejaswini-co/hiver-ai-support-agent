"""Minimal smoke runner using an explicitly supplied JSONL build file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.agent import run_agent
from src.intent_classifier import IntentClassifier
from src.retriever import HistoricalCase, TfidfRetriever


def load_cases(path: Path) -> list[dict[str, str]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-jsonl", required=True, help="JSONL with id, customer_text, agent_text, intent")
    parser.add_argument("--message", required=True)
    args = parser.parse_args()
    rows = load_cases(Path(args.build_jsonl))
    classifier = IntentClassifier().fit([row["customer_text"] for row in rows], [row["intent"] for row in rows])
    retriever = TfidfRetriever().fit([HistoricalCase(**row) for row in rows])
    print(json.dumps(run_agent(args.message, classifier, retriever), indent=2))


if __name__ == "__main__":
    main()