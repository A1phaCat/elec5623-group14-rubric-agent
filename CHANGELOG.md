# Changelog

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
