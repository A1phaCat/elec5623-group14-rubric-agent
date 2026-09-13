"""Headless Streamlit walk-through of scenario S8 (marker session) using AppTest.

Checks NFR4 (no prompt writing, just pick and click), NFR5 (export blocked until
every criterion has a decision) and FR7 (evidence shown with locators).
"""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def _start(example: str) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.run()
    at.sidebar.selectbox[0].select(example)
    at.sidebar.button[0].click()
    at.run()
    return at


def test_s8_marker_session_blocks_then_exports():
    at = _start("s1_standard (S1 baseline)")
    assert not at.exception
    text = " ".join(e.value for e in at.error)
    assert "Export blocked" in text, text
    # Evidence is shown in context with a locator (FR7).
    assert any("p.1" in m.value or "p.2" in m.value for m in at.markdown)

    # Every criterion gets a decision; edited ones need a score (FR12/FR13).
    for radio in at.radio:
        if radio.key and radio.key.startswith("act-"):
            radio.set_value("accepted")
    at.run()
    assert not at.exception
    errors = " ".join(e.value for e in at.error)
    # Criteria the fixture found insufficient cannot be 'accepted' with a score; reject them instead.
    for radio in at.radio:
        if radio.key and radio.key.startswith("act-"):
            cid = radio.key.split("-", 1)[1]
            score_widget = next((n for n in at.number_input if n.key == f"sc-{cid}"), None)
            if score_widget is not None and score_widget.value == 0.0:
                radio.set_value("rejected")
    at.run()
    assert not at.exception
    success = " ".join(s.value for s in at.success)
    assert "All criteria confirmed" in success, (success, errors)


def test_s6_fault_injection_shows_validator_warning():
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.run()
    at.sidebar.selectbox[0].select("s1_standard (S1 baseline)")
    at.sidebar.selectbox[1].select("unknown_id")
    at.sidebar.button[0].click()
    at.run()
    assert not at.exception
    warnings = " ".join(w.value for w in at.warning)
    assert "failed validation" in warnings
    errors = " ".join(e.value for e in at.error)
    assert "unknown_evidence_ids" in errors
