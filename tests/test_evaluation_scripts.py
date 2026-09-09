import pytest

from scripts.evaluate_escalation import main


def test_escalation_cli_requires_real_labels(monkeypatch, tmp_path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("example_id,expected_decision,predicted_decision\n1,,ESCALATE\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["evaluate_escalation", "--labels", str(path)])
    with pytest.raises(ValueError, match="Independent"):
        main()