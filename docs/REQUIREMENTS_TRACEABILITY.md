# Requirements traceability

Proposal v2 §4.5–4.8 → code → test → metric. Owner codes A1–A5 are the
responsibility areas from proposal §10.2. Named owners below are proposed, pending team confirmation; they do not assert past authorship. Zhengyu Han leads the core GenAI system and evaluation design (see `TEAM_DELIVERY.md`). Who has actually committed what is generated from git history in `CONTRIBUTIONS.md`, not asserted here.

Current measurement state is in `../STATUS.md`; the frozen configuration these
results belong to is `FREEZE.md`.

| ID | Priority | Requirement (short) | Implemented in | Test | Metric | Owner |
|---|---|---|---|---|---|---|
| FR1 | Must | Rubric as pasted text or document | `rubric_parser.parse_rubric` (str, .md/.txt/.pdf) | `test_fr1_pasted_text_and_pdf_rubric` | M1 | A1 — Zongjian Li |
| FR2 | Must | Decompose into criteria | `_parse_blocks/_parse_table/_parse_numbered`; table headers may be numbers or graded bands (`Excellent (8–10)`) | `test_fr1_fr3_block_rubric`, `test_fr1_numbered_rubric_format`, `test_fr1_s7_banded_table_rubric_without_max_column`, `test_real_canvas_rubric_and_real_pdf_parse` | M1 | A1 — Zongjian Li |
| FR3 | Must | Maxima + descriptors | same; `_make` rejects out-of-range levels | `test_fr2_fr3_s7_table_rubric_half_marks`, `test_fr3_rejects_*` | M1 | A1 — Zongjian Li |
| FR4 | Must | TXT / text-PDF submission | `text_parser.parse_submission`; heading detection for PDF text | `test_fr4_fr5_txt_and_pdf_with_locators`, `test_real_canvas_rubric_and_real_pdf_parse` (16-page real PDF) | M2 | A2 — Yuchun Zheng |
| FR5 | Must | Evidence units with locators | `chunker.chunk_pages` (heading-aware grouping, sentence split of long PDF paragraphs), `EvidenceUnit.locator` | same | M2 | A2 — Yuchun Zheng |
| FR6 | Must | Ranked evidence or explicit empty | `retriever.BM25Retriever` | `test_fr6_topk_or_explicit_empty`, `test_s2_*` | M3 | A3 — Yutong Liu |
| FR7 | Must | Inspect evidence in context | Streamlit: cited/uncited units, ↑/↓ adjacent context, locator | `tests/test_ui.py::test_s8_*` | M14 (session) | A5 — Zhaoxinyi Zhou |
| FR8 | Should | Sufficiency label | gateway output, validated | `test_corpus_harness_targets` (reported) | M4 | A3 — Yutong Liu |
| FR9 | Must | Score constrained by rubric | `validator` range + granularity | `test_fr9_fr10_*`, `test_fr11_s6_*[out_of_range]` | M7 | A4 — Zhengyu Han |
| FR10 | Must | Explanation grounded in evidence | `textutil.positive_claims`, `citation_ids` (accepts `[E-001, E-002]`, `[E-001: "…"]`), validator `uncited_claim` | `test_fr11_s6_*[uncited_claim]`, `test_citation_variants_are_recognised_but_still_checked` | M5, M6 | A4 — Zhengyu Han |
| FR11 | Must | Flag weak evidence / validation failure | `validator` (fail-closed), one corrective round via `gateway.revise` then re-validation, UI warning | `test_fr11_s6_validator_fails_closed` (4 modes), `test_live_gateway_corrective_round_after_validator_rejection` | M6, M7 | A4 — Zhengyu Han |
| FR12 | Must | Accept provisional score | `ReviewSession.decide("accepted")` | `test_fr12_fr13_fr15_nfr5_*` | M16 | A5 — Zhaoxinyi Zhou |
| FR13 | Must | Edit score + comment; AI value retained | `decide("edited")`, range check; export keeps both | same, `test_fr13_edited_score_must_be_in_range` | M9, M16 | A5 — Zhaoxinyi Zhou |
| FR14 | Should | Draft feedback, required unless `insufficient` | gateway `draft_feedback`; `assessment_v4` rule 7 requires it for scored records; validator checks its citations | `test_corpus_harness_targets` (M17) | M17 | A4 — Zhengyu Han |
| FR15 | Should | Structured export | `export_record/export_json/export_csv`, `EXPORT_FIELDS` | `test_fr12_fr13_fr15_nfr5_*` | M16 | A2 — Yuchun Zheng |
| FR16 | Should | Log every model call | `RunLogEntry` (incl. `attempts`, `first_attempt_warnings`), `RunLogger`; Run-log page | `test_fr16_nfr7_run_log_and_replay` | M12 | A3 — Yutong Liu |
| NFR1 | — | Traceability ≥95% | validator + eval M5 | `test_corpus_harness_targets` | M5 | A4 — Zhengyu Han |
| NFR2 | — | Reliability across 3 runs | `eval` repeats, `store.replay_entry` | same + replay test | M12 | A3 — Yutong Liu |
| NFR3 | — | ≤120 s for 10–20 pages | `eval` M13; concurrent criterion calls. **Met**: median 33.1 s over 9 submissions in `docs/evaluation_dev_frozen/`, against 126 s on the September serial build | same | M13 | A2 — Yuchun Zheng |
| NFR4 | — | No prompt writing, ≤1 intervention | Streamlit flow; `ReviewSession.summary()` records duration, overrides, interventions | `test_ui.py` (headless S8) | M10, M11, M14 (session) | A5 — Zhaoxinyi Zhou |
| NFR5 | — | Export blocked until all confirmed | `ReviewSession.export_record` raises `ExportBlocked` | `test_fr12_fr13_fr15_nfr5_*`, `test_ui.py` | M15 | A5 — Zhaoxinyi Zhou |
| NFR6 | — | No real student data to any model | synthetic corpus + our own proposal only (`dataset/real/README.md`); local Ollama keeps text on the machine; hosted gateway opt-in via env | `test_build_gateway_from_env_*` | M15 (audit) | all |
| NFR7 | — | Reproducibility | run log fields + `rma replay` | `test_fr16_nfr7_*` | M12 | A3 — Yutong Liu |

