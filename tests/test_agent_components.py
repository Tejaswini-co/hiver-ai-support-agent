from src.escalation import decide
from src.retriever import HistoricalCase, TfidfRetriever


def test_retriever_can_exclude_a_case() -> None:
    retriever = TfidfRetriever().fit(
        [
            HistoricalCase("1", "refund status", "please check", "refund"),
            HistoricalCase("2", "delivery delay", "we are checking", "delivery"),
        ]
    )
    results = retriever.search("refund", exclude_ids={"1"})
    assert results[0][0].case_id == "2"


def test_low_confidence_escalates_with_reason() -> None:
    decision = decide(intent_confidence=0.2, evidence_count=2, message="hello")
    assert decision.decision == "ESCALATE"
    assert "confidence" in decision.reason.lower()