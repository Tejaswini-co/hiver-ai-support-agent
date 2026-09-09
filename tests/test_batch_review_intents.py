from scripts.batch_review_intents import parse_corrections, summary


def test_parse_corrections_validates_taxonomy_and_reason() -> None:
    corrections = parse_corrections("2=account_access|Login is the primary issue", 1, 20)
    assert corrections == {1: ("account_access", "Login is the primary issue")}


def test_summary_distinguishes_unchanged_corrected_and_pending() -> None:
    rows = [
        {"intent": "app_technical_issue", "provisional_intent": "app_technical_issue", "review_status": "HUMAN_REVIEWED"},
        {"intent": "account_access", "provisional_intent": "other_unclear", "review_status": "HUMAN_REVIEWED"},
        {"intent": "", "provisional_intent": "other_unclear", "review_status": "PENDING"},
    ]
    assert summary(rows) == {"total": 3, "approved_unchanged": 1, "corrected": 1, "still_pending": 1}