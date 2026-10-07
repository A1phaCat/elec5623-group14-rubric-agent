"""Invalid model values and factual feedback must fail closed."""

import json

import pytest

from rubric_agent.gateway import parse_model_json
from rubric_agent.schemas import AssessmentDraft, Criterion, EvidenceUnit
from rubric_agent.validator import validate_assessment


@pytest.fixture
def case():
    criterion = Criterion(id="C1", name="Method", max_mark=4, granularity=1)
    units = [EvidenceUnit(id="E-001", text="The method is documented.", page=1,
                          section="Method", paragraph=0)]
    draft = AssessmentDraft(criterion_id="C1", evidence_ids=["E-001"], sufficiency="partial",
                            provisional_score=2, score_max=4,
                            explanation="The method is documented [E-001].")
    return criterion, units, draft


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("field", ["provisional_score", "score_max"])
def test_non_finite_provider_values_rejected_at_schema(case, value, field):
    criterion, _, draft = case
    data = draft.model_dump()
    data[field] = value
    result = parse_model_json(json.dumps(data), criterion)
    assert "invalid_model_output" in result.flags
    assert result.provisional_score is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_mutated_non_finite_score_cannot_crash_validator(case, value):
    criterion, units, draft = case
    draft.provisional_score = value  # in-process callers can mutate Pydantic models
    result = validate_assessment(draft, criterion, units)
    assert not result.accepted
    assert "non_finite_score" in result.warnings
    assert result.draft.provisional_score is None


@pytest.mark.parametrize("feedback,warning", [
    ('The report includes ten experiments [E-001: "ten experiments"].', "quote_not_in_evidence"),
    ("The report includes ten experiments.", "uncited_feedback_claim"),
])
def test_feedback_cannot_bypass_evidence_checks(case, feedback, warning):
    criterion, units, draft = case
    draft.draft_feedback = feedback
    result = validate_assessment(draft, criterion, units)
    assert not result.accepted
    assert any(w.startswith(warning) for w in result.warnings)
    assert result.draft.provisional_score is None


def test_feedback_advice_and_exact_quote_remain_usable(case):
    criterion, units, draft = case
    draft.draft_feedback = 'The method is documented [E-001: "method is documented"]. Add an experiment.'
    assert validate_assessment(draft, criterion, units).accepted


def test_live_feedback_instruction_is_not_a_factual_claim(case):
    criterion, units, draft = case
    draft.draft_feedback = "Specify the metrics, baselines, scenarios, and labelled data for your evaluation plan."
    assert validate_assessment(draft.model_copy(deep=True), criterion, units).accepted
    draft.draft_feedback += " The report includes ten experiments."
    result = validate_assessment(draft, criterion, units)
    assert not result.accepted
    assert "uncited_feedback_claim:1" in result.warnings


@pytest.mark.parametrize("change,warning", [
    ({"criterion_id": "C2"}, "criterion_id_mismatch"),
    ({"provisional_score": 0.3}, "score_granularity"),
    ({"provisional_score": None}, "missing_score"),
])
def test_invalid_suggestion_is_not_silently_repaired(case, change, warning):
    criterion, units, draft = case
    result = validate_assessment(draft.model_copy(update=change), criterion, units)
    assert not result.accepted
    assert warning in result.warnings
    assert result.draft.provisional_score is None
