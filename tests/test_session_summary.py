"""The session summariser must report 'unmeasured' rather than a convenient number.

M9-M11 and M14 are the only human-workflow evidence this project will have, so
the failure mode that matters is a missing arm silently becoming 0, or a median
of one value being presented as a result. Each case is pinned here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.summarise_sessions import load_sessions, summarise

ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "docs/sessions"


def _session(arm: str, participant: str = "P1", **fields) -> dict:
    base = {
        "participant": participant, "arm": arm, "submission_id": "s1_standard",
        "rubric_id": "engineering_report", "_file": f"{participant}_{arm}.json",
        "questionnaire": {},
    }
    return {**base, **fields}


def test_no_sessions_leaves_every_human_metric_unmeasured():
    report = summarise([])
    assert report["status"] == "no sessions recorded"
    for key in ("M9_marker_correction_rate", "M10_review_time",
                "M11_perceived_usefulness_and_control", "M14_usability"):
        assert report[key].get("unmeasured_because"), key
    assert report["M9_marker_correction_rate"]["value"] is None
    assert report["M10_review_time"]["reduction"] is None
    assert report["M14_usability"]["evidence_in_context_rate"] is None


def test_agent_arm_alone_cannot_measure_review_time():
    report = summarise([_session("agent", duration_s=300.0)])
    m10 = report["M10_review_time"]
    assert m10["reduction"] is None and m10["target_met"] is None
    assert "both the agent and the manual arm" in m10["unmeasured_because"]
    assert m10["agent_median_s"] == 300.0 and m10["manual_median_s"] is None


def test_review_time_reduction_needs_both_arms_and_reports_participants():
    report = summarise([
        _session("manual", "P1", duration_s=600.0),
        _session("agent", "P1", duration_s=300.0),
    ])
    m10 = report["M10_review_time"]
    assert m10["reduction"] == pytest.approx(0.5)
    assert m10["target_met"] is True
    assert m10["participants_with_both_arms"] == ["P1"]
    # The sample size must travel with the claim.
    assert "not a reliable effect" in m10["note"]


def test_correction_rate_uses_edited_over_decided_and_keeps_rejected_separate():
    report = summarise([_session("agent", criteria_decided=5, accepted=3, edited=1, rejected=1)])
    m9 = report["M9_marker_correction_rate"]
    assert m9["value"] == pytest.approx(0.2)
    assert m9["edited_criteria"] == 1 and m9["criteria_decided"] == 5
    assert m9["rejected_criteria"] == 1
    assert "automation-bias" in m9["note"]


def test_questionnaire_items_carry_their_own_respondent_counts():
    report = summarise([
        _session("agent", "P1", questionnaire={"in_control_of_final_score": 5,
                                              "evidence_saved_me_searching": 4}),
        _session("agent", "P2", questionnaire={"in_control_of_final_score": 4,
                                              "what_would_you_change_first": "bigger evidence pane"}),
    ])
    items = report["M11_perceived_usefulness_and_control"]["items"]
    assert items["in_control_of_final_score"]["mean"] == pytest.approx(4.5)
    assert items["in_control_of_final_score"]["respondents"] == 2
    assert items["evidence_saved_me_searching"]["respondents"] == 1
    # An item nobody answered stays null rather than defaulting.
    assert items["would_trust_as_a_first_pass"]["mean"] is None
    assert items["would_trust_as_a_first_pass"]["respondents"] == 0
    assert report["M11_perceived_usefulness_and_control"]["target_met"] is True
    assert report["M11_perceived_usefulness_and_control"]["free_text"] == ["bigger evidence pane"]


def test_control_item_below_four_fails_its_declared_target():
    report = summarise([_session("agent", questionnaire={"in_control_of_final_score": 3})])
    assert report["M11_perceived_usefulness_and_control"]["target_met"] is False


def test_usability_targets_need_both_tallies():
    report = summarise([_session("agent", facilitator_interventions=0,
                                 evidence_items_opened_in_context=6,
                                 evidence_items_found_by_searching_document=0)])
    m14 = report["M14_usability"]
    assert m14["intervention_target_met"] is True
    assert m14["evidence_in_context_rate"] == 1.0 and m14["evidence_target_met"] is True

    worse = summarise([_session("agent", facilitator_interventions=3,
                                evidence_items_opened_in_context=4,
                                evidence_items_found_by_searching_document=2)])["M14_usability"]
    assert worse["intervention_target_met"] is False
    assert worse["evidence_in_context_rate"] == pytest.approx(4 / 6)
    assert worse["evidence_target_met"] is False


def test_an_unknown_arm_is_rejected(tmp_path):
    (tmp_path / "P9_other.json").write_text(json.dumps({"participant": "P9", "arm": "other"}), encoding="utf-8")
    with pytest.raises(SystemExit, match="arm must be"):
        load_sessions(tmp_path)


def test_template_is_not_loaded_as_a_session():
    assert (SESSIONS / "TEMPLATE.json").is_file()
    assert load_sessions(SESSIONS) == [], (
        "docs/sessions holds a real session file; recompute summary.json and update the report"
    )


def test_limits_always_state_the_participant_count():
    report = summarise([_session("agent", "P1", duration_s=10.0)])
    assert any("participant(s)" in line for line in report["limits"])
    assert any("Synthetic submissions only" in line for line in report["limits"])
