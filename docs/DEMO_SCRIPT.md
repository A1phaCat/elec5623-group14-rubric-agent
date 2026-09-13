# Demo script (Week 13, ~8 minutes) and Q&A prep

Course rule: every member must be able to answer questions on the whole system.
Rehearse with the person who did *not* write each part driving that part.

## Setup (before the session)

```bash
cd rubric-marking-agent && source .venv/bin/activate
pytest -q                     # green
OLLAMA_CONTEXT_LENGTH=16384 ollama serve &     # local model; the UI lists it automatically
streamlit run app/streamlit_app.py
```

Pre-run the real case with the local model before the session (it takes ~2 min
for 6 criteria) and keep that browser tab; run the short synthetic cases live.
Have `docs/img/review_ui.png`, `docs/EVALUATION_live_qwen7b.md` and
`docs/EVALUATION.md` open as backup if the app or the model fails. If Ollama is
down, switch the gateway radio to *fixture*: same UI, same validator, same export.

## Story (what to say, what to click)

| Min | Say | Show |
|---|---|---|
| 0–1 | Problem: markers re-read long reports for each criterion; chatbots grade without showing where. Our agent is *evidence-first* and the marker keeps the final say. | Title slide / README |
| 1–2 | Rubric goes in as pasted text, table or PDF; no prompt writing. This one is the official Canvas rubric for the proposal, six criteria. | First example → "Rubric as parsed" expander (criteria, maxima, levels) |
| 2–4 | Real case: our own 16-page proposal PDF, local 7B model. Per criterion: top-K evidence with page/section, explanation with `[E-00N]` citations, suggested score on the 0.5 grid. Point at one *uncited* retrieved unit to show the marker sees what the model ignored. | Pre-run tab; open R3 (methodology) and R5 (plan) |
| 4–5 | Decoy case: the text *mentions* "evaluation" but has no plan. Agent returns `insufficient`, no score, and says why with a pointer. Then B2 on the same submission: with a real model it also spots the decoy — but every one of its sentences is unverifiable (no evidence IDs; 45/45 unsupported in the harness). The product's claim is traceability, not "smarter than a chatbot". | Example `s4_decoy_eval` C3; then "Run B2 on this submission" button, compare the evidence columns |
| 5–6 | Fault injection: model returns an unknown evidence ID / score 6 of 4 / claim without citation → validator downgrades, warning shown, nothing exported. With the live model, show a record marked "corrected once after validator feedback": the model broke a rule, was told, and fixed it — and the fix was checked again. | Sidebar "S6 fault injection" → `unknown_id`, run (fixture); then the live tab's blue notice |
| 6–7 | Human oversight: export blocked until every criterion is accepted/edited/rejected; edited score overrides but AI value is kept. | Set decisions, download CSV, show both columns |
| 7–8 | Evaluation: 62 labelled pairs, metrics M1–M17, per-scenario table, agent vs B2, two gateways side by side (fixture = harness check, Qwen 7B = real numbers). Replay one logged call from the Run-log page. | *Evaluation* page → pick `evaluation_live_qwen7b.json`; *Run log* page → Replay |

## Likely questions

**Why not just send the whole report to GPT?**
Baseline B2 does exactly that. With the local 7B model it actually agrees with our labels *better* than the agent (QWK 0.87 vs 0.48) — and 100 % of its claims have no evidence pointer, so a marker cannot check any of them. The agent's claims are 100 % cited because the validator refuses anything else. `docs/EVALUATION_NOTES.md` explains why the agreement gap is probably partly a labelling artefact and how Week 11's second-annotator round settles it. Do not hide this number; it is the most honest thing in the project.

**Isn't the fixture cheating?**
It is a deterministic stand-in so tests and CI run without a key or student data (Lab practice: dummy model). It never sees gold labels. Its M4 is deliberately reported as failing. The real numbers come from the local 7B model run in `docs/EVALUATION_live_qwen7b.md`.

**Why a local 7B model and not GPT-4-class?**
Proposal §6.3 names both as candidates. The local one needs no key, sends no text off the machine (NFR6) and gave us real numbers today. The adapter is the same class; switching to Azure is five environment variables (`docs/GOVERNANCE.md`).

**The model corrects itself — isn't that hiding errors?**
No: one round only, the corrected answer goes through the same validator, and both attempts are in the log. The evaluation reports how often correction was needed (`revision_rate`) and what the first mistakes were.

**What stops the model from inventing a page reference?**
It can only cite IDs from the set it was given; the validator checks every `[E-00N]` in the explanation and feedback against that set.

**How do you know it's reproducible?**
Every call logs model id, prompt version, K, retrieval method, query, evidence IDs and outputs. `rma replay` re-runs from the log and reports identical top-1 evidence and score drift (M12).

**What changes between fixture, local model and hosted model?**
Only the gateway (`--gateway fixture | ollama:<model> | live`). Parser, retriever, validator, UI and metrics are unchanged, which is the point of Constraint C5.

**What is out of scope and why?**
OCR/handwriting (C4), LMS integration (C2), autonomous grading (C1). These are product-scope decisions from the proposal, not schedule cuts.

**What did AI tools write?**
See `AI_USE.md`; the group reviewed and ran everything, and each member owns an area (A1–A5).

## Team split for the demo

| Segment | Area | Member |
|---|---|---|
| Rubric + ingestion | A1/A2 | |
| Retrieval + logs + eval | A3 | |
| Assessment + validator | A4 | |
| UI + oversight | A5 | |
