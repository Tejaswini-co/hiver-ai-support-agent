import pandas as pd
import pytest

from src.intent_classifier import IntentClassifier
from src.intent_data import group_split


def test_classifier_requires_more_than_one_label() -> None:
    with pytest.raises(ValueError, match="two intent labels"):
        IntentClassifier().fit(["a", "b"], ["one", "one"])


def test_group_split_keeps_conversations_disjoint() -> None:
    labelled = pd.DataFrame(
        {
            "customer_text": ["refund", "refund follow-up", "login", "login follow-up", "playlist", "playlist follow-up"],
            "intent": ["billing", "billing", "account", "account", "library", "library"],
            "conversation_id": ["a", "a", "b", "b", "c", "c"],
        }
    )
    train, test = group_split(labelled, test_size=1 / 3)
    assert set(train["conversation_id"]).isdisjoint(set(test["conversation_id"]))


def test_classifier_predicts_labels_after_fit() -> None:
    classifier = IntentClassifier().fit(["cannot login", "playlist missing"], ["account", "library"])
    prediction = classifier.predict("login problem")
    assert prediction.label in {"account", "library"}
    assert 0 <= prediction.confidence <= 1