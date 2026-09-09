from pathlib import Path

from scripts.complete_missing_judges import valid_cached_results


def test_valid_cached_results_ignores_failed_rows(tmp_path: Path) -> None:
    path = tmp_path / "judge.jsonl"
    path.write_text('{"message_id":"1","error":"JSONDecodeError"}\n{"message_id":"2","judge":{"correctness":{"score":1}}}\n', encoding="utf-8")
    assert list(valid_cached_results([path])) == []
