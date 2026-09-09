"""Conservative, explainable escalation policy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EscalationDecision:
    decision: str
    reason: str


def decide(
    *,
    intent_confidence: float,
    evidence_count: int,
    message: str,
    min_intent_confidence: float = 0.65,
    min_evidence: int = 1,
    financial_intents: set[str] | None = None,
    intent: str | None = None,
) -> EscalationDecision:
    lowered = message.lower()
    if intent in (financial_intents or set()):
        return EscalationDecision("ESCALATE", "Financial or account-specific handling requires a human.")
    if any(term in lowered for term in ("password", "hacked", "stolen", "security")):
        return EscalationDecision("ESCALATE", "Security-sensitive requests require a human.")
    if intent_confidence < min_intent_confidence:
        return EscalationDecision("ESCALATE", "Intent confidence is below the configured threshold.")
    if evidence_count < min_evidence:
        return EscalationDecision("ESCALATE", "There is insufficient historical evidence for a grounded reply.")
    return EscalationDecision("AUTO_HANDLE", "Intent confidence and historical evidence meet the configured thresholds.")