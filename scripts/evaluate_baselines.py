"""Evaluate required trivial and simple intent baselines on the same grouped split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from baselines.majority_baseline import majority_label
from src.intent_data import group_split
from scripts.review_intents import propose_intent


def metrics(actual: list[str], predicted: list[str]) -> dict[str, object]:
    return {
        "accuracy": accuracy_score(actual, predicted),
        "macro_f1": f1_score(actual, predicted, average="macro", zero_division=0),
        "weighted_f1": f1_score(actual, predicted, average="weighted", zero_division=0),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", default="reports/baseline_results.json")
    args = parser.parse_args()
    labelled = pd.read_csv(args.labels, dtype=str, keep_default_na=False)
    train, test = group_split(labelled)
    actual = test["intent"].tolist()
    majority = majority_label(train["intent"].tolist())
    majority_result = {"method": "majority_class", "label": majority, **metrics(actual, [majority] * len(actual))}
    keyword_predictions = [propose_intent(text)[0] for text in test["customer_text"]]
    keyword_result = {"method": "keyword_rules", **metrics(actual, keyword_predictions)}
    result = {
        "training_examples": len(train),
        "held_out_examples": len(test),
        "split": "GroupShuffleSplit by conversation_id, random_state=42",
        "baselines": [majority_result, keyword_result],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()