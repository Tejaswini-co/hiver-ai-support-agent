"""The simple TF-IDF + logistic-regression baseline used by the agent."""

from src.intent_classifier import IntentClassifier


def train(texts: list[str], labels: list[str]) -> IntentClassifier:
    return IntentClassifier().fit(texts, labels)