# Freeze record — 7 October 2026

Tag: **`v1.0.0-frozen`**

This is the configuration the final-test campaign must run under. It was fixed
*before* the independent annotation of `dataset/final_test/` began, which is
what makes those labels a test rather than a tuning target
(`docs/EVALUATION_PROTOCOL.md`).

## What is frozen

| Item | Value |
|---|---|
| Model | local `qwen2.5:7b-instruct` via Ollama, digest `845dbda0ea48` |
| Decoding | temperature 0, max 700 output tokens |
| Prompt (system A and B3) | `prompts/assessment_v4.md` |
| Prompt (baseline B2) | `prompts/direct_grading_v1.md` |
| Retrieval | BM25, k=5, `k1=1.5`, `b=0.75` |
| Evidence modes | A `bm25`; B3 `full_context`, all other settings identical |
| JSON re-ask budget | 1 |
| Validator corrective rounds | 1 |
| Repeats | 3 for A and B3, 1 for B2 |
| Server | `127.0.0.1:11434`, `OLLAMA_CONTEXT_LENGTH=16384`, one worker |

## Manifest digests at the freeze

| Scope | SHA-256 |
|---|---|
| `src/rubric_agent/**/*.py` | `534309638b31f4bc59cb8845b3acc1e2699471bd924a62de52fde5186ea301ba` |
| `prompts/*` | `d80612d16c4bec4584d7baafa9721e256caee3534df7e65a8ae40ba8d9ed4706` |
| `dataset/final_test` inputs (excluding the annotation workspace) | `14f72e5c491f0729ca1f539feae20e13bae26a8a91332d1d8779c507bb49eaa3` |
| `dataset/` development corpus and both label files | `ac15a11f9bce6bc31b8c10706e863f139c12e4cc233d0b4c50b215e38b0ef3cd` |

Per-file digests of the frozen final-test inputs:

| File | SHA-256 (first 16) |
|---|---|
| `dataset/final_test/corpus.json` | `4d2eb109a806aa7e` |
| `dataset/final_test/rubrics/engineering_report.md` | `bea09daf1b9ead77` |
| `dataset/final_test/rubrics/proposal_rubric.md` | `2e33e02538287f05` |
| `dataset/final_test/submissions/f01.txt` | `9a9ba0ffd82e3829` |
| `dataset/final_test/submissions/f02.txt` | `e0ca99612ee28122` |
| `dataset/final_test/submissions/f03.txt` | `ef1a95dbc4268d6b` |
| `dataset/final_test/submissions/f04.txt` | `dba01ebff0a793d5` |
| `dataset/final_test/submissions/f05.txt` | `7e361db7b98cb5c8` |
| `dataset/final_test/submissions/f06.txt` | `eaf8b915fbcd79bf` |

`scripts/run_campaign.py` recomputes an equivalent manifest at startup and
around every model call, and aborts if anything moved mid-run. The digests above
let a reader confirm a committed report came from this configuration.

## Prompt selection, and why it is not a leak

`prompts/assessment_v4.md` was chosen in the window recorded in
`docs/tuning/README.md`: four variants, dev split only (43 pairs), against the
corrected labels `dataset/labels_v2.json`. The heldout split and
`dataset/final_test/` were never read during that window. Earlier prompts are
kept in `prompts/` so the comparison can be re-run.

## What is still open after the freeze

These do not reopen the configuration:

- the independent annotation of the 27 final-test pairs
  (`dataset/final_test/annotation/REGISTER.md`);
- the marker sessions (`docs/MARKER_SESSIONS.md`);
- report writing, screenshots and packaging.

## What would break the freeze

Changing the model, decoding settings, any prompt, `k`, the retriever, the
validator rules, the correction budget, or any final-test input or label. Any
of those creates a **new experiment** with a new manifest. After final-test
results have been seen, such a change cannot be reported as this run.

## Historical reports that predate this freeze

Keep their dates and prompt versions; do not restate them as current.

| Report | Prompt | Note |
|---|---|---|
| `docs/EVALUATION_live_qwen7b.md` | `assessment_v2` | 13 September, 2 repeats, pooled QWK since superseded |
| `docs/EVALUATION.md`, `EVALUATION_heldout.md` | `assessment_v2` | fixture only |
| `docs/validation/local_smoke_2026-10-04*.json` | `assessment_v2` | smoke runs, not a campaign |
| `docs/tuning/dev_v*prompt_v2labels.*` | `v2`/`v3`/`v4`/`v5` | development selection, not results |
