"""Orchestrates classification, retrieval, drafting, and escalation."""

from __future__ import annotations

from .escalation import decide
from .intent_classifier import IntentClassifier
from .response_generator import draft_reply
from .retriever import TfidfRetriever


def run_agent(
    message: str,
    classifier: IntentClassifier,
    retriever: TfidfRetriever,
    *,
    exclude_case_ids: set[str] | None = None,
) -> dict[str, object]:
    prediction = classifier.predict(message)
    evidence = retriever.search(message, top_k=5, exclude_ids=exclude_case_ids)
    escalation = decide(
        intent=prediction.label,
        intent_confidence=prediction.confidence,
        evidence_count=len(evidence),
        message=message,
    )
    response = draft_reply(message, evidence, escalated=escalation.decision == "ESCALATE")
    return {
        "intent": prediction.label,
        "intent_confidence": prediction.confidence,
        "decision": escalation.decision,
        "reason": escalation.reason,
        "draft_reply": response,
        "response_draft": response,
        "retrieved_cases": [
            {
                "id": case.case_id,
                "score": score,
                "customer_text": case.customer_text,
                "support_response": case.agent_text,
                "conversation_id": case.conversation_id,
            }
            for case, score in evidence
        ],
    }