# Architecture

This follows the Lab 2 practice of separating the *AI component* from the
deterministic software around it, and the Lab 6 rule that a connection to a
model is not permission to trust its output.

## 1. Context

```mermaid
flowchart LR
    Marker[Marker / tutor] -->|rubric, submission| UI[Review UI<br/>Streamlit]
    UI --> Agent[Rubric Marking Agent<br/>Python package]
    Agent -->|criterion + evidence only| LLM[(Assessment model<br/>hosted or local)]
    Agent --> Log[(Run log JSONL)]
    UI -->|review record JSON/CSV| Marker
    Coordinator[Unit coordinator] -.->|reads| Log
```

The final grade is never produced by the system (Constraint C1). The model sees
one criterion and at most K evidence units on the default BM25 path. B3 deliberately sends all indexed units; B2 sends the whole rubric/document. The parser does not automatically remove identities, so authorised inputs must be checked before use.

## 2. Containers and modules

```mermaid
flowchart TB
    subgraph Deterministic["Deterministic code (regression tested)"]
        RP[rubric_parser<br/>block · table · numbered · PDF]
        TP[text_parser<br/>TXT / PDF → pages + sections]
        CH[chunker<br/>EvidenceUnit E-00N with locator]
        RT[retriever<br/>BM25 top-K or empty]
        VA[validator<br/>schema · range · citations · claims]
        RV[review<br/>decisions · export · NFR5 gate]
        ST[store<br/>run log · replay]
    end
    subgraph AI["AI component (swappable, Constraint C5)"]
        GW[gateway.ModelGateway]
        FX[FixtureGateway<br/>offline heuristic]
        LV[OpenAICompatibleGateway<br/>OpenAI · Azure · Ollama]
        GW --- FX
        GW --- LV
    end
    RP --> RT
    TP --> CH --> RT
    RT -->|evidence| GW
    GW -->|Listing 6.1 JSON| VA
    VA --> RV
    RT --> ST
    VA --> ST
    EV[eval<br/>M1–M8 · M12 · M13 · M16 · M17] --> RT
    EV --> GW
    BL[pipeline.run_direct_baseline<br/>B2 whole-document] --> GW
```

| Module | Responsibility | Proposal item |
|---|---|---|
| `schemas.py` | Pydantic contracts; `AssessmentDraft` = Listing 6.1 | §6.2 |
| `rubric_parser.py` | Ingest block / table / numbered / PDF rubrics, infer granularity, reject invalid levels | FR1–FR3, S7 |
| `text_parser.py`, `chunker.py` | TXT/PDF → pages, line structure kept; headings detected (`#`, `2.1 Title`, ALL CAPS) so PDF text gets real section names; paragraphs grouped to ~160 words, over-long PDF paragraphs split on sentences; evidence units with `p.X · section · ¶n` locator | FR4–FR5 |
| `retriever.py` | BM25 baseline; query = criterion name ×2 + top descriptors; returns top-K or `[]` | FR6, §6.4 |
| `gateway.py` | Only place a model is called. Fixture for tests; OpenAI-compatible client (hosted / Azure via env, local Ollama via `ollama:<model>`); strict JSON parse; one JSON-repair retry; `revise()` for one validator-driven corrective round; fail-closed | FR9–FR10, C5, NFR6 |
| `validator.py` | Unknown IDs, range, granularity, uncited positive claims, malformed output → warning + downgrade | FR11, S6 |
| `review.py` | Accept / edit / reject, marker values override AI values, export JSON+CSV, blocked while pending; session summary (duration, overrides, interventions) for M10/M11 | FR12, FR13, FR15, NFR5 |
| `store.py` | Append-only JSONL run log; `replay_entry` re-executes from the log with the gateway that produced the entry | FR16, NFR7, M12 |
| `pipeline.py` | Agent path (retrieve → assess → validate → optional revise → validate) and B2 baseline | §6.1, §8.2 |
| `eval.py` | Metrics, per-scenario table, revision statistics, Markdown report | §8.3–8.5 |
| `app/streamlit_app.py`, `app/review.py`, `app/evaluation.py`, `app/run_log.py` | Marker UI (no prompt writing, B2 side-by-side), Evaluation dashboard, Run-log viewer + replay | FR7, NFR4 |

## 3. Data flow for one criterion