## Scenarios

| Scenario | Fixture / test |
|---|---|
| S1 standard | `s1_standard`, `test_fr9_fr10_*` |
| S2 dispersed | `s2_dispersed`, `test_s2_dispersed_evidence_reaches_topk` |
| S3 missing | `s3_missing_eval`, `p2_gaps`, `test_fr6_topk_or_explicit_empty` |
| S4 decoy | `s4_decoy_eval`, `p3_decoy`, `test_s4_decoy_never_positive` |
| S5 long | `s5_long` (12 pages), M13 in eval; real 16-page PDF in `dataset/real/` |
| S6 malformed output | `FixtureGateway(fail_mode=…)`, live-gateway stub tests (bad JSON, transport error, corrective round) |
| S7 unusual rubric | `half_mark.md` (0.5 steps, table), `proposal_rubric.md` (2.5 steps, numbered), banded table without Max column, official Canvas rubric (block, 0.5 steps) |
| S8 marker session | `tests/test_ui.py` headless; real sessions still required for M9–M11, M14 |

## Not covered by software

M9–M11 and M14 need two to three real marker sessions, each including a timed
rubric-only arm or M10 cannot be computed at all. Protocol and recording kit:
`docs/MARKER_SESSIONS.md`; `scripts/summarise_sessions.py` reports each metric
as `null` with a reason until the data exists, and currently reports all four
that way.

M5's "human judged to support the claim" is approximated by phrase overlap
(`M5_citation_supports_proxy`) until the annotation round.

M3 is measured on the development corpus only. The final-test labels built by
`scripts/adjudicate_annotations.py` carry no `must_contain` phrases, so
retrieval relevance is **unmeasured** there rather than inherited.

## 4 October integrity extensions

| Requirement | Current verification | Proposed lead |
|---|---|---|
| FR9–FR11, FR14: finite, rubric-aligned model values; explanations and feedback checked | `tests/test_validator_integrity.py` | Zhengyu Han |
| FR12–FR13, NFR5: invalid suggestions cannot be accepted; invalid edits block export | `tests/test_review_integrity.py`, including headless UI | Zhaoxinyi Zhou, with Zhengyu Han on validation |
| FR6, FR16/NFR7: full-context ablation recorded and replayed | `tests/test_context_ablation.py`, `test_full_context_run_replays_with_its_logged_retrieval_method` | Yutong Liu |
| Evaluation evidence: denominators, abstention coverage, scale-aware QWK, source/data/prompt hashes | `tests/test_evaluation_integrity.py`, `EVALUATION_PROTOCOL.md` | Zhengyu Han designs; Yutong Liu executes |

M6 checks uncited positive sentences, not semantic hallucinations. M5/M17 are
structural/proxy checks until independently annotated. Current-code fixture
results and historical 13 September live results are separate artifacts.
