"""Run log (FR16, NFR7) — one JSON line per model call, append-only.

JSONL rather than SQLite so that a log can be read with any text tool and
diffed in a pull request. `replay_entry()` re-executes a call from its log line
alone (M12) and reports whether the cited evidence and score are unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .schemas import RunLogEntry


class RunLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, entry: RunLogEntry) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(entry.model_dump_json() + "\n")

    def read(self) -> list[RunLogEntry]:
        if not self.path.exists():
            return []
        entries = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(RunLogEntry.model_validate(json.loads(line)))
        return entries


@dataclass
class ReplayOutcome:
    test_case_id: str
    criterion_id: str
    same_top1: bool
    same_cited: bool
    score_drift: float | None  # |new - old| / max_mark, None when either score absent
    within_tolerance: bool


def replay_entry(entry: RunLogEntry, *, gateway=None, tolerance: float = 0.10) -> ReplayOutcome:
    """Re-run one logged call with the logged settings and compare (NFR2, M12)."""
    from .gateway import build_gateway
    from .pipeline import run_pipeline

    if not entry.rubric_ref or not entry.submission_ref:
        raise ValueError("log entry lacks rubric_ref/submission_ref; cannot replay")
    gateway = gateway or build_gateway("fixture" if entry.model_id.startswith("fixture") else None)
    result = run_pipeline(
        Path(entry.rubric_ref), Path(entry.submission_ref),
        gateway=gateway, k=entry.retrieval_k, test_case_id=entry.test_case_id,
    )
    new = next(a for a in result.assessments if a.draft.criterion_id == entry.criterion_id)
    new_log = next(l for l in result.logs if l.criterion_id == entry.criterion_id)
    old_top1 = entry.evidence_ids[0] if entry.evidence_ids else None
    new_top1 = new_log.evidence_ids[0] if new_log.evidence_ids else None
    drift = None
    if entry.provisional_score is not None and new.draft.provisional_score is not None:
        drift = abs(new.draft.provisional_score - entry.provisional_score) / max(new.draft.score_max, 1e-9)
    same_score_state = (entry.provisional_score is None) == (new.draft.provisional_score is None)
    return ReplayOutcome(
        test_case_id=entry.test_case_id,
        criterion_id=entry.criterion_id,
        same_top1=old_top1 == new_top1,
        same_cited=list(entry.cited_ids) == list(new.draft.evidence_ids),
        score_drift=drift,
        within_tolerance=same_score_state and (drift is None or drift <= tolerance),
    )
