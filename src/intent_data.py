"""Prepare manually labelled intent examples without crossing conversation splits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


@dataclass(frozen=True)
class IntentExample:
    message_id: str
    conversation_id: str
    customer_text: str
    intent: str


def spotify_customer_messages(path: str | Path, support_account: str = "SpotifyCares") -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)
    required = {"tweet_id", "author_id", "inbound", "text", "in_response_to_tweet_id"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required TWCS columns: {sorted(missing)}")
    frame["tweet_id"] = frame["tweet_id"].astype(str)
    frame["parent_id"] = frame["in_response_to_tweet_id"].astype("Int64").astype(str).replace("<NA>", "")
    frame["author_id"] = frame["author_id"].astype(str)
    support_ids = set(frame.loc[(~frame["inbound"]) & (frame["author_id"] == support_account), "tweet_id"])
    customer = frame[frame["inbound"] & frame["parent_id"].isin(support_ids)].copy()
    customer["conversation_id"] = customer["tweet_id"].map(_conversation_roots(frame))
    return customer[["tweet_id", "conversation_id", "text", "parent_id", "created_at"]].rename(
        columns={"tweet_id": "message_id", "text": "customer_text"}
    )


def _conversation_roots(frame: pd.DataFrame) -> dict[str, str]:
    parents = dict(zip(frame["tweet_id"], frame["parent_id"]))
    roots: dict[str, str] = {}
    for tweet_id in parents:
        path: list[str] = []
        current = tweet_id
        while current and current not in roots and current in parents and current not in path:
            path.append(current)
            current = parents[current]
        root = roots.get(current, current or tweet_id)
        for node in path:
            roots[node] = root
    return roots


def group_split(
    labelled: pd.DataFrame,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"customer_text", "intent", "conversation_id"}
    missing = required.difference(labelled.columns)
    if missing:
        raise ValueError(f"Missing labelled-data columns: {sorted(missing)}")
    if labelled["intent"].isna().any() or labelled["conversation_id"].isna().any():
        raise ValueError("Manual labels and conversation IDs must be present for every row")
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_index, test_index = next(splitter.split(labelled, groups=labelled["conversation_id"]))
    return labelled.iloc[train_index].copy(), labelled.iloc[test_index].copy()