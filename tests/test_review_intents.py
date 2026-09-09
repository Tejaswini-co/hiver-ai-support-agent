from pathlib import Path

from scripts.review_intents import propose_intent, save_rows


def test_proposal_is_a_taxonomy_value() -> None:
    intent, reason = propose_intent("My playlist is missing after I downloaded it")
    assert intent == "playlist_library_downloads"
    assert reason


def test_save_rows_preserves_message_fields(tmp_path: Path) -> None:
    path = tmp_path / "labels.csv"
    fields = ["message_id", "conversation_id", "customer_text", "intent", "label_notes"]
    rows = [{"message_id": "1", "conversation_id": "c1", "customer_text": "A, exact text", "intent": "", "label_notes": ""}]
    save_rows(path, fields, rows)
    assert path.read_text(encoding="utf-8").count("A, exact text") == 1