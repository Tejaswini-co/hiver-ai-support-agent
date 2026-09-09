"""Compute evidence-backed support-account statistics from the TWCS export."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


def numeric_like(value: object) -> bool:
    return bool(re.fullmatch(r"\d+", str(value)))


def candidate_stats(frame: pd.DataFrame, handle: str) -> dict[str, object]:
    outbound = frame[(~frame["inbound"]) & (frame["author_id"] == handle)]
    support_ids = set(outbound["tweet_id"].astype(str))
    inbound = frame[frame["inbound"]]
    linked_inbound = inbound[inbound["in_response_to_tweet_id"].isin(support_ids)]
    inbound_ids = set(linked_inbound["tweet_id"].astype(str))
    replies_to_customers = outbound[outbound["in_response_to_tweet_id"].isin(inbound_ids)]
    support_with_children = outbound[outbound["tweet_id"].astype(str).isin(set(inbound["in_response_to_tweet_id"].dropna().astype(str)))]
    customer_authors = linked_inbound[linked_inbound["author_id"].map(numeric_like)]["author_id"].nunique()
    # A linked customer message with a direct company reply is a conservative
    # observable multi-turn unit in this export.
    replied_customer_ids = set(replies_to_customers["in_response_to_tweet_id"].astype(str))
    multi_turn_anchors = inbound_ids & replied_customer_ids
    text = linked_inbound["text"].fillna("").astype(str)
    vectorizer = TfidfVectorizer(stop_words="english", min_df=5, max_features=3000)
    vocabulary_size = 0
    top_terms: list[str] = []
    if len(text) >= 10:
        matrix = vectorizer.fit_transform(text)
        vocabulary_size = len(vectorizer.vocabulary_)
        means = matrix.mean(axis=0).A1
        top_terms = [term for term, _ in sorted(zip(vectorizer.get_feature_names_out(), means), key=lambda item: item[1], reverse=True)[:20]]
    return {
        "support_account": handle,
        "outbound_company_responses": int(len(outbound)),
        "linked_inbound_customer_messages": int(len(linked_inbound)),
        "linked_customer_accounts": int(customer_authors),
        "support_tweets_with_customer_children": int(len(support_with_children)),
        "company_replies_to_linked_customers": int(len(replies_to_customers)),
        "customer_to_company_response_rate": round(len(replies_to_customers) / len(linked_inbound), 4) if len(linked_inbound) else 0.0,
        "customer_messages_with_direct_company_reply": int(len(multi_turn_anchors)),
        "linked_inbound_share_of_all_customer_messages": round(len(linked_inbound) / int(frame["inbound"].sum()), 6),
        "inbound_text_vocabulary_size": vocabulary_size,
        "top_inbound_terms": top_terms,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/twcs.csv")
    parser.add_argument("--output", default="reports/brand_analysis.json")
    args = parser.parse_args()
    frame = pd.read_csv(args.input, low_memory=False)
    frame["in_response_to_tweet_id"] = frame["in_response_to_tweet_id"].astype("Int64").astype(str).replace("<NA>", "")
    frame["tweet_id"] = frame["tweet_id"].astype(str)
    frame["author_id"] = frame["author_id"].astype(str)
    handles = (
        frame.loc[~frame["inbound"], "author_id"]
        .value_counts()
        .head(50)
        .index.tolist()
    )
    stats = [candidate_stats(frame, handle) for handle in handles]
    result = {
        "rows": int(len(frame)),
        "customer_messages": int(frame["inbound"].sum()),
        "company_messages": int((~frame["inbound"]).sum()),
        "unique_authors": int(frame["author_id"].nunique()),
        "reply_links": int((frame["in_response_to_tweet_id"] != "").sum()),
        "candidates": stats,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()