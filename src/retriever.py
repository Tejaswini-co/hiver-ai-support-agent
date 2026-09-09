"""TF-IDF historical-case retrieval with explicit exclusion hooks for evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class HistoricalCase:
    case_id: str
    customer_text: str
    agent_text: str
    intent: str | None = None
    conversation_id: str | None = None


class TfidfRetriever:
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.cases: list[HistoricalCase] = []
        self.matrix = None

    def fit(self, cases: list[HistoricalCase]) -> "TfidfRetriever":
        if not cases:
            raise ValueError("At least one historical case is required")
        self.cases = list(cases)
        self.matrix = self.vectorizer.fit_transform([case.customer_text for case in cases])
        return self

    def search(self, query: str, top_k: int = 5, exclude_ids: set[str] | None = None) -> list[tuple[HistoricalCase, float]]:
        if self.matrix is None:
            raise RuntimeError("Retriever must be fitted before search")
        excluded = exclude_ids or set()
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        ranked = sorted(enumerate(scores), key=lambda item: float(item[1]), reverse=True)
        return [
            (self.cases[index], float(score))
            for index, score in ranked
            if self.cases[index].case_id not in excluded
        ][:top_k]