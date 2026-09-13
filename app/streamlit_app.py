"""Entry point: streamlit run app/streamlit_app.py

Three pages, one process:
  Review      – marker workflow (FR7, FR12–FR15, NFR4, NFR5)
  Evaluation  – metric reports written by `rma eval --json` (M1–M17, agent vs B2)
  Run log     – every model call, with replay (FR16, NFR7, M12)
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent

st.set_page_config(page_title="Rubric Marking Agent", layout="wide")

page = st.navigation([
    st.Page(str(HERE / "review.py"), title="Review", icon=":material/rate_review:", default=True),
    st.Page(str(HERE / "evaluation.py"), title="Evaluation", icon=":material/monitoring:"),
    st.Page(str(HERE / "run_log.py"), title="Run log", icon=":material/history:"),
])
page.run()
