import json

import pandas as pd

from scripts.build_spotify_cases import build_cases


def test_build_cases_links_customer_to_support_reply(tmp_path) -> None:
    source = tmp_path / "twcs.csv"
    output = tmp_path / "cases.jsonl"
    pd.DataFrame(
        [
            {"tweet_id": 1, "author_id": "SpotifyCares", "inbound": False, "text": "Support answer", "in_response_to_tweet_id": 2, "created_at": "now"},
            {"tweet_id": 2, "author_id": "99", "inbound": True, "text": "My app fails", "in_response_to_tweet_id": 1, "created_at": "now"},
            {"tweet_id": 3, "author_id": "SpotifyCares", "inbound": False, "text": "Try restart", "in_response_to_tweet_id": 2, "created_at": "now"},
        ]
    ).to_csv(source, index=False)
    assert build_cases(str(source), str(output)) == 1
    case = json.loads(output.read_text(encoding="utf-8"))
    assert case["customer_text"] == "My app fails"
    assert case["agent_text"] == "Support answer Try restart"