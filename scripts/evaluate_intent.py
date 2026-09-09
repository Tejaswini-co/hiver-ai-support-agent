"""Evaluate the intent classifier using a conversation-grouped labelled CSV."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from baselines.tfidf_baseline import train
from src.intent_data import group_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True, help="CSV containing manually reviewed labels")
    parser.add_argument("--output", default="reports/intent_results.json")
    args = parser.parse_args()
    import pandas as pd

    labelled = pd.read_csv(args.labels)
    training, testing = group_split(labelled)
    model = train(training["customer_text"].tolist(), training["intent"].tolist())
    actual = testing["intent"].tolist()
    predicted = [model.predict(text).label for text in testing["customer_text"]]
    result = {
        "count": len(testing),
        "training_conversations": int(training["conversation_id"].nunique()),
        "held_out_conversations": int(testing["conversation_id"].nunique()),
        "accuracy": accuracy_score(actual, predicted),
        "macro_f1": f1_score(actual, predicted, average="macro", zero_division=0),
        "per_class": classification_report(actual, predicted, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(actual, predicted).tolist(),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()