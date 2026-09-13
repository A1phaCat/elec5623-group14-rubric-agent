"""Marker review UI (FR7, FR12, FR13, FR15, NFR4, NFR5).

Run: streamlit run app/streamlit_app.py
The marker never writes a prompt. Every criterion must be accepted, edited or
rejected before export is enabled.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rubric_agent import PROMPT_VERSION  # noqa: E402
from rubric_agent.errors import ExportBlocked, RubricParseError, SubmissionParseError  # noqa: E402
from rubric_agent.gateway import build_gateway  # noqa: E402
from rubric_agent.pipeline import run_pipeline  # noqa: E402

DATASET = ROOT / "dataset"
EXAMPLES = {
    "s1_standard (S1 baseline)": ("engineering_report", "s1_standard"),
    "s2_dispersed (S2 evidence spread out)": ("engineering_report", "s2_dispersed"),
    "s3_missing_eval (S3 criterion absent)": ("engineering_report", "s3_missing_eval"),
    "s4_decoy_eval (S4 keyword decoy)": ("engineering_report", "s4_decoy_eval"),
    "s5_long (S5 12 pages)": ("engineering_report", "s5_long"),
    "p3_decoy on proposal rubric (numbered format)": ("proposal_rubric", "p3_decoy"),
    "s1_standard on half-mark table rubric (S7)": ("half_mark", "s1_standard"),
}

st.set_page_config(page_title="Rubric Marking Agent", layout="wide")
st.title("AI-Assisted Rubric Marking Agent")
st.caption("ELEC5623 Group 14 · Track A prototype · provisional scores are suggestions, the marker decides.")

for key in ("result", "session", "case_id"):
    st.session_state.setdefault(key, None)

# --- Sidebar ------------------------------------------------------------------------
with st.sidebar:
    st.header("1 · Inputs")
    example = st.selectbox("Synthetic example", ["(upload my own)", *EXAMPLES])
    rubric_file = st.file_uploader("Rubric (.md / .txt / .pdf)", type=["md", "txt", "pdf"])
    submission_file = st.file_uploader("Submission (.txt / .pdf)", type=["txt", "pdf"])

    st.header("2 · Model")
    live_ready = bool(os.environ.get("RMA_MODEL_ENDPOINT") and os.environ.get("RMA_MODEL"))
    options = ["fixture (offline, deterministic)"] + (["live (RMA_* environment)"] if live_ready else [])
    gateway_choice = st.radio("Gateway", options, help="Live is only offered when RMA_MODEL_ENDPOINT and RMA_MODEL are set. Keys are never shown or logged.")
    fail_mode = st.selectbox("S6 fault injection (fixture only)", ["none", "unknown_id", "out_of_range", "uncited_claim", "invalid_json"])
    k = st.slider("Evidence units per criterion (K)", 1, 10, 5)
    run = st.button("Run review", type="primary", use_container_width=True)

    st.divider()
    st.caption(f"Prompt version `{PROMPT_VERSION}` · no student data is stored by this app.")


def _save_upload(upload, folder: str) -> Path:
    tmp = ROOT / "data" / folder / upload.name
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(upload.getvalue())
    return tmp


if run:
    spec = "fixture" if gateway_choice.startswith("fixture") else "live"
    if spec == "fixture" and fail_mode != "none":
        spec = f"fixture:{fail_mode}"
    try:
        gateway = build_gateway(spec)
        if example != "(upload my own)":
            rubric_id, sub_id = EXAMPLES[example]
            rubric_src: str | Path = DATASET / "rubrics" / f"{rubric_id}.md"
            sub_src: str | Path = DATASET / "submissions" / f"{sub_id}.txt"
            case_id = sub_id
        elif rubric_file and submission_file:
            rubric_src = _save_upload(rubric_file, "rubrics") if rubric_file.name.endswith(".pdf") else rubric_file.getvalue().decode("utf-8")
            sub_src = _save_upload(submission_file, "submissions") if submission_file.name.endswith(".pdf") else submission_file.getvalue().decode("utf-8")
            case_id = submission_file.name
        else:
            st.error("Pick an example or upload both a rubric and a submission.")
            st.stop()
        with st.spinner("Parsing, retrieving evidence and assessing…"):
            result = run_pipeline(rubric_src, sub_src, gateway=gateway, k=k, test_case_id=case_id)
        st.session_state.result = result
        st.session_state.session = result.review_session()
        st.session_state.case_id = case_id
        for key in list(st.session_state.keys()):
            if key.startswith(("act-", "sc-", "cm-")):
                del st.session_state[key]
    except (RubricParseError, SubmissionParseError) as exc:
        st.error(f"Could not read input: {exc}")
        st.stop()
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

result = st.session_state.result
session = st.session_state.session
if not result or not session:
    st.info("Pick a synthetic example in the sidebar (or upload a rubric and a submission) and press **Run review**.")
    st.stop()

# --- Header ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Criteria", len(result.rubric.criteria))
c2.metric("Evidence units indexed", len(result.units))
c3.metric("Pipeline latency", f"{result.latency_ms:.0f} ms")
c4.metric("Model", result.model_id)
st.caption(f"Rubric **{result.rubric.title}** ({result.rubric.source_format} format) · case `{st.session_state.case_id}` · pages {len(result.pages)}")

flagged = [a for a in result.assessments if not a.accepted]
if flagged:
    st.warning(f"{len(flagged)} criterion record(s) failed validation and were downgraded to *insufficient* with no score. Details are shown per criterion.")

with st.expander("Rubric as parsed (FR1–FR3)", expanded=False):
    for c in result.rubric.criteria:
        st.markdown(f"**{c.id} · {c.name}** — max {c.max_mark}, step {c.granularity}")
        for d in c.descriptors:
            st.markdown(f"&nbsp;&nbsp;&nbsp;`{d.score:g}` {d.text}")

# --- Per-criterion review ---------------------------------------------------------------
st.subheader("3 · Review each criterion")
for validated in result.assessments:
    draft = validated.draft
    crit = next(c for c in result.rubric.criteria if c.id == draft.criterion_id)
    decision = session.decisions[draft.criterion_id]
    badge = {"sufficient": "🟢", "partial": "🟡", "insufficient": "🔴"}[draft.sufficiency]
    state_badge = {"pending": "⏳", "accepted": "✅", "edited": "✏️", "rejected": "🚫"}[decision.state]
    title = f"{state_badge} {draft.criterion_id} · {crit.name} · {badge} {draft.sufficiency} · suggested {draft.provisional_score if draft.provisional_score is not None else '—'} / {crit.max_mark:g}"
    with st.expander(title, expanded=decision.state == "pending"):
        left, right = st.columns([3, 2])
        with left:
            if validated.warnings:
                st.error("Validator: " + "; ".join(validated.warnings))
            st.markdown("**AI explanation**")
            st.write(draft.explanation)
            if draft.sufficiency != "insufficient":
                st.caption(f"Grounding audit: {validated.claims - validated.unsupported_claims}/{validated.claims} positive claims carry an evidence ID.")
            if draft.draft_feedback:
                st.markdown("**Draft feedback (optional, FR14)**")
                st.write(draft.draft_feedback)
            hits = result.retrieved.get(draft.criterion_id, [])
            st.markdown(f"**Evidence** ({len(hits)} retrieved, {len(draft.evidence_ids)} cited)")
            if not hits:
                st.info("No relevant evidence found for this criterion (FR6 explicit state).")
            for unit in hits:
                cited = unit.id in draft.evidence_ids
                with st.container(border=True):
                    st.markdown(f"{'**' if cited else ''}{unit.id}{'**' if cited else ''} · {unit.locator}" + (" · cited" if cited else " · retrieved, not cited"))
                    if unit.adjacent_before:
                        st.caption("↑ " + unit.adjacent_before[:240])
                    st.write(unit.text)
                    if unit.adjacent_after:
                        st.caption("↓ " + unit.adjacent_after[:240])
        with right:
            st.markdown("**Marker decision**")
            states = ["pending", "accepted", "edited", "rejected"]
            action = st.radio("State", states, index=states.index(decision.state), key=f"act-{draft.criterion_id}", horizontal=True,
                              help="accepted = keep AI score · edited = your score overrides · rejected = no score recorded")
            default_score = decision.marker_score if decision.marker_score is not None else (draft.provisional_score or 0.0)
            score = st.number_input("Marker score", min_value=0.0, max_value=float(crit.max_mark), step=float(crit.granularity),
                                    value=float(default_score), key=f"sc-{draft.criterion_id}", disabled=action != "edited")
            comment = st.text_area("Marker comment", value=decision.marker_comment, key=f"cm-{draft.criterion_id}", height=90)
            if action == "pending":
                if decision.state != "pending":
                    session.reset(draft.criterion_id)
            else:
                try:
                    session.decide(draft.criterion_id, action, score=score, comment=comment)
                except ValueError as exc:
                    st.error(str(exc))

# --- Export -------------------------------------------------------------------------------
st.subheader("4 · Export")
missing = session.unconfirmed()
got, cap = session.total()
if missing:
    st.error(f"Export blocked (NFR5) until these criteria have a decision: {', '.join(missing)}")
else:
    st.success(f"All criteria confirmed. Marker total {got:g} / {cap:g}.")
    try:
        col_a, col_b = st.columns(2)
        col_a.download_button("Download review record (JSON)", data=session.export_json(),
                              file_name=f"review_{st.session_state.case_id}.json", mime="application/json", use_container_width=True)
        col_b.download_button("Download review record (CSV)", data=session.export_csv(),
                              file_name=f"review_{st.session_state.case_id}.csv", mime="text/csv", use_container_width=True)
        with st.expander("Preview record"):
            st.dataframe(session.export_record(), use_container_width=True)
    except ExportBlocked as exc:
        st.error(str(exc))
