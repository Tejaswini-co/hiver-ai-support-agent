from evaluation.human_agreement import compare


def test_agreement_uses_only_rows_with_both_scores(tmp_path) -> None:
    path = tmp_path / "ratings.csv"
    path.write_text(
        "example_id,human_score,judge_score\n1,1,1\n2,2,\n3,3,2\n",
        encoding="utf-8",
    )
    result = compare(str(path))
    assert result["examples"] == 2
    assert result["excluded_missing_judge_scores"] == 1