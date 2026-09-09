"""A small, inspectable TF-IDF classifier for the first reproducible baseline."""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


@dataclass
class IntentPrediction:
    label: str
    confidence: float


class IntentClassifier:
    def __init__(self, random_state: int = 42) -> None:
        self.model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
                ("classifier", LogisticRegression(max_iter=1000, random_state=random_state)),
            ]
        )

    def fit(self, texts: list[str], labels: list[str]) -> "IntentClassifier":
        if len(texts) != len(labels) or not texts:
            raise ValueError("texts and labels must be non-empty and have equal length")
        if len(set(labels)) < 2:
            raise ValueError("at least two intent labels are required")
        self.model.fit(texts, labels)
        return self

    def predict(self, text: str) -> IntentPrediction:
        probabilities = self.model.predict_proba([text])[0]
        index = int(probabilities.argmax())
        return IntentPrediction(
            label=str(self.model.classes_[index]),
            confidence=float(probabilities[index]),
        )