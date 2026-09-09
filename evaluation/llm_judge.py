"""Structured LLM-judge contract; it does not call a provider or fabricate scores."""

from __future__ import annotations

import json
import re


RUBRIC = {
    "correctness": "Does the reply accurately address the customer message without unsupported facts?",
    "relevance": "Does the reply directly address the customer's issue?",
    "groundedness": "Can the reply's claims be supported by the supplied historical evidence?",
    "helpfulness": "Does it provide a useful, safe next step?",
    "completeness": "Does it address the material parts of the request?",
    "appropriate_escalation": "Is auto-handling versus escalation appropriate given confidence and evidence?",
    "unsupported_claim_penalty": "Score 1 when unsupported claims are absent; score 5 when severe unsupported claims are present.",
}

JUDGE_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        key: {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "score": {"type": "integer", "minimum": 1, "maximum": 5},
                "explanation": {"type": "string"},
            },
            "required": ["score", "explanation"],
        }
        for key in RUBRIC
    },
    "required": list(RUBRIC),
}


def build_prompt(customer_message: str, evidence: list[dict[str, object]], response: str, decision: str) -> str:
    return json.dumps(
        {
            "instruction": "Rate each rubric dimension from 1 to 5. Return JSON only. Do not reward fluency over evidence.",
            "rubric": RUBRIC,
            "customer_message": customer_message,
            "retrieved_evidence": evidence,
            "generated_response": response,
            "decision": decision,
            "required_output": {key: {"score": "integer 1-5", "explanation": "short string"} for key in RUBRIC},
        },
        ensure_ascii=False,
        indent=2,
    )


def validate_result(result: dict[str, object]) -> None:
    unexpected = set(result).difference(RUBRIC)
    if unexpected:
        raise ValueError(f"Judge result has unexpected fields: {sorted(unexpected)}")
    missing = set(RUBRIC).difference(result)
    if missing:
        raise ValueError(f"Judge result missing rubric fields: {sorted(missing)}")
    for key in RUBRIC:
        value = result[key]
        if (
            not isinstance(value, dict)
            or set(value) != {"score", "explanation"}
            or isinstance(value.get("score"), bool)
            or not isinstance(value.get("score"), int)
            or not 1 <= value["score"] <= 5
            or not isinstance(value.get("explanation"), str)
            or not value["explanation"].strip()
        ):
            raise ValueError(f"Invalid judge score for {key}; expected integer 1-5")


def parse_judge_content(content: str) -> dict[str, object]:
    """Parse JSON responses with optional markdown fences, without inventing fields."""
    cleaned = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    result = json.loads(cleaned)
    if not isinstance(result, dict):
        raise ValueError("Judge response must be a JSON object")
    validate_result(result)
    return result
