"""Evidence-constrained draft generation that never claims an action was performed."""

from __future__ import annotations

from .retriever import HistoricalCase


def draft_reply(message: str, cases: list[tuple[HistoricalCase, float]], *, escalated: bool) -> str:
    if not cases:
        return "Thanks for contacting us. We need a support specialist to review this request."
    example = cases[0][0]
    if escalated:
        return "Thanks for contacting us. We have not made any account changes here; a support specialist should review your request."
    if example.agent_text.strip():
        return f"Thanks for reaching out. Based on similar support cases: {example.agent_text.strip()}"
    return "Thanks for reaching out. We found a similar historical case, but need more information before suggesting a next step."