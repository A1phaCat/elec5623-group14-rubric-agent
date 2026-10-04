"""Validator (FR9–FR11, scenario S6).

Runs after every model call and before anything reaches the marker. It is
deterministic code, not a model, so it can be tested exhaustively. Any critical
warning downgrades the record to `insufficient` with no score (fail-closed).
A quote written next to an evidence id must occur in that unit.
"""

from __future__ import annotations

import math

from .schemas import AssessmentDraft, Criterion, EvidenceUnit, ValidatedAssessment
from .textutil import citation_ids, cited_quotes, normalize, positive_claims, unsupported_claims

CRITICAL = {
    "score_out_of_range",
    "unknown_evidence_ids",
    "missing_evidence",
    "unknown_citation_ids",
    "uncited_claim",
    "quote_not_in_evidence",
    "invalid_model_output",
    "provider_error",
    "score_max_mismatch",
    "criterion_id_mismatch",
    "non_finite_score",
    "uncited_feedback_claim",
    "missing_score",
    "score_granularity",
    "supported_without_citation",
}


def validate_assessment(
    draft: AssessmentDraft,
    criterion: Criterion,
    evidence: list[EvidenceUnit],
) -> ValidatedAssessment:
    allowed = {u.id for u in evidence}
    by_id = {u.id: u for u in evidence}
    warnings: list[str] = []

    if draft.criterion_id != criterion.id:
        warnings.append("criterion_id_mismatch")

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

    # A quote tied to a known id must be a whitespace-normalised substring of that unit.
    # Unknown ids stay on the citation check above; a citation with no quote is unchanged.
    bad_quotes: list[str] = []
    for eid, quote in cited_quotes(draft.explanation) + cited_quotes(draft.draft_feedback or ""):
        unit = by_id.get(eid)
        span = normalize(quote)
        if unit is None or not span:
            continue
        if span not in normalize(unit.text):
            bad_quotes.append(eid)
    if bad_quotes:
        warnings.append("quote_not_in_evidence:" + ",".join(dict.fromkeys(bad_quotes)))

    if not math.isfinite(draft.score_max) or abs(draft.score_max - criterion.max_mark) > 1e-9:
        warnings.append("score_max_mismatch")

    if draft.provisional_score is not None and not math.isfinite(draft.provisional_score):
        warnings.append("non_finite_score")

    # Feedback can contain factual claims too. Imperative advice is not a claim
    # about existing work, but statements about the submission need a citation.
    feedback_claims = unsupported_claims(draft.draft_feedback or "")
    advice_openers = ("add ", "include ", "consider ", "explain ", "describe ", "provide ",
                      "clarify ", "improve ", "ensure ", "revise ", "specify ", "for ", "to improve")
    feedback_claims = [s for s in feedback_claims if not s.lower().startswith(advice_openers)]
    if feedback_claims:
        warnings.append(f"uncited_feedback_claim:{len(feedback_claims)}")

    claims = positive_claims(draft.explanation) if draft.sufficiency != "insufficient" else []
    bad_claims = unsupported_claims(draft.explanation) if draft.sufficiency != "insufficient" else []

    if draft.sufficiency == "insufficient":
        if draft.provisional_score is not None:
            warnings.append("score_present_when_insufficient")
    else:
        if draft.provisional_score is None:
            warnings.append("missing_score")
        elif math.isfinite(draft.provisional_score):
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
    return ValidatedAssessment(
        draft=draft,
        accepted=accepted,
        warnings=warnings,
        claims=len(claims),
        unsupported_claims=len(bad_claims),
    )
