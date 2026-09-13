"""Pydantic data contracts.

`AssessmentDraft` is the JSON contract fixed in proposal Listing 6.1. Everything a
model returns must validate against it before the Validator even looks at it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Sufficiency = Literal["sufficient", "partial", "insufficient"]
DecisionState = Literal["pending", "accepted", "edited", "rejected"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# --- Rubric -----------------------------------------------------------------


class ScoreDescriptor(StrictModel):
    score: float
    text: str


class Criterion(StrictModel):
    id: str
    name: str
    max_mark: float = Field(gt=0)
    granularity: float = Field(gt=0)
    descriptors: list[ScoreDescriptor] = Field(default_factory=list)


class Rubric(StrictModel):
    id: str
    title: str
    criteria: list[Criterion]
    source_format: str = "unknown"


# --- Submission -------------------------------------------------------------


class EvidenceUnit(StrictModel):
    id: str
    text: str
    page: int = Field(ge=1)
    section: str
    paragraph: int = Field(ge=0)
    adjacent_before: str = ""
    adjacent_after: str = ""

    @property
    def locator(self) -> str:
        return f"p.{self.page} · {self.section} · ¶{self.paragraph + 1}"


# --- Assessment (Listing 6.1) ----------------------------------------------


class AssessmentDraft(StrictModel):
    criterion_id: str
    evidence_ids: list[str]
    sufficiency: Sufficiency
    provisional_score: float | None = None
    score_max: float
    explanation: str
    draft_feedback: str | None = None
    flags: list[str] = Field(default_factory=list)


class ValidatedAssessment(StrictModel):
    draft: AssessmentDraft
    accepted: bool
    warnings: list[str] = Field(default_factory=list)
    # Sentence-level grounding audit (FR10 / M6). Filled by the validator.
    claims: int = 0
    unsupported_claims: int = 0


# --- Marker review ----------------------------------------------------------


class MarkerDecision(StrictModel):
    criterion_id: str
    state: DecisionState = "pending"
    marker_score: float | None = None
    marker_comment: str = ""
    decided_at: str | None = None


# --- Logging / reproducibility (FR16, NFR7) ---------------------------------


class RunLogEntry(StrictModel):
    test_case_id: str
    criterion_id: str
    model_id: str
    prompt_version: str
    retrieval_k: int
    retrieval_method: str
    query: str
    evidence_ids: list[str]
    latency_ms: float
    # Inputs needed to replay the call from the log alone (M12).
    rubric_ref: str = ""
    submission_ref: str = ""
    # Outputs recorded for drift comparison.
    sufficiency: str = ""
    provisional_score: float | None = None
    cited_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


# --- Evaluation labels ------------------------------------------------------


class GoldLabel(StrictModel):
    rubric_id: str
    submission_id: str
    criterion_id: str
    must_contain: list[str] = Field(default_factory=list)
    sufficiency: Sufficiency
    score: float | None = None
    scenario: str = "S1"
    split: Literal["dev", "heldout"] = "dev"
