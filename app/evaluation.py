"""Evaluation dashboard: reads the JSON written by `rma eval --json` (M1–M17, per scenario, agent vs B2)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

st.title("Evaluation results")
st.caption("Numbers come from `rma eval` runs committed under docs/. Refresh with `rma eval --json docs/<name>.json --report docs/<NAME>.md`.")

# Campaign runs write A.json/B3.json into their own directory, so a flat glob
# over docs/ would hide the very reports the final report cites.
reports = sorted(ROOT.glob("docs/evaluation*.json")) + sorted(ROOT.glob("docs/evaluation*/[AB]*.json"))
if not reports:
    st.info("No evaluation JSON found under docs/. Run `rma eval --json docs/evaluation_fixture.json`.")
    st.stop()

labels = {str(p.relative_to(ROOT / "docs")): p for p in reports}
# Campaign results first: they describe the frozen build, the loose files are older.
order = sorted(labels, key=lambda name: ("/" not in name, name))
choice = st.selectbox("Report", order, index=0)
report = json.loads(labels[choice].read_text(encoding="utf-8"))
gen = report["generated_with"]
metrics = report["metrics"]
passes = report["pass"]
targets = report["targets"]
base = report.get("baseline_B2")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Gateway", gen["gateway"])
c2.metric("Prompt", gen["prompt_version"])
c3.metric("Labelled pairs", report["pairs"])
c4.metric("Submissions / rubrics", f"{report['submissions']} / {report['rubrics']}")
c5.metric("Repeats · split", f"{gen['repeats']} · {gen['split']}")


def _fmt(v):
    if isinstance(v, float):
        return round(v, 3)
    return v


st.subheader("Metrics against proposal targets")
rows = []
for key, target in targets.items():
    value = metrics.get(key)
    if value is None:
        continue
    higher = key not in {"M6_unsupported_rate", "M13_median_latency_ms", "M13_s5_latency_ms"}
    rows.append({"metric": key, "value": _fmt(value), "target": f"{'≥' if higher else '≤'} {target}",
                 "status": {True: "pass", False: "below target", None: "n/a"}[passes.get(key)]})
st.dataframe(rows, use_container_width=True, hide_index=True)
n_pass = sum(1 for v in passes.values() if v)
n_total = sum(1 for v in passes.values() if v is not None)
st.caption(f"{n_pass}/{n_total} targets met by this configuration. Metrics M9–M11, M14, M15 need a marker session and are collected in Week 11–12.")

other = {k: _fmt(v) for k, v in metrics.items() if k not in targets}
if other:
    with st.expander("Other reported values (M8 QWK/MAE, coverage, B2 figures)"):
        st.dataframe([{"metric": k, "value": v} for k, v in other.items()], use_container_width=True, hide_index=True)

if base:
    st.subheader("Agent vs baseline B2 (direct whole-document grading)")
    agent_like = {
        "sufficiency_macro_f1": metrics.get("M4_sufficiency_macro_f1"),
        "unsupported_rate": metrics.get("M6_unsupported_rate"),
        "score_qwk": metrics.get("M8_agent_qwk"),
        "score_mae": metrics.get("M8_agent_mae"),
        "score_coverage": metrics.get("M8_agent_score_coverage"),
    }
    st.dataframe([{"metric": k, "agent": _fmt(agent_like[k]), "B2": _fmt(base.get(k))} for k in agent_like],
                 use_container_width=True, hide_index=True)
    st.caption("B2 sees the whole document but cannot cite evidence units, so a marker cannot check any of its claims. "
               "The agent's unsupported-claim rate is what the validator lets through after its checks.")

if report.get("per_scenario"):
    st.subheader("Per test scenario (S1–S8)")
    st.dataframe([{"scenario": s, **{k: _fmt(v) for k, v in m.items()}} for s, m in report["per_scenario"].items()],
                 use_container_width=True, hide_index=True)

st.subheader("Validator activity")
st.write({
    "warnings_on_final_records": report.get("validator_warnings", {}),
    "first_attempt_rejections_fed_back_to_model": report.get("first_attempt_warnings", {}),
    "corrective_round_rate": _fmt(report.get("revision_rate")),
})

with st.expander("Raw JSON"):
    st.json(report)
