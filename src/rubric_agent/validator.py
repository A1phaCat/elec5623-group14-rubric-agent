"""Validator (FR9–FR11, scenario S6).

Runs after every model call and before anything reaches the marker. It is
deterministic code, not a model, so it can be tested exhaustively. Any critical
warning downgrades the record to `insufficient` with no score (fail-closed).
"""

from __future__ import annotations

from .schemas import AssessmentDraft, Criterion, EvidenceUnit, ValidatedAssessment
from .textutil import citation_ids, positive_claims, unsupported_claims

CRITICAL = {
    "score_out_of_range",
    "unknown_evidence_ids",
    "missing_evidence",
    "unknown_citation_ids",
    "uncited_claim",
    "invalid_model_output",
    "provider_error",
    "score_max_mismatch",
}


def validate_assessment(
    draft: AssessmentDraft,
    criterion: Criterion,
    evidence: list[EvidenceUnit],
) -> ValidatedAssessment:
    allowed = {u.id for u in evidence}
    warnings: list[str] = []

    # Flags raised upstream by the gateway (bad JSON, HTTP failure) are warnings too.
    for flag in draft.flags:
        if flag in {"invalid_model_output", "provider_error"}:
            warnings.append(flag)

    unknown = [eid for eid in draft.evidence_ids if eid not in allowed]
    if unknown:
        warnings.append(f"unknown_evidence_ids:{','.join(unknown)}")

    cited = citation_ids(draft.explanation) + citation_ids(draft.draft_feedback or "")
    unknown_cite = [eid for eid in cited if eid not in allowed]
    if unknown_cite:
        warnings.append(f"unknown_citation_ids:{','.join(sorted(set(unknown_cite)))}")

    if abs(draft.score_max - criterion.max_mark) > 1e-9:
        warnings.append("score_max_mismatch")

    claims = positive_claims(draft.explanation) if draft.sufficiency != "insufficient" else []
    bad_claims = unsupported_claims(draft.explanation) if draft.sufficiency != "insufficient" else []

    if draft.sufficiency == "insufficient":
        if draft.provisional_score is not None:
            warnings.append("score_present_when_insufficient")
    else:
        if draft.provisional_score is None:
            warnings.append("missing_score")
        else:
            score = draft.provisional_score
            if score < 0 or score > criterion.max_mark:
                warnings.append("score_out_of_range")
            step = criterion.granularity
            if abs(round(score / step) * step - score) > 1e-6:
                warnings.append("score_granularity")
        if not draft.evidence_ids:
            warnings.append("missing_evidence")
        if bad_claims:
            warnings.append(f"uncited_claim:{len(bad_claims)}")
        if draft.sufficiency == "sufficient" and not cited:
            warnings.append("supported_without_citation")

    accepted = not warnings
    if not accepted:
        draft.flags = list(dict.fromkeys([*draft.flags, *warnings, "validation_failed"]))
        codes = {w.split(":", 1)[0] for w in warnings}
        if codes & CRITICAL:
            draft.sufficiency = "insufficient"
            draft.provisional_score = None
        elif "score_present_when_insufficient" in codes:
            draft.provisional_score = None
        elif "score_granularity" in codes and draft.provisional_score is not None:
            step = criterion.granularity
            draft.provisional_score = max(0.0, min(criterion.max_mark, round(round(draft.provisional_score / step) * step, 4)))
    return ValidatedAssessment(
        draft=draft,
        accepted=accepted,
        warnings=warnings,
        claims=len(claims),
        unsupported_claims=len(bad_claims),
    )
