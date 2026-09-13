"""Evidence retrieval (FR6).

BM25 is the proposal's stated baseline (§6.4). The query for a criterion is built
from the criterion name (weighted) and the descriptor text of the *upper* levels,
because those describe what a well-addressed criterion looks like. Lower-level
descriptors ("missing", "absent") would otherwise pull in negative filler.
"""

from __future__ import annotations

import math
from collections import Counter

from .schemas import Criterion, EvidenceUnit
from .textutil import stemmed_tokens as content_tokens


class BM25Retriever:
    method = "bm25"

    def __init__(self, units: list[EvidenceUnit], *, k1: float = 1.5, b: float = 0.75) -> None:
        self.units = units
        self.k1 = k1
        self.b = b
        self._docs = [content_tokens(u.text) for u in units]
        self._avgdl = sum(len(d) for d in self._docs) / max(len(self._docs), 1)
        df: Counter[str] = Counter()
        for doc in self._docs:
            df.update(set(doc))
        n = max(len(self._docs), 1)
        self._idf = {term: math.log(1 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}

    def query_for(self, criterion: Criterion) -> str:
        parts = [criterion.name, criterion.name]  # name counts double
        upper = [d for d in criterion.descriptors if d.score > 0]
        upper.sort(key=lambda d: d.score, reverse=True)
        parts.extend(d.text for d in upper[:2])
        return " ".join(parts)

    def retrieve(self, criterion: Criterion, *, k: int = 5) -> list[EvidenceUnit]:
        return [u for u, _ in self.retrieve_scored(criterion, k=k)]

    def retrieve_scored(self, criterion: Criterion, *, k: int = 5) -> list[tuple[EvidenceUnit, float]]:
        query = content_tokens(self.query_for(criterion))
        if not self.units:
            return []
        scored = [(unit, self._score(query, i)) for i, unit in enumerate(self.units)]
        scored.sort(key=lambda item: (-item[1], item[0].id))
        return [(u, s) for u, s in scored if s > 0][:k]

    def _score(self, query: list[str], index: int) -> float:
        doc = self._docs[index]
        if not doc:
            return 0.0
        tf = Counter(doc)
        score = 0.0
        length = len(doc)
        for term in query:
            if term not in tf:
                continue
            idf = self._idf.get(term, 0.0)
            freq = tf[term]
            denom = freq + self.k1 * (1 - self.b + self.b * length / max(self._avgdl, 1e-9))
            score += idf * freq * (self.k1 + 1) / denom
        return score
