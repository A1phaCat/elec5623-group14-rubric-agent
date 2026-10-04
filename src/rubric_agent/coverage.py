"""Deterministic checklist of the top rubric band against retrieved evidence.

This does not score the submission. It tells the marker which words from the
full-marks descriptor appear in sentences that are not denials, so a keyword
mention inside "does not include metrics" is not counted as present.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schemas import Criterion, EvidenceUnit
from .textutil import NEGATIVE_MARKERS, sentences, stemmed_tokens


@dataclass(frozen=True)
class TopBandCoverage:
    score: float
    text: str
    present: tuple[str, ...]
    missing: tuple[str, ...]


def top_band_coverage(criterion: Criterion, evidence: list[EvidenceUnit]) -> TopBandCoverage | None:
    upper = [d for d in criterion.descriptors if d.score > 0]
    if not upper:
        return None
    top = max(upper, key=lambda d: d.score)
    name_terms = set(stemmed_tokens(criterion.name))
    required = tuple(dict.fromkeys(t for t in stemmed_tokens(top.text) if t not in name_terms))
    affirmative: list[str] = []
    for unit in evidence:
        for sentence in sentences(unit.text):
            if NEGATIVE_MARKERS.search(sentence):
                continue
            affirmative.append(sentence)
    found = set(stemmed_tokens(" ".join(affirmative)))
    present = tuple(t for t in required if t in found)
    missing = tuple(t for t in required if t not in found)
    return TopBandCoverage(score=top.score, text=top.text, present=present, missing=missing)
