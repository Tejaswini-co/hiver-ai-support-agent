import pytest

from evaluation.llm_judge import parse_judge_content


def test_parse_judge_content_accepts_json_fence() -> None:
    rubric = {key: {"score": 3, "explanation": "ok"} for key in [
        "correctness", "relevance", "groundedness", "helpfulness", "completeness", "appropriate_escalation", "unsupported_claim_penalty"
    ]}
    assert parse_judge_content("```json\n" + __import__("json").dumps(rubric) + "\n```")["correctness"]["score"] == 3


def test_parse_judge_content_rejects_non_object() -> None:
    with pytest.raises(ValueError):
        parse_judge_content("[]")