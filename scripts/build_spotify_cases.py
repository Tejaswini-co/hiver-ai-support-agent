"""Build linked SpotifyCares customer/support cases for historical retrieval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def build_cases(input_path: str, output_path: str) -> int:
    frame = pd.read_csv(input_path, low_memory=False)
    required = {"tweet_id", "author_id", "inbound", "text", "in_response_to_tweet_id"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    frame["tweet_id"] = frame["tweet_id"].astype(str)
    frame["author_id"] = frame["author_id"].astype(str)
    frame["parent_id"] = frame["in_response_to_tweet_id"].astype("Int64").astype(str).replace("<NA>", "")
    support = frame[(~frame["inbound"]) & (frame["author_id"] == "SpotifyCares")]
    support_by_id = support.set_index("tweet_id")
    customer = frame[frame["inbound"] & frame["parent_id"].isin(set(support["tweet_id"]))]
    customer_ids = set(customer["tweet_id"])
    replies = frame[(~frame["inbound"]) & frame["parent_id"].isin(customer_ids)]
    grouped_replies = replies.groupby("parent_id")["text"].apply(lambda values: " ".join(str(value) for value in values)).to_dict()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as destination:
        for row in customer.itertuples(index=False):
            response = grouped_replies.get(row.tweet_id, "")
            if not response.strip():
                continue
            parent_support = support_by_id.loc[row.parent_id]
            case = {
                "case_id": f"spotifycares-{row.tweet_id}",
                "customer_message_id": row.tweet_id,
                "support_message_id": str(row.parent_id),
                "conversation_id": row.parent_id,
                "customer_text": str(row.text),
                "agent_text": response,
                "created_at": str(row.created_at),
                "support_account": str(parent_support["author_id"]),
            }
            destination.write(json.dumps(case, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/twcs.csv")
    parser.add_argument("--output", default="data/processed/spotifycares_cases.jsonl")
    args = parser.parse_args()
    count = build_cases(args.input, args.output)
    print(json.dumps({"cases_written": count, "output": args.output}, indent=2))


if __name__ == "__main__":
    main()