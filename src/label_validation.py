"""Validation for manually labelled intent data; never changes submitted labels."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class LabelValidation:
    row_count: int
    empty_rows: list[int]
    invalid_labels: dict[str, int]
    duplicate_message_ids: int
    duplicate_texts: int
    suspicious_rows: list[dict[str, object]]

    @property
    def valid(self) -> bool:
        return not (
            self.empty_rows
            or self.invalid_labels
            or self.duplicate_message_ids
            or self.duplicate_texts
        )


INTENT_TERMS = {
    "playback_audio_issue": {"song", "music", "shuffle", "repeat", "sound", "playback", "pause"},
    "app_technical_issue": {"app", "crash", "error", "bug", "work", "working", "update"},
    "account_access": {"login", "log in", "password", "account", "email", "access"},
    "subscription_plan_billing": {"premium", "subscription", "payment", "charge", "refund", "billing"},
    "playlist_library_downloads": {"playlist", "album", "library", "download", "offline"},
    "device_platform_compatibility": {"iphone", "ios", "android", "windows", "mac", "browser", "device"},
    "feature_or_policy_information": {"feature", "possible", "available", "how do", "can i", "suggestion"},
}


def validate_labels(frame: pd.DataFrame, approved: set[str]) -> LabelValidation:
    required = {"message_id", "conversation_id", "customer_text", "intent"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required label columns: {sorted(missing)}")
    intents = frame["intent"].fillna("").astype(str).str.strip()
    texts = frame["customer_text"].fillna("").astype(str).str.strip()
    invalid = intents[(intents != "") & ~intents.isin(approved)].value_counts().to_dict()
    suspicious: list[dict[str, object]] = []
    for index, (text, intent) in enumerate(zip(texts, intents)):
        lowered = text.lower()
        matched = [label for label, terms in INTENT_TERMS.items() if any(term in lowered for term in terms)]
        if intent and intent != "other_unclear" and len(matched) >= 3:
            suspicious.append({"row": index + 2, "intent": intent, "signals": matched, "text": text})
    return LabelValidation(
        row_count=len(frame),
        empty_rows=[index + 2 for index, value in enumerate(intents) if not value],
        invalid_labels={str(key): int(value) for key, value in invalid.items()},
        duplicate_message_ids=int(frame["message_id"].duplicated(keep=False).sum()),
        duplicate_texts=int(texts.duplicated(keep=False).sum()),
        suspicious_rows=suspicious,
    )