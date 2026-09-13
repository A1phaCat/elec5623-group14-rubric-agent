# Contributing (Group 14)

The unit assesses individual contribution through the repository history, so
work in your own branch and merge through pull requests.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
python scripts/generate_dataset.py
pytest -q
```

## Workflow

1. Branch from `main`: `git switch -c a3/retrieval-hybrid` (prefix = your area A1–A5).
2. Keep commits small and descriptive: `A4: validator rejects uncited claims (FR10)`.
3. Every PR must: keep `pytest -q` green, update `docs/REQUIREMENTS_TRACEABILITY.md` if an FR/test changed, and re-run `rma eval --report docs/EVALUATION.md` if retrieval, gateway or validator changed.
4. One reviewer from a different area approves before merge.
5. Never commit keys, `data/`, `.venv/` or real student files.

## Areas (proposal §10.2)

| Area | Scope | Main files |
|---|---|---|
| A1 | Rubric schema and parser | `rubric_parser.py`, `schemas.py` |
| A2 | Ingestion, export, storage | `text_parser.py`, `chunker.py`, `review.py` (export) |
| A3 | Retrieval, run log, evaluation harness | `retriever.py`, `store.py`, `eval.py` |
| A4 | Assessment prompt, gateway, validator | `gateway.py`, `prompts/`, `validator.py` |
| A5 | Marker UI and usability study | `app/streamlit_app.py`, `tests/test_ui.py` |

## Adding a labelled case

1. Write the submission with `scripts/generate_dataset.py` helpers (or add a real openly-licensed report under `dataset/submissions/`).
2. Add one `add(...)` line per criterion with the distinctive `must_contain` phrase, the sufficiency label and the reference score; follow `dataset/LABELLING_GUIDE.md`.
3. Put new held-out submissions in `HELDOUT`.
4. Re-run the generator and `pytest`.

## AI assistance

Allowed; disclose it in `AI_USE.md` (tool, what it produced, who reviewed).
