"""End-to-end agent path: parse → chunk → retrieve → assess → validate → log.

The model gateway is injected; the default is the offline fixture. The pipeline
never passes gold labels or the full submission to the gateway.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from . import PROMPT_VERSION
from .chunker import chunk_pages
from .gateway import FixtureGateway, ModelGateway
from .retriever import BM25Retriever
from .review import ReviewSession
from .rubric_parser import parse_rubric
from .schemas import AssessmentDraft, EvidenceUnit, Rubric, RunLogEntry, ValidatedAssessment
from .store import RunLogger
from .text_parser import ParsedPage, parse_submission
from .validator import validate_assessment

__all__ = ["PipelineResult", "run_pipeline", "run_direct_baseline", "ValidatedAssessment"]


@dataclass
class PipelineResult:
    rubric: Rubric
    pages: list[ParsedPage]
    assessments: list[ValidatedAssessment]
    units: list[EvidenceUnit]
    retrieved: dict[str, list[EvidenceUnit]]
    logs: list[RunLogEntry] = field(default_factory=list)
    latency_ms: float = 0.0
    model_id: str = ""

    def review_session(self) -> ReviewSession:
        return ReviewSession(
            self.assessments,
            criteria=self.rubric.criteria,
            retrieved=self.retrieved,
            model_id=self.model_id,
            prompt_version=PROMPT_VERSION,
        )

    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)


def run_pipeline(
    rubric_source: str | Path,
    submission_source: str | Path,
    *,
    gateway: ModelGateway | None = None,
    k: int = 5,
    test_case_id: str = "adhoc",
    logger: RunLogger | None = None,
    rubric_id: str | None = None,
    revise: bool = True,
    workers: int | None = None,
    evidence_mode: Literal["bm25", "full_context"] = "bm25",
) -> PipelineResult:
    if evidence_mode not in {"bm25", "full_context"}:
        raise ValueError(f"Unknown evidence mode: {evidence_mode}")
    if k < 1:
        raise ValueError("k must be positive")
    started = time.perf_counter()
    gateway = gateway or FixtureGateway()
    rubric = parse_rubric(rubric_source, rubric_id=rubric_id)
    pages = parse_submission(submission_source)
    units = chunk_pages(pages)
    retriever = BM25Retriever(units)
    rubric_ref = str(rubric_source) if isinstance(rubric_source, Path) or "\n" not in str(rubric_source) else ""
    sub_ref = str(submission_source) if isinstance(submission_source, Path) or "\n" not in str(submission_source) else ""

    def assess_one(criterion):
        t0 = time.perf_counter()
        # B3 ablation: change only context selection. Keep identical prompts,
        # citation IDs, per-criterion calls, revision budget and validator.
        hits = list(units) if evidence_mode == "full_context" else retriever.retrieve(criterion, k=k)
        draft = gateway.assess(criterion, hits)
        validated = validate_assessment(draft.model_copy(deep=True), criterion, hits)
        attempts = 1
        first_warnings: list[str] = []
        if not validated.accepted and revise:
            # One corrective round: the validator's findings go back to the model (Lab 6:
            # keep the error in the observation). The revision is validated like any other output.
            first_warnings = list(validated.warnings)
            revised = gateway.revise(criterion, hits, draft, first_warnings)
            if revised is not None:
                attempts = 2
                second = validate_assessment(revised, criterion, hits)
                second.draft.flags = list(dict.fromkeys([*second.draft.flags, "revised_once"]))
                validated = second
        entry = RunLogEntry(
            test_case_id=test_case_id,
            criterion_id=criterion.id,
            model_id=gateway.name,
            prompt_version=PROMPT_VERSION,
            retrieval_k=len(units) if evidence_mode == "full_context" else k,
            retrieval_method="full-context-v1" if evidence_mode == "full_context" else retriever.method,
            query=retriever.query_for(criterion),
            evidence_ids=[u.id for u in hits],
            latency_ms=(time.perf_counter() - t0) * 1000,
            rubric_ref=rubric_ref,
            submission_ref=sub_ref,
            sufficiency=validated.draft.sufficiency,
            provisional_score=validated.draft.provisional_score,
            cited_ids=list(validated.draft.evidence_ids),
            warnings=list(validated.warnings),
            attempts=attempts,
            first_attempt_warnings=first_warnings,
        )
        return hits, validated, entry

    # Criteria do not depend on each other. Overlap the model calls, then
    # restore rubric order so logs and exports stay stable.
    n_workers = len(rubric.criteria) if workers is None else max(1, workers)
    n_workers = min(n_workers, max(len(rubric.criteria), 1))
    if n_workers == 1:
        finished = [assess_one(c) for c in rubric.criteria]
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            finished = list(pool.map(assess_one, rubric.criteria))
    assessments: list[ValidatedAssessment] = []
    retrieved: dict[str, list[EvidenceUnit]] = {}
    logs: list[RunLogEntry] = []
    for criterion, (hits, validated, entry) in zip(rubric.criteria, finished, strict=True):
        retrieved[criterion.id] = hits
        assessments.append(validated)
        logs.append(entry)
        if logger:
            logger.write(entry)
    return PipelineResult(
        rubric=rubric,
        pages=pages,
        assessments=assessments,
        units=units,
        retrieved=retrieved,
        logs=logs,
        latency_ms=(time.perf_counter() - started) * 1000,
        model_id=gateway.name,
    )


def run_direct_baseline(
    rubric_source: str | Path,
    submission_source: str | Path,
    *,
    gateway: ModelGateway | None = None,
    rubric_id: str | None = None,
) -> tuple[Rubric, list[AssessmentDraft]]:
    """Baseline B2: whole rubric + whole document in one call.

    Returns the *raw* drafts. The baseline is measured as it would be used
    (no evidence set, so nothing to validate citations against); the evaluation
    audits its explanations for unsupported claims with the same rule as the agent.
    """
    from .gateway import rejected

    gateway = gateway or FixtureGateway()
    rubric = parse_rubric(rubric_source, rubric_id=rubric_id)
    pages = parse_submission(submission_source)
    drafts = gateway.grade_direct(rubric, "\n\n".join(p.text for p in pages))
    ordered: list[AssessmentDraft] = []
    for c in rubric.criteria:
        d = next((x for x in drafts if x.criterion_id == c.id), None)
        ordered.append(d or rejected(c, "criterion missing", "invalid_model_output"))
    return rubric, ordered
