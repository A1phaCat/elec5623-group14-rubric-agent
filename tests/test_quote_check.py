"""A quote written next to an evidence id must occur in that unit."""

from __future__ import annotations

from rubric_agent.schemas import AssessmentDraft, Criterion, EvidenceUnit
from rubric_agent.validator import validate_assessment


def _criterion() -> Criterion:
    return Criterion(id="C1", name="Problem definition", max_mark=4, granularity=1)


def _units() -> list[EvidenceUnit]:
    return [
        EvidenceUnit(
            id="E-001",
            text="The problem is scoped for tutors and markers.",
            page=1,
            section="Introduction",
            paragraph=0,
        ),
        EvidenceUnit(
            id="E-002",
            text="We will measure accuracy on a labelled set.",
            page=2,
            section="Evaluation",
            paragraph=1,
        ),
    ]


def _draft(explanation: str, evidence_ids: list[str] | None = None) -> AssessmentDraft:
    return AssessmentDraft(
        criterion_id="C1",
        evidence_ids=["E-001"] if evidence_ids is None else evidence_ids,
        sufficiency="partial",
        provisional_score=2,
        score_max=4,
        explanation=explanation,
    )


def test_quoted_span_that_occurs_in_the_cited_unit_is_kept():
    exact = validate_assessment(
        _draft('The submission scopes the problem for tutors [E-001: "scoped for tutors"].'),
        _criterion(),
        _units(),
    )
    assert exact.accepted
    assert exact.draft.provisional_score == 2
    assert exact.draft.sufficiency == "partial"
    assert not any(w.startswith("quote_not_in_evidence") for w in exact.warnings)

    # Whitespace inside the quotes is collapsed before the substring check.
    spaced = validate_assessment(
        _draft("The submission scopes the problem for tutors [E-001: 'scoped\nfor   tutors']."),
        _criterion(),
        _units(),
    )
    assert spaced.accepted and spaced.draft.provisional_score == 2

    plain = validate_assessment(
        _draft("The submission scopes the problem for tutors [E-001]."),
        _criterion(),
        _units(),
    )
    assert plain.accepted and plain.draft.provisional_score == 2


def test_quoted_span_missing_from_the_cited_unit_is_rejected():
    missing = validate_assessment(
        _draft('The submission scopes the problem for tutors [E-001: "a full evaluation plan"].'),
        _criterion(),
        _units(),
    )
    assert any(w.startswith("quote_not_in_evidence") for w in missing.warnings)
    assert not missing.accepted
    assert missing.draft.sufficiency == "insufficient"
    assert missing.draft.provisional_score is None
    assert "validation_failed" in missing.draft.flags

    # The words exist in E-002. Citing them from E-001 is still a miss.
    other_unit = validate_assessment(
        _draft('The submission names a labelled set [E-001: "labelled set"].'),
        _criterion(),
        _units(),
    )
    assert any(w.startswith("quote_not_in_evidence:E-001") for w in other_unit.warnings)
    assert other_unit.draft.provisional_score is None

    on_its_own_unit = validate_assessment(
        _draft('The submission names a labelled set [E-002: "labelled set"].', ["E-002"]),
        _criterion(),
        _units(),
    )
    assert on_its_own_unit.accepted and on_its_own_unit.draft.provisional_score == 2


def test_unknown_ids_and_uncited_claims_still_fail_closed():
    unknown = validate_assessment(
        _draft('Users are named [E-999: "tutors"].', ["E-999"]),
        _criterion(),
        _units(),
    )
    assert any(w.startswith("unknown_evidence_ids") for w in unknown.warnings)
    assert any(w.startswith("unknown_citation_ids") for w in unknown.warnings)
    assert unknown.draft.provisional_score is None

    uncited = validate_assessment(
        _draft("The submission fully addresses the problem. It is excellent."),
        _criterion(),
        _units(),
    )
    assert any(w.startswith("uncited_claim") for w in uncited.warnings)
    assert uncited.draft.sufficiency == "insufficient"
    assert uncited.draft.provisional_score is None
