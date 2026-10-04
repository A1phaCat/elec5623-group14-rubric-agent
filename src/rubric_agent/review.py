"""Marker review session (FR7, FR12, FR13, FR15, NFR5).

The AI suggestion is never overwritten: the exported record keeps the AI value
and the marker value side by side, plus the decision state and timestamp.
Export is refused while any criterion is still `pending`.
"""

from __future__ import annotations

import csv
import io
import json
import math
from datetime import datetime

from .errors import ExportBlocked
from .schemas import Criterion, EvidenceUnit, MarkerDecision, ValidatedAssessment, utc_now


def _seconds_between(start_iso: str, end_iso: str) -> float:
    start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    return max((end - start).total_seconds(), 0.0)

EXPORT_FIELDS = [
    "criterion_id", "criterion_name", "max_mark",
    "evidence_ids", "evidence_locations", "sufficiency",
    "ai_suggested_score", "ai_explanation", "draft_feedback", "warnings",
    "marker_final_score", "marker_comment", "marker_state", "decided_at",
    "model_id", "prompt_version",
]


class ReviewSession:
    def __init__(
        self,
        assessments: list[ValidatedAssessment],
        *,
        criteria: list[Criterion] | None = None,
        retrieved: dict[str, list[EvidenceUnit]] | None = None,
        model_id: str = "",
        prompt_version: str = "",
    ) -> None:
        ids = [item.draft.criterion_id for item in assessments]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("review needs a non-empty set of unique criterion assessments")
        if criteria is not None:
            criterion_ids = [c.id for c in criteria]
            if len(criterion_ids) != len(set(criterion_ids)) or set(criterion_ids) != set(ids):
                raise ValueError("review assessments must match every rubric criterion exactly once")
        # Keep the reviewed suggestion stable if the caller later updates its result.
        self.assessments = {item.draft.criterion_id: item.model_copy(deep=True) for item in assessments}
        self.criteria = {c.id: c.model_copy(deep=True) for c in (criteria or [])}
        self.retrieved = {cid: [u.model_copy(deep=True) for u in units] for cid, units in (retrieved or {}).items()}
        self.model_id = model_id
        self.prompt_version = prompt_version
        self.decisions = {cid: MarkerDecision(criterion_id=cid) for cid in self.assessments}
        self.started_at = utc_now()
        self.interventions = 0  # every decide()/reset() call; M10/M11 raw material

    # -- session summary (M10 review time, M11 override rate) --------------------------

    def summary(self) -> dict:
        states = [d.state for d in self.decisions.values()]
        got, cap = self.total()
        return {
            "started_at": self.started_at,
            "exported_at": utc_now(),
            "duration_s": round(_seconds_between(self.started_at, utc_now()), 1),
            "criteria": len(self.decisions),
            "accepted": states.count("accepted"),
            "edited": states.count("edited"),
            "rejected": states.count("rejected"),
            "pending": states.count("pending"),
            "override_rate": round((states.count("edited") + states.count("rejected")) / max(len(states), 1), 3),
            "interventions": self.interventions,
            "marker_total": got,
            "marker_max": cap,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
        }

    # -- decisions ------------------------------------------------------------------

    def _validate_score(self, criterion_id: str, score: float | None) -> None:
        crit = self.criteria.get(criterion_id)
        maximum = crit.max_mark if crit else self.assessments[criterion_id].draft.score_max
        if score is None or not math.isfinite(score) or not math.isfinite(maximum) or not (0 <= score <= maximum):
            raise ValueError(f"score must be finite and inside 0..{maximum:g}")
        if crit and abs(round(score / crit.granularity) * crit.granularity - score) > 1e-6:
            raise ValueError(f"score must follow the rubric step of {crit.granularity:g}")

    def _check_acceptance(self, criterion_id: str) -> None:
        item = self.assessments[criterion_id]
        if not item.accepted or item.draft.sufficiency == "insufficient" or item.draft.provisional_score is None:
            raise ValueError("AI suggestion has no validated score; choose edited with your own score or rejected")
        self._validate_score(criterion_id, item.draft.provisional_score)

    def decide(self, criterion_id: str, state: str, *, score: float | None = None, comment: str = "") -> MarkerDecision:
        if criterion_id not in self.decisions:
            raise KeyError(criterion_id)
        if state not in {"accepted", "edited", "rejected"}:
            raise ValueError(state)
        draft = self.assessments[criterion_id].draft
        if state == "accepted":
            self._check_acceptance(criterion_id)
            marker_score = draft.provisional_score
        elif state == "edited":
            if score is None:
                raise ValueError("edited decisions need a score")
            self._validate_score(criterion_id, score)
            marker_score = score
        else:
            marker_score = None
        decision = MarkerDecision(
            criterion_id=criterion_id, state=state,  # type: ignore[arg-type]
            marker_score=marker_score, marker_comment=comment, decided_at=utc_now(),
        )
        previous = self.decisions[criterion_id]
        if previous == decision.model_copy(update={"decided_at": previous.decided_at}):
            return previous
        self.interventions += 1
        self.decisions[criterion_id] = decision
        return decision

    def reset(self, criterion_id: str) -> None:
        if self.decisions[criterion_id].state != "pending":
            self.interventions += 1
        self.decisions[criterion_id] = MarkerDecision(criterion_id=criterion_id)

    def unconfirmed(self) -> list[str]:
        return [cid for cid, item in self.decisions.items() if item.state == "pending"]

    # -- export (FR15, M16) -----------------------------------------------------------

    def export_record(self) -> list[dict]:
        if set(self.decisions) != set(self.assessments):
            raise ExportBlocked("review decisions do not cover every criterion")
        missing = self.unconfirmed()
        if missing:
            raise ExportBlocked(f"unconfirmed criteria: {', '.join(missing)}")
        rows = []
        for cid, validated in self.assessments.items():
            draft = validated.draft
            decision = self.decisions[cid]
            # Recheck persisted/public decision objects at the final export boundary.
            try:
                if decision.criterion_id != cid or not decision.decided_at:
                    raise ValueError("decision is missing its criterion or confirmation time")
                if decision.state == "accepted":
                    self._check_acceptance(cid)
                    if decision.marker_score != draft.provisional_score:
                        raise ValueError("accepted score differs from the AI suggestion")
                elif decision.state == "edited":
                    self._validate_score(cid, decision.marker_score)
                elif decision.state != "rejected" or decision.marker_score is not None:
                    raise ValueError("invalid review decision")
            except ValueError as exc:
                raise ExportBlocked(f"invalid decision for {cid}: {exc}") from exc
            crit = self.criteria.get(cid)
            units = {u.id: u for u in self.retrieved.get(cid, [])}
            rows.append({
                "criterion_id": cid,
                "criterion_name": crit.name if crit else "",
                "max_mark": crit.max_mark if crit else draft.score_max,
                "evidence_ids": list(draft.evidence_ids),
                "evidence_locations": [units[e].locator for e in draft.evidence_ids if e in units],
                "sufficiency": draft.sufficiency,
                "ai_suggested_score": draft.provisional_score,
                "ai_explanation": draft.explanation,
                "draft_feedback": draft.draft_feedback,
                "warnings": list(validated.warnings),
                "marker_final_score": decision.marker_score,
                "marker_comment": decision.marker_comment,
                "marker_state": decision.state,
                "decided_at": decision.decided_at,
                "model_id": self.model_id,
                "prompt_version": self.prompt_version,
            })
        return rows

    def export_json(self) -> str:
        rows = self.export_record()  # raises ExportBlocked first
        return json.dumps({"exported_at": utc_now(), "session": self.summary(), "criteria": rows}, indent=2)

    def export_csv(self) -> str:
        rows = self.export_record()
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=EXPORT_FIELDS)
        writer.writeheader()
        for row in rows:
            flat = dict(row)
            for key in ("evidence_ids", "evidence_locations", "warnings"):
                flat[key] = "; ".join(flat[key])
            writer.writerow(flat)
        return buf.getvalue()

    def total(self) -> tuple[float, float]:
        """(marker total, maximum) over confirmed, non-rejected criteria."""
        got = sum(d.marker_score or 0.0 for d in self.decisions.values() if d.marker_score is not None)
        cap = sum(c.max_mark for c in self.criteria.values()) if self.criteria else sum(a.draft.score_max for a in self.assessments.values())
        return got, cap
