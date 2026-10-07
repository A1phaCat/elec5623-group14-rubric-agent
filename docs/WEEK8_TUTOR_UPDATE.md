# Week 8 tutor update — Group 14

For the Lab 7 Part A progress discussion (23 Sep 2026). Not a polished presentation.
Approved direction is unchanged: Track A, AI-Assisted Rubric Marking Agent, tutor Linghan Huang, approval 6 Sep 2026.

## 1. Problem and value

Markers of long reports still have to find the passage that matches each rubric criterion. A chatbot can emit a score, but the marker cannot see which span it used. The prototype retrieves criterion-specific evidence first, asks a model only about those spans, rejects uncited claims, and leaves the final score with the marker.

## 2. What works now

End to end, offline and with a local model:

- Rubric in (block, table, numbered list, or PDF) and a TXT/PDF submission, with page and section locators.
- BM25 top-5 evidence per criterion, or an explicit empty result.
- Local Qwen2.5-7B-Instruct via Ollama. One validator round can send a broken answer back once.
- Marker accept / edit / reject. Export stays blocked until every criterion is decided. AI score is kept beside the marker's value.
- 62 labelled synthetic pairs plus one real case: our own proposal PDF against the official proposal rubric (cover with names removed).

Show this, not a feature list: `streamlit run app/streamlit_app.py`, first example, then `s4_decoy_eval`.

## 3. Architecture

```text
rubric + submission → parse → chunk (E-001…) → BM25 top-K
    → model sees one criterion + those units only
    → validator (range, citations, claims) → at most one revision
    → marker review → JSON/CSV + run log
```

The model is swappable (fixture for tests, Ollama locally, Azure only if `RMA_*` is set). There is no MCP server: the tools are in-process, and nothing writes a grade to an external system. Detail: `docs/ARCHITECTURE.md`.

## 4. Main blocker

On the 13 Sep local run the agent cites every positive claim (unsupported-claim rate 0.00) but agrees with our labels less than the one-shot baseline (quadratic weighted kappa 0.48 vs 0.87). A K=10 control showed this is not missing retrieval. The labels were written by one person and treat "sufficient evidence" as if it meant "high quality". Until a second person labels sufficiency and score separately, we will not claim the agent matches human scores.

The 16-page real case also took about 126 seconds in the UI, just over the 120 second target, because the six criteria run one after another.

## 5. Evaluation already in hand

| Comparison | What it shows | Source |
|---|---|---|
| Agent vs direct whole-document grading (B2), same 7B model | B2 agrees more and has 45/45 claims with no evidence pointer. The agent has none uncited. | `docs/EVALUATION_live_qwen7b.md` |
| K=5 vs K=10 | Agreement does not rise when the model sees every unit. | `docs/EVALUATION_NOTES.md` §4 |
| Fixture gateway | Tests the harness only. It is not a model result. | `docs/EVALUATION.md` |

Not collected, and not invented here: a second annotator, inter-annotator agreement, or timed marker sessions.

## 6. Next engineering action

1. Second labelling pass on the 62 pairs, sufficiency and score labelled apart, using `dataset/LABELLING_GUIDE.md`.
2. Two or three marker sessions on the UI for time and override rate. The export already records duration and overrides.
3. Turn `docs/FINAL_REPORT_DRAFT.md` into the Week 13 report only after those numbers exist. Each member writes their own contribution row.
