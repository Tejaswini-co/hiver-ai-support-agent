from src.preprocessing import detect_columns, normalize_text


def test_detect_columns_uses_case_insensitive_aliases() -> None:
    detected = detect_columns(["Tweet", "Company", "created_at", "inbound"])
    assert detected["text"] == ["Tweet"]
    assert detected["brand"] == ["Company"]
    assert detected["timestamp"] == ["created_at"]
    assert detected["inbound"] == ["inbound"]


def test_normalize_text_removes_unstable_tokens() -> None:
    assert normalize_text("Hi @support https://example.test  now") == "Hi USER URL now"