"""Regression coverage for the marker confirmation and export boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rubric_agent.errors import ExportBlocked
from rubric_agent.review import ReviewSession
from rubric_agent.schemas import AssessmentDraft, Criterion, ValidatedAssessment


def _assessment(*, accepted=True, sufficiency="partial", score=2):
    return ValidatedAssessment(
        draft=AssessmentDraft(
            criterion_id="C1", evidence_ids=["E-001"], sufficiency=sufficiency,
            provisional_score=score, score_max=4, explanation="The method is documented [E-001].",
        ),
        accepted=accepted,
        warnings=[] if accepted else ["invalid_model_output"],
    )


def _session(assessment=None, *, with_criteria=True):
    kwargs = {"criteria": [Criterion(id="C1", name="Method", max_mark=4, granularity=1)]} if with_criteria else {}
    return ReviewSession([assessment if assessment is not None else _assessment()], **kwargs)


@pytest.mark.parametrize("assessment", [
    _assessment(accepted=False),
    _assessment(accepted=False, sufficiency="insufficient", score=None),
    _assessment(sufficiency="insufficient", score=None),
    _assessment(score=None),
])
def test_invalid_or_absent_ai_score_requires_explicit_edit_or_reject(assessment):
    session = _session(assessment)
    with pytest.raises(ValueError, match="no validated score"):
        session.decide("C1", "accepted")
    with pytest.raises(ExportBlocked):
        session.export_json()
    session.decide("C1", "edited", score=1, comment="Human checked the source.")
    row = session.export_record()[0]
    assert row["marker_final_score"] == 1 and row["marker_state"] == "edited"
    assert row["ai_suggested_score"] == assessment.draft.provisional_score
    session.decide("C1", "rejected")
    assert session.export_record()[0]["marker_final_score"] is None


@pytest.mark.parametrize("score", [-1, 5, float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("with_criteria", [True, False])
def test_manual_score_must_be_finite_and_in_range_even_without_rubric(score, with_criteria):
    session = _session(with_criteria=with_criteria)
    with pytest.raises(ValueError, match="finite and inside"):
        session.decide("C1", "edited", score=score)
    assert session.unconfirmed() == ["C1"]


def test_manual_score_obeys_rubric_granularity_and_accepts_zero():
    session = _session()
    with pytest.raises(ValueError, match="rubric step"):
        session.decide("C1", "edited", score=0.3)
    session.decide("C1", "edited", score=0)
    assert json.loads(session.export_json())["criteria"][0]["marker_final_score"] == 0


def test_incomplete_or_duplicate_assessments_cannot_silently_drop_criteria():
    with pytest.raises(ValueError, match="non-empty"):
        ReviewSession([])
    with pytest.raises(ValueError, match="unique"):
        ReviewSession([_assessment(), _assessment()])
    with pytest.raises(ValueError, match="every rubric criterion"):
        ReviewSession([_assessment()], criteria=[
            Criterion(id="C1", name="Method", max_mark=4, granularity=1),
            Criterion(id="C2", name="Results", max_mark=4, granularity=1),
        ])


def test_repeated_ui_rerun_preserves_decision_timestamp_and_interventions(monkeypatch):
    monkeypatch.setattr("rubric_agent.review.utc_now", lambda: "2026-10-04T00:00:00+00:00")
    original = _assessment()
    session = _session(original)
    first = session.decide("C1", "accepted")
    # External pipeline changes cannot rewrite the suggestion already reviewed.
    original.draft.provisional_score = 3
    monkeypatch.setattr("rubric_agent.review.utc_now", lambda: "2026-10-04T01:00:00+00:00")
    repeated = session.decide("C1", "accepted")
    assert repeated.decided_at == first.decided_at
    assert session.interventions == 1
    assert session.export_record()[0]["ai_suggested_score"] == 2
    changed = session.decide("C1", "edited", score=1)
    assert changed.decided_at != first.decided_at and session.interventions == 2


def test_export_rechecks_mutated_or_missing_decisions():
    session = _session()
    session.decide("C1", "accepted")
    session.decisions["C1"].marker_score = 3
    with pytest.raises(ExportBlocked, match="differs"):
        session.export_json()
    session.decide("C1", "edited", score=1)
    session.decisions["C1"].marker_score = float("nan")
    with pytest.raises(ExportBlocked, match="finite"):
        session.export_csv()
    session.decisions.pop("C1")
    with pytest.raises(ExportBlocked, match="every criterion"):
        session.export_record()


def test_invalid_ui_replacement_clears_previous_confirmation():
    from streamlit.testing.v1 import AppTest

    app = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    at = AppTest.from_file(str(app), default_timeout=30).run()
    at.sidebar.selectbox[0].select("s1_standard (S1 baseline)")
    at.sidebar.button[0].click().run()
    assert not at.exception
    for radio in at.radio:
        if radio.key and radio.key.startswith("act-"):
            radio.set_value("rejected")
    at.run()
    assert "All criteria confirmed" in " ".join(s.value for s in at.success)
    at.radio(key="act-C1").set_value("edited").run()
    at.number_input(key="sc-C1").set_value(0.3).run()
    assert not at.exception
    assert "rubric step" in " ".join(e.value for e in at.error)
    assert at.session_state["session"].decisions["C1"].state == "pending"
    assert "Export blocked" in " ".join(e.value for e in at.error)
    assert not at.get("download_button")


def test_full_context_run_replays_with_its_logged_retrieval_method():
    from rubric_agent.pipeline import run_pipeline
    from rubric_agent.store import replay_entry

    dataset = Path(__file__).resolve().parents[1] / "dataset"
    result = run_pipeline(
        dataset / "rubrics" / "engineering_report.md",
        dataset / "submissions" / "s2_dispersed.txt",
        evidence_mode="full_context",
    )
    assert all(e.retrieval_method == "full-context-v1" for e in result.logs)
    assert all(e.retrieval_k == len(result.units) for e in result.logs)
    outcomes = [replay_entry(e) for e in result.logs]
    assert all(o.same_top1 and o.same_cited and o.within_tolerance for o in outcomes)
    changed = result.logs[0].model_copy(update={"retrieval_method": "unknown-v2"})
    with pytest.raises(ValueError, match="unknown retrieval method"):
        replay_entry(changed)
