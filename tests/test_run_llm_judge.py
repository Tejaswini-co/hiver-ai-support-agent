from scripts.run_llm_judge import load_env


def test_load_env_reads_key_names_without_printing(tmp_path, monkeypatch) -> None:
    path = tmp_path / ".env"
    path.write_text("LLM_MODEL=test\nLLM_API_KEY=secret\n", encoding="utf-8")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    load_env(path)
    assert __import__("os").environ["LLM_MODEL"] == "test"