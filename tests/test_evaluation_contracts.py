import pytest

from evaluation.llm_judge import build_prompt, validate_result
from evaluation.human_agreement import compare


def test_judge_prompt_contains_evidence_and_message() -> None:
    prompt = build_prompt("app fails", [{"text": "try restart"}], "Try restart.", "AUTO_HANDLE")
    assert "app fails" in prompt
    assert "try restart" in prompt


def test_judge_validation_rejects_missing_rubric() -> None:
    with pytest.raises(ValueError):
        validate_result({})


def test_human_agreement_rejects_template(tmp_path) -> None:
    path = tmp_path / "ratings.csv"
    path.write_text("example_id,human_score,judge_score\n1,,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Real human"):
        compare(str(path))