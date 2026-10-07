# Changelog

## Unreleased — robustness results, after the freeze

The frozen prompts, model settings and final-test inputs are unchanged.
Addendum A was predeclared, then run. Injection resistance is 0.972 of 36
pairs and order invariance is 0.750 of 12 permutations; both miss a target of
1.00. Removing decisive evidence never raised a judgement (0 of 4). Token
counts are post-processed from captured responses. The report states the
misses rather than a security claim.

## 1.0.0 — 7 Oct 2026, frozen for the final campaign

Tag `v1.0.0-frozen`. Configuration, digests and the rules for what would break
the freeze are in `docs/FREEZE.md`.

### The target was wrong before the prompt was

The first-pass labels assigned sufficiency by quality band, which contradicts
`dataset/LABELLING_GUIDE.md` rule 4 and matches the one-step-down bias recorded
in `docs/EVALUATION_NOTES.md` §2. Tuning against them would have optimised
toward that confusion, so the labels were corrected first:
`scripts/build_labels_v2.py` declares each change with a reason and refuses to
run if the source no longer matches. Seven of eight dev `partial` pairs became
`sufficient`; one was reviewed and kept. `labels.json` is untouched and the 19
heldout pairs are byte-identical.

That correction exposed a corpus property rather than hiding it: corrected dev
holds a single `partial` pair, so one third of macro-F1 now rests on one
judgement. The evaluator reports per-class precision, recall, F1 with gold
supports and the full confusion matrix so the mean is never read alone.

### Prompt selection, dev split only

`prompts/assessment_v4.md`, chosen from four variants in `docs/tuning/README.md`.
`assessment_v2` had the same quality/evidence conflation in its rule 2.
Separating the two questions cut one-step-down errors from 16 to 4 and raised
accuracy from 0.581 to 0.837 (v3), but v3 also told the model a `partial`
record could omit the score — which the validator fail-closes — destroying five
usable records, and it stopped producing draft feedback, leaving FR14
unexercised. v4 states the contract the validator enforces and requires
feedback: `missing_score` disappears, M17 returns to 1.00, score coverage is
the best of the four at 36/38, accuracy settles at 0.767. v5 is kept as a
recorded rejection for pushing four of five genuinely absent criteria to
`sufficient`.

`RMA_PROMPT_VERSION` selects a prompt for comparison runs; the active value is
recorded in every report's provenance.

### Evidence infrastructure

- `evaluate_corpus` takes `labels_path`, and `run_campaign.py` takes
  `--corpus`/`--labels`/`--split`, so the frozen final test runs through the
  same code as the development corpus. A corpus with no labels fails with a
  pointer to the annotation procedure.
- Annotation workspace for the 27 final-test pairs: blank per-annotator sheets,
  Cohen's kappa, three-class confusion, score agreement, and an adjudication
  step kept separate so agreement is computed before anyone discusses a
  disagreement. Nothing accepts an incomplete sheet.
- Marker-session kit with the proposal's own questionnaire items and a
  summariser that returns `null` plus a reason for every metric it lacks data
  for. M10 needs a timed manual arm or it stays unmeasured.
- `docs/CONTRIBUTIONS.md` is generated from git history; a member with no
  commits appears with zero rather than a description of intent.

### Verification

Clean clone installs with no steps beyond the README and passes 128 tests with
no API key and no network (`docs/validation/cleanroom_2026-10-07.md`). The wheel
ships no private document, and the bundled proposal PDF was text-extracted and
searched for every name and student ID with no match.

`docs/validation/freeze_guard_2026-10-07.md` records the freeze guard aborting a
real campaign after a version string changed mid-run, and refusing to resume
into the same directory. The change was harmless; the guard cannot know that,
and a results table assembled from two source trees cannot honestly report one
code hash.

### Still unmeasured

M9, M10, M11, M14 need real marker sessions. M3 is unmeasured on final_test,
whose labels carry no `must_contain`. The final-test campaign is blocked until
the independent annotation exists.

## 2026-10-04 — A2 and proposal-feedback improvements

- Correct novelty positioning against EFS, GradeAgentOps and RULERS; explicit evaluation protocol and named proposed delivery, with Zhengyu Han leading GenAI/evaluation.
- Reject non-finite/model-grid/feedback quote failures; prevent accepting invalid suggestions or exporting stale invalid edits.
- Add same-prompt full-context B3 and replay; improve denominator, abstention, scale-aware QWK, raw-output and hash evidence.
- Record current offline and local-model validation separately from historical 13 September results; preserve failed targets and remaining independent-study work.


## 22 Sep 2026 — documents only

No pipeline change. Added `docs/FINAL_REPORT_DRAFT.md` (A2's ten sections, using the 13 Sep local-model numbers only) and `docs/WEEK8_TUTOR_UPDATE.md`. Architecture note: Week 7 RAG/context applies; MCP is not added. `pytest -q`: 34 passed.

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
