"""Majority-label baseline; metrics must be computed on an actual golden set."""

from collections import Counter


def majority_label(labels: list[str]) -> str:
    if not labels:
        raise ValueError("labels must not be empty")
    return Counter(labels).most_common(1)[0][0]