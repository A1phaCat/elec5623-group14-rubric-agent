# Demo script (Week 13, ~8 minutes) and Q&A prep

Course rule: every member must be able to answer questions on the whole system.
Rehearse with the person who did *not* write each part driving that part.

## Setup (before the session)

```bash
cd rubric-marking-agent && source .venv/bin/activate
pytest -q                     # green
rma eval --report docs/EVALUATION.md
streamlit run app/streamlit_app.py
```

Have `docs/img/review_ui.png` and `docs/EVALUATION.md` open as backup if the app fails.

## Story (what to say, what to click)

| Min | Say | Show |
|---|---|---|
| 0–1 | Problem: markers re-read long reports for each criterion; chatbots grade without showing where. Our agent is *evidence-first* and the marker keeps the final say. | Title slide / README |
| 1–2 | Rubric goes in as pasted text, table or PDF; no prompt writing. | Sidebar → "Rubric as parsed" expander (criteria, maxima, levels) |
| 2–4 | Standard case: per criterion, top-K evidence with page/section, explanation with `[E-00N]` citations, suggested score on the rubric scale. | Example `s1_standard`, open C1 and C3 |
| 4–5 | Decoy case: the text *mentions* "evaluation" but has no plan. Agent returns `insufficient`, no score. A naive whole-document grader gives full marks (baseline B2). | Example `s4_decoy_eval` C3; then terminal `rma baseline --submission s4_decoy_eval` |
| 5–6 | Fault injection: model returns an unknown evidence ID / score 6 of 4 / claim without citation → validator downgrades, warning shown, nothing exported. | Sidebar "S6 fault injection" → `unknown_id`, run |
| 6–7 | Human oversight: export blocked until every criterion is accepted/edited/rejected; edited score overrides but AI value is kept. | Set decisions, download CSV, show both columns |
| 7–8 | Evaluation harness: 62 labelled pairs, metrics M1–M17, per-scenario table, replay from log. Honest caveat: fixture numbers prove the harness; M4/M8 wait for the approved model. | `docs/EVALUATION.md`, `rma replay --log runs.jsonl` |

## Likely questions

**Why not just send the whole report to GPT?**
Baseline B2 does exactly that; in the harness 100% of its positive claims have no evidence pointer, and it scores the decoy as sufficient. The agent's claims are 100% cited because the validator refuses anything else.

**Isn't the fixture cheating?**
It is a deterministic stand-in so tests and CI run without a key or student data (Lab practice: dummy model). It never sees gold labels. Its M4 is deliberately reported as failing.

**What stops the model from inventing a page reference?**
It can only cite IDs from the set it was given; the validator checks every `[E-00N]` in the explanation and feedback against that set.

**How do you know it's reproducible?**
Every call logs model id, prompt version, K, retrieval method, query, evidence IDs and outputs. `rma replay` re-runs from the log and reports identical top-1 evidence and score drift (M12).

**What would a real model change?**
Only the gateway (`RMA_GATEWAY=live`). Everything else — parser, retriever, validator, UI, metrics — is unchanged, which is the point of Constraint C5.

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
