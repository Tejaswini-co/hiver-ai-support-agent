import pandas as pd

from src.label_validation import validate_labels


def test_validation_flags_empty_and_invalid_labels() -> None:
    frame = pd.DataFrame(
        {
            "message_id": ["1", "2"],
            "conversation_id": ["a", "b"],
            "customer_text": ["hello", "hello again"],
            "intent": ["", "not_approved"],
        }
    )
    result = validate_labels(frame, {"other_unclear"})
    assert result.empty_rows == [2]
    assert result.invalid_labels == {"not_approved": 1}
    assert not result.valid


def test_validation_accepts_unique_approved_labels() -> None:
    frame = pd.DataFrame(
        {
            "message_id": ["1", "2"],
            "conversation_id": ["a", "b"],
            "customer_text": ["cannot login", "playlist missing"],
            "intent": ["account_access", "playlist_library_downloads"],
        }
    )
    result = validate_labels(frame, {"account_access", "playlist_library_downloads"})
    assert result.valid