1. `retriever.retrieve(criterion, k)` → `[EvidenceUnit]` (may be empty → explicit "no relevant evidence").
2. `gateway.assess(criterion, evidence)` → `AssessmentDraft`. The prompt (`prompts/assessment_v4.md`) is versioned and its name is written to the run log. If the reply is not valid JSON for Listing 6.1 the gateway asks once more with the parse error attached.
3. `validator.validate_assessment(draft, criterion, evidence)`:
   * cited IDs ⊆ retrieved IDs, score ∈ [0, max] on the granularity grid,
   * positive sentences recognised by the heuristic carry `[E-00N]` (variants such as `[E-001, E-002]` or `[E-001: "quote"]` are recognised; the IDs are still checked),
   * gateway flags `invalid_model_output` / `provider_error` become warnings.
   Any critical warning → `insufficient`, `provisional_score = null`, `validation_failed` flag.
4. **One corrective round.** If the record was rejected, the pipeline calls `gateway.revise(criterion, evidence, draft, warnings)`: the model sees its own answer and the validator's findings and answers again. The revision is validated exactly like the first answer and carries the flag `revised_once`; attempt counts and first validation warnings are logged (`attempts`, `first_attempt_warnings`); raw responses are not retained. The schema retry is separate and permits up to three HTTP requests per criterion overall. The fixture cannot revise, so this path only runs with a live model. There is no second round: if the model breaks a rule twice the record stays `insufficient` with no score.
5. `RunLogEntry` written (model id, prompt version, K, method, query, evidence IDs, outputs, attempts, latency).
6. Marker sees explanation, cited and uncited evidence with adjacent context, decides; export refused until all criteria decided.

## 4. Failure handling (Lab 6 "check the result")

| Failure | Where caught | What the marker sees |
|---|---|---|
| Model returns prose / bad JSON | `gateway.parse_model_json` | `insufficient`, warning `invalid_model_output` |
| HTTP error, timeout, no key | `OpenAICompatibleGateway.assess` | `insufficient`, warning `provider_error` |
| Model cites `E-999` | validator | warning `unknown_evidence_ids`, no score |
| Score 6/4 | validator | warning `score_out_of_range`, no score |
| Claim without citation | validator | warning `uncited_claim:n`, no score — unless the corrective round fixes it, then `revised_once` |
| Model breaks a rule twice | pipeline | first attempt's warnings in the log, final record `insufficient`, no score |
| PDF has no text layer | `text_parser` | `SubmissionParseError` surfaced in UI (OCR is out of scope, C4) |
| Document longer than the model context (B2 only) | `render_direct_prompt` | text truncated at 48k characters with a marker; the default BM25 path is bounded; B3 sends all indexed units and may exceed model context on larger inputs |

## 5. What is deliberately not here

* No LMS or student-record integration (C2).
* No OCR / image / handwriting (C4).
* No autonomous grade submission (C1) — there is no code path that writes a grade anywhere.
* No embedding re-ranker yet; it is added only if Recall@K on the labelled set improves (§6.4, de-scoping order §10.3).
* No MCP server. Week 7 introduces MCP as a way to reach an external system the model cannot see. This prototype's tools (parser, BM25, validator, review store) are ordinary in-process code. A gradebook or LMS write would also break Constraint C1. The Week 8 LangChain notebook is a separate lab exercise, not this product.

## 6. Week 7 alignment (RAG and context)

The agent path is closed-corpus retrieval over one submission, not open-domain Wikipedia QA. BM25 (Robertson and Zaragoza, 2009; the lecture's classical IR baseline) selects at most K units before the model is called. That is the context-engineering choice: the model does not receive the whole document, because a longer window does not mean the relevant span is used (Liu et al., "Lost in the Middle", ACL 2024, Week 7).

The historical K=10 control did not change macro-F1 (0.554). It does not establish a general causal retrieval claim. Subsequent changes to validation, human review and evaluation mean the old live reports no longer describe every current behaviour. B3 now passes all evidence in document order through the same criterion prompt, validation and revision budget. See `EVALUATION_PROTOCOL.md` and `validation/README.md` for current checks and limitations.

## 7. Current integrity and evaluation boundaries

- `StrictModel` rejects NaN/Infinity; the validator also defends against mutated non-finite scores, wrong criterion IDs and invalid rubric scores.
- Explicit cited quotes are checked in both explanations and feedback. Advice is distinguished from factual feedback heuristically. These checks do not establish semantic entailment.
- A rejected/absent AI score cannot be accepted; the marker must edit explicitly or reject. Edits obey the rubric range/grid. Invalid UI edits clear stale confirmation; exports recheck every criterion.
- Replay distinguishes `bm25` and `full-context-v1` and refuses unknown retrieval methods.
- Evaluator schema 2 reports denominators, score coverage, conditional normalised MAE and within-criterion QWK, plus hashes and individual outputs. Historic pooled QWK is a different metric.
