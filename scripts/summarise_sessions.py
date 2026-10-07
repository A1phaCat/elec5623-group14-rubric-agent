"""Compute M9, M10, M11 and M14 from recorded marker sessions.

Reads every `docs/sessions/<participant>_<arm>.json` except the template and
writes `docs/sessions/summary.json`.

The point of this script is to refuse to produce a number it does not have.
A metric with no data comes back `null` with a stated reason, never 0 and never
an estimate. M10 in particular needs both the agent and the manual arm from the
same participants, so a tool-only session leaves it unmeasured.

    .venv/bin/python scripts/summarise_sessions.py

Definitions are the proposal's (§8.4); see docs/MARKER_SESSIONS.md.
"""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "docs/sessions"
QUESTIONS = (
    "in_control_of_final_score",
    "evidence_saved_me_searching",
    "could_tell_where_score_came_from",
    "would_trust_as_a_first_pass",
    "interface_stayed_out_of_my_way",
)


def load_sessions(directory: Path) -> list[dict]:
    sessions = []
    for path in sorted(directory.glob("*.json")):
        if path.name in {"TEMPLATE.json", "summary.json"}:
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        record["_file"] = path.name
        if record.get("arm") not in {"agent", "manual"}:
            raise SystemExit(f"{path.name}: arm must be 'agent' or 'manual'")
        if not record.get("participant"):
            raise SystemExit(f"{path.name}: participant is required")
        sessions.append(record)
    return sessions


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def summarise(sessions: list[dict]) -> dict:
    agent = [s for s in sessions if s["arm"] == "agent"]
    manual = [s for s in sessions if s["arm"] == "manual"]
    participants = sorted({s["participant"] for s in sessions})

    # M9: criteria whose AI score the marker changed, over criteria decided.
    edited = [s["edited"] for s in agent if s.get("edited") is not None]
    decided = [s["criteria_decided"] for s in agent if s.get("criteria_decided") is not None]
    rejected = [s["rejected"] for s in agent if s.get("rejected") is not None]
    m9 = {
        "value": (sum(edited) / sum(decided)) if edited and decided and sum(decided) else None,
        "edited_criteria": sum(edited) if edited else None,
        "criteria_decided": sum(decided) if decided else None,
        "rejected_criteria": sum(rejected) if rejected else None,
        "sessions": len(agent),
        "target": "reported, not pass/fail",
        "note": "A correction rate near zero is not accuracy; read it with M8 as an automation-bias signal (proposal R3).",
    }
    if m9["value"] is None:
        m9["unmeasured_because"] = "no agent-arm session recorded edited and criteria_decided"

    # M10: median time per submission, agent vs manual.
    agent_times = [s["duration_s"] for s in agent if s.get("duration_s") is not None]
    manual_times = [s["duration_s"] for s in manual if s.get("duration_s") is not None]
    both = sorted({s["participant"] for s in agent if s.get("duration_s") is not None}
                  & {s["participant"] for s in manual if s.get("duration_s") is not None})
    agent_median, manual_median = _median(agent_times), _median(manual_times)
    m10 = {
        "agent_median_s": agent_median,
        "manual_median_s": manual_median,
        "agent_sessions": len(agent_times),
        "manual_sessions": len(manual_times),
        "participants_with_both_arms": both,
        "reduction": None,
        "target": ">=0.20 reduction",
        "target_met": None,
    }
    if agent_median is not None and manual_median and manual_median > 0:
        m10["reduction"] = (manual_median - agent_median) / manual_median
        m10["target_met"] = m10["reduction"] >= 0.20
        m10["note"] = (f"Median of {len(agent_times)} agent and {len(manual_times)} manual timings. "
                       "A median over so few sessions is not a reliable effect.")
    else:
        m10["unmeasured_because"] = (
            "M10 is a comparison and needs timings from both the agent and the manual arm; "
            f"recorded agent={len(agent_times)}, manual={len(manual_times)}"
        )

    # M11: questionnaire, per item, with its own denominator.
    items = {}
    for key in QUESTIONS:
        answers = [s["questionnaire"][key] for s in sessions
                   if isinstance(s.get("questionnaire"), dict) and s["questionnaire"].get(key) is not None]
        items[key] = {
            "mean": (sum(answers) / len(answers)) if answers else None,
            "answers": answers,
            "respondents": len(answers),
        }
    control = items["in_control_of_final_score"]
    m11 = {
        "items": items,
        "target": "in_control_of_final_score mean >= 4/5",
        "target_met": (control["mean"] >= 4) if control["mean"] is not None else None,
        "free_text": [s["questionnaire"].get("what_would_you_change_first", "")
                      for s in sessions if isinstance(s.get("questionnaire"), dict)
                      and s["questionnaire"].get("what_would_you_change_first")],
    }
    if control["mean"] is None:
        m11["unmeasured_because"] = "no participant answered the control item"

    # M14: facilitator interventions, and whether evidence was read in context.
    interventions = [s["facilitator_interventions"] for s in agent
                     if s.get("facilitator_interventions") is not None]
    in_context = [s["evidence_items_opened_in_context"] for s in agent
                  if s.get("evidence_items_opened_in_context") is not None]
    searched = [s["evidence_items_found_by_searching_document"] for s in agent
                if s.get("evidence_items_found_by_searching_document") is not None]
    total_evidence = sum(in_context) + sum(searched) if in_context or searched else 0
    m14 = {
        "interventions_per_session": interventions,
        "max_interventions": max(interventions) if interventions else None,
        "sessions": len(agent),
        "intervention_target": "<=1 per session",
        "intervention_target_met": (max(interventions) <= 1) if interventions else None,
        "evidence_in_context_rate": (sum(in_context) / total_evidence) if total_evidence else None,
        "evidence_items_in_context": sum(in_context) if in_context else None,
        "evidence_items_searched_manually": sum(searched) if searched else None,
        "evidence_target": "1.00 of evidence items opened in context",
        "evidence_target_met": (sum(searched) == 0) if searched or in_context else None,
    }
    if not interventions:
        m14["unmeasured_because"] = "no agent-arm session recorded a facilitator intervention tally"

    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "no sessions recorded" if not sessions else "derived from the session files in this directory",
        "participants": participants,
        "sessions": [{"file": s["_file"], "participant": s["participant"], "arm": s["arm"],
                      "submission_id": s.get("submission_id")} for s in sessions],
        "agent_sessions": len(agent),
        "manual_sessions": len(manual),
        "M9_marker_correction_rate": m9,
        "M10_review_time": m10,
        "M11_perceived_usefulness_and_control": m11,
        "M14_usability": m14,
        "limits": [
            f"{len(participants)} participant(s), convenience sample, non-expert, one session per arm.",
            "Synthetic submissions only; no real student work was marked.",
            "These numbers describe this prototype with these documents, not university marking.",
            "Any metric reported as null above is unmeasured and must be written as 'not measured'.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=SESSIONS)
    parser.add_argument("--output", type=Path, default=SESSIONS / "summary.json")
    args = parser.parse_args()
    sessions = load_sessions(args.directory)
    report = summarise(sessions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not sessions:
        print(f"No session files in {args.directory}. M9, M10, M11 and M14 remain unmeasured.")
    else:
        print(f"{len(sessions)} session file(s), {len(report['participants'])} participant(s).")
        for key in ("M9_marker_correction_rate", "M10_review_time",
                    "M11_perceived_usefulness_and_control", "M14_usability"):
            metric = report[key]
            reason = metric.get("unmeasured_because")
            print(f"  {key}: {'UNMEASURED - ' + reason if reason else 'measured'}")
    print(f"wrote {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
