import json

import pandas as pd

from scripts.run_spotify_agent import load_cases


def test_load_cases_maps_retrieval_schema(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        json.dumps({"case_id": "c1", "customer_text": "app fails", "agent_text": "restart", "conversation_id": 1}) + "\n",
        encoding="utf-8",
    )
    cases = load_cases(path)
    assert cases[0].case_id == "c1"
    assert cases[0].agent_text == "restart"