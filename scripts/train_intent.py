"""Train the explainable intent classifier from manually labelled CSV data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from src.intent_classifier import IntentClassifier
from src.intent_data import group_split
from src.label_validation import validate_labels


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True, help="CSV containing customer_text, intent, conversation_id")
    parser.add_argument("--output", default="reports/intent_training_summary.json")
    args = parser.parse_args()
    labelled = pd.read_csv(args.labels, dtype=str, keep_default_na=False)
    config = yaml.safe_load(Path("config/brand.yaml").read_text(encoding="utf-8"))
    validation = validate_labels(labelled, set(config["intents"]))
    if not validation.valid:
        raise ValueError(
            "Label validation failed; labels were not changed. "
            f"empty={len(validation.empty_rows)}, invalid={validation.invalid_labels}, "
            f"duplicate_ids={validation.duplicate_message_ids}, duplicate_texts={validation.duplicate_texts}"
        )
    train, test = group_split(labelled)
    classifier = IntentClassifier().fit(train["customer_text"].tolist(), train["intent"].tolist())
    actual = test["intent"].tolist()
    predicted = [classifier.predict(text).label for text in test["customer_text"]]
    labels = sorted(labelled["intent"].unique())
    summary = {
        "training_examples": len(train),
        "held_out_examples": len(test),
        "training_conversations": train["conversation_id"].nunique(),
        "held_out_conversations": test["conversation_id"].nunique(),
        "intents": sorted(train["intent"].unique().tolist()),
        "classifier": "word and bigram TF-IDF + Logistic Regression",
        "accuracy": accuracy_score(actual, predicted),
        "macro_f1": f1_score(actual, predicted, labels=labels, average="macro", zero_division=0),
        "per_intent": classification_report(actual, predicted, labels=labels, output_dict=True, zero_division=0),
        "confusion_matrix_labels": labels,
        "confusion_matrix": confusion_matrix(actual, predicted, labels=labels).tolist(),
        "suspicious_rows": validation.suspicious_rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()