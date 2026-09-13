# Changelog

## 0.3.0 — 13 Sep 2026 (evening)

First numbers from a real model, a real document on the real rubric, and the
robustness work both of them forced.

### Real model, real numbers
- Installed a local open-weight model (Ollama, `qwen2.5:7b-instruct`, 16k context) — candidate (b) of proposal §6.3 — and ran the full harness with it: `docs/EVALUATION_live_qwen7b.md` / `.json`. Headline: 12 of 13 targets met; M6 unsupported-claim rate 0.00 vs 1.00 for B2; M12 0.97; 46 s per submission. M4 macro-F1 0.55 (target 0.75) — the agent is one step more conservative than our single-annotator labels, while B2 agrees with them better (QWK 0.87 vs 0.48) with zero traceable claims. A k=10 control run shows the gap is not retrieval coverage. Full reading in `docs/EVALUATION_NOTES.md`.
- `build_gateway("ollama:<model>")` for a local server without environment variables; the UI lists running Ollama models by itself; `rma replay` rebuilds the gateway that produced each log line (`store.gateway_spec_for`).
- Live gateway: `max_tokens`, 180 s timeout, one re-ask when the reply is not valid JSON (the parse error is quoted back).

### Real rubric, real document
- `dataset/real/`: the official Canvas marking rubric for the proposal (6 criteria, 10 marks, descriptors verbatim) and our own 16-page proposal PDF (cover page with names/IDs removed). First example in the UI; parsed and run in CI.
- What the real PDF broke, and the fixes: PDF text loses blank lines, so one page became one 450-word unit → the text parser now keeps line structure and detects headings (`2.1 Title`, `#`, ALL CAPS), the chunker starts a unit at each heading, groups paragraphs to ~160 words and splits long PDF paragraphs on sentences (median unit 83 words, max 194 on the real document; every unit carries a real section name).
- Table rubrics with graded bands (`Excellent (8–10)`) and no `Max` column now parse (S7).

### Validator ↔ model loop (FR11)
- **One corrective round**: when the validator rejects a record, `gateway.revise()` sends the model its own answer plus the findings; the revision is validated again and flagged `revised_once`; both attempts are logged (`attempts`, `first_attempt_warnings`) and reported (`revision_rate`). The fixture cannot revise, so nothing changes offline.
- Citation recogniser accepts `[E-001, E-002]` and `[E-001: "quote"]`; IDs are still checked against the retrieved set.
- Claim detector (M6) no longer counts sentences that state an absence ("does not mention…") or relate the finding to the rubric ("aligns with the descriptor for 4.0") as positive claims — those cannot point at a span. Cited sentences are always counted. Real explanations from the 7B model were being rejected for exactly these sentence types.
- Sentence splitter no longer splits on `;` or inside quoted rubric text (fixture explanations quoting descriptors were failing their own audit).
- Prompt bumped to `assessment_v2`: explicit `allowed_evidence_ids`, `output_schema`, a format example for a *different* criterion (the 7B model copied the previous example verbatim), sharper `partial` vs `insufficient` definition aligned with `dataset/LABELLING_GUIDE.md`.
- B2 prompt now lists `criterion_ids` and asks for `{"criteria": [...]}` explicitly; parser accepts the shapes one-shot graders actually return (single object, bare list, dict keyed by id) with one re-ask. The first live run returned one criterion instead of five, which made the B2 comparison meaningless.

### Review session (M10, M11)
- `ReviewSession.summary()`: start/export time, duration, accepted/edited/rejected counts, override rate, intervention count; included in the JSON export header.

### UI
- `st.navigation` with three pages: **Review** (adds B2 side-by-side on the current submission, session duration in the export line, "corrected once" notices), **Evaluation** (any `docs/evaluation*.json`, targets, agent vs B2, per scenario, validator activity), **Run log** (table + one-click replay).

### Engineering
- `ruff` configured and clean; in CI. 34 tests (was 28).

## 0.2.0 — 13 Sep 2026

Major rework after re-reading the course requirements (Week 1 project brief
items, Lab 2 AI-component separation, Lab 4 evaluation discipline, Lab 5/6
tools-and-permissions rules) against the approved Group 14 proposal.

### Honesty of the evaluation
- The gateway under test **no longer receives gold labels**. In 0.1 the fixture read the label to produce its answer, so M4 was meaningless. M4/M8 are now reported honestly and the fixture fails M4 as expected.
- Added baseline **B2** (direct whole-document grading) through the same gateway class, and the M6 relative-reduction and M8 comparison from proposal Table 8.4.
- Added M1 (criteria), M3 Precision@5, M5 "supports" proxy, M8 QWK/MAE, M16 export completeness, M17 feedback grounding, per-scenario table, dev/held-out split, Markdown report (`docs/EVALUATION.md`).

### Model gateway (Constraint C5, NFR6)
- `OpenAICompatibleGateway`: OpenAI / Azure AI Foundry / Ollama via `RMA_*` environment variables; strict Listing 6.1 parsing; fail-closed on bad JSON or transport errors; injectable transport so it is unit-tested without network.
- `build_gateway("fixture" | "fixture:<fault>" | "live")` factory; `--gateway` on the CLI; gateway radio in the UI (live only when configured).
- Versioned prompts: `assessment_v1.md` rewritten with the six validator-checked rules; new `direct_grading_v1.md` for B2.

### Grounding (FR10, M6)
- Sentence-level positive-claim audit (`textutil.positive_claims`); validator warning `uncited_claim` downgrades the record. New S6 fault modes `uncited_claim`, `invalid_json`.

### Parsing and retrieval
- Rubric formats: block, table, **numbered list** (`1. Name (4 marks)`), **PDF**. Descriptor levels outside 0..max and duplicate IDs are rejected.
- Retrieval query uses the criterion name (double weight) and upper-level descriptors; crude stemming shared by retriever and fixture.

### Review and export (FR12–FR15, NFR5)
- Export rows include criterion name, max mark, evidence locators, model id, prompt version; CSV in addition to JSON; edited scores range-checked; `reset()` to un-decide.

### Reproducibility (FR16, NFR7, M12)
- Run log records inputs and outputs; `rma replay --log runs.jsonl` re-executes each call and reports top-1/cited/score drift.

### UI
- Rubric-as-parsed panel, cited vs uncited evidence, grounding audit line, S6 fault injection, K slider, CSV/JSON download, marker total. Headless AppTest walk-through in `tests/test_ui.py`.

### Dataset
- Third rubric (proposal style, 2.5-mark steps) + 3 submissions → 62 labelled pairs, 19 held-out; PDF rubric fixture.

### Repository evidence
- `docs/ARCHITECTURE.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/GOVERNANCE.md`, `docs/DEMO_SCRIPT.md`, `CONTRIBUTING.md`, GitHub Actions CI (tests + dataset reproducibility + eval artifact).

## 0.1.0 — 12 Sep 2026

First runnable prototype of the Must path with a gold-driven fixture (superseded).
