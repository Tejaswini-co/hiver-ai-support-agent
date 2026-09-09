"""Column detection and conservative text normalization."""

from __future__ import annotations

import re
from collections.abc import Mapping

import pandas as pd


ALIASES: Mapping[str, tuple[str, ...]] = {
    "text": ("text", "tweet", "body", "content", "message"),
    "brand": ("brand", "company", "account"),
    "conversation_id": ("conversation_id", "thread_id", "in_reply_to_status_id"),
    "author_id": ("author_id", "user_id", "user", "name"),
    "timestamp": ("created_at", "timestamp", "date", "time"),
    "id": ("tweet_id", "status_id", "id"),
    "inbound": ("inbound", "is_inbound"),
    "response_id": ("response_tweet_id", "in_response_to_tweet_id"),
}


def detect_columns(columns: list[str]) -> dict[str, list[str]]:
    lowered = {column.lower(): column for column in columns}
    return {
        role: [lowered[name] for name in aliases if name in lowered]
        for role, aliases in ALIASES.items()
    }


def normalize_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = re.sub(r"https?://\S+", " URL ", text)
    text = re.sub(r"@\w+", " USER ", text)
    return re.sub(r"\s+", " ", text).strip()