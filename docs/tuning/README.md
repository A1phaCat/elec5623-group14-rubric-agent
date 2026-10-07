# Dev-split tuning window — 7 October 2026

Closed after four attempts. **Selected prompt: `assessment_v4`.**

Everything here ran on the **dev split only** (43 pairs, 9 submissions) against
the corrected labels `dataset/labels_v2.json`. The heldout split and
`dataset/final_test/` were not read. Model: local `qwen2.5:7b-instruct` via
Ollama, temperature 0, max 700 output tokens, BM25 k=5, one repeat,
`--no-baseline`. One repeat is enough to compare prompts and is **not** a
repeatability measurement.

Artifacts per attempt: `dev_v{N}prompt_v2labels.json` and `.md`.

## Why the labels were corrected first

`dataset/LABELS_V2_CHANGES.md`. The first-pass labels assigned sufficiency by
quality band, so tuning against them would have optimised toward that
confusion. The corrected labels are the target throughout this window.

## Results

| Attempt | macro-F1 | accuracy | F1 sufficient | F1 partial | F1 insufficient | one-step-down errors | score coverage | scored | feedback outputs | final validator warnings | M17 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `assessment_v2` (previous build) | 0.394 | 0.581 | 0.712 | 0.000 | 0.471 | 16 | 0.789 | 30/38 | 7 | 2 | 1.00 |
| `assessment_v3` | **0.468** | **0.837** | 0.904 | 0.000 | **0.500** | 4 | 0.895 | 34/38 | **0** | 6 | **unmeasured** |
| **`assessment_v4` (selected)** | 0.439 | 0.767 | 0.873 | 0.000 | 0.444 | 6 | **0.947** | **36/38** | 40 | **2** | 1.00 |
| `assessment_v5` | 0.372 | 0.814 | 0.895 | 0.000 | **0.222** | **3** | 0.921 | 35/38 | 41 | 4 | 1.00 |

"One-step-down errors" counts `sufficient`→`partial`, `sufficient`→`insufficient`
and `partial`→`insufficient`, the bias identified in `docs/EVALUATION_NOTES.md` §2.

Confusion matrices (gold→predicted) are in each JSON under
`agent.sufficiency_confusion`.

## What each attempt changed, and what it taught

**v3 — separate the two questions.** `assessment_v2` rule 2 illustrated `partial`
with *quality* examples ("a plan with no metrics, a method with no
justification"). That is weak work, not incomplete evidence: the same
conflation the labels had. v3 split sufficiency from score, ordered the two
decisions, and carried the guide's worked example plus a counter-example.

This worked on the target problem. One-step-down errors fell from 16 to 4 and
accuracy rose from 0.581 to 0.837. It also introduced two regressions:

- v3 rule 5 said a `partial` record "may" carry a score and could be left null.
  The validator treats a non-`insufficient` record with no score as critical
  (`missing_score`) and fail-closes it. Five records were discarded this way, so
  a prompt sentence was destroying usable output.
- Feedback output fell to zero, leaving FR14 unexercised and M17 unmeasured.

**v4 — match the validator contract and restore feedback.** Rule 5 now states
what the validator enforces: `sufficient` or `partial` must carry a number,
`insufficient` must be null, and if no descriptor can be named the answer is
`insufficient`. `draft_feedback` became required for non-`insufficient` records,
phrased as actionable advice so it passes the feedback claim check.

Both regressions cleared: `missing_score` disappeared, feedback outputs went to
40, M17 returned to 1.00, and score coverage became the best of the four at
0.947 (36 of 38 numeric-gold pairs). Accuracy fell from v3's 0.837 to 0.767
because making a `partial` score mandatory also made `partial` usable again,
and the model spent it on four `sufficient` pairs.

**v5 — tighten the `partial` bar. Rejected.** v5 restricted `partial` to
evidence that points at content outside the evidence set, and called
`sufficient` "the normal answer". One-step-down errors did reach their lowest
value (3), but the model then labelled **four of the five genuinely absent
criteria `sufficient`**, collapsing F1 for `insufficient` from 0.444 to 0.222.
Crediting a criterion that is not in the document is a worse failure than
under-scoring one that is, so v5 was discarded. The lesson recorded for the
report: pressure toward `sufficient` does not stop at the quality confusion, it
also erodes the absence check.

## Why `assessment_v4` was selected

Not for macro-F1, which v3 wins. v4 is selected because it is the only attempt
that improves the measured bias **without** giving something else up:

- sufficiency accuracy 0.767 against the previous build's 0.581;
- the highest score coverage, 36 of 38, so the marker is left with the most
  usable suggestions;
- FR14 exercised and M17 measurable, which v3 lost;
- validator warnings back to the previous build's level (2, both
  `uncited_feedback_claim`), with no self-inflicted fail-closures;
- `insufficient` F1 held at 0.444, close to v2's 0.471, so the absence check
  that v5 broke is intact.

M5 citation existence stayed 1.000 and M6 uncited positive claim rate stayed
0.000 in every attempt. The traceability properties are not what moved.

## The M4 target cannot be settled on this split

All four attempts fail M4 ≥ 0.75, and the reason is structural rather than a
prompt deficiency. Corrected dev contains **one** `partial` pair
(`s7_partial_results` C5). macro-F1 is the unweighted mean of three per-class
F1 values, so that single pair carries one third of the metric. Every attempt
labelled it `sufficient`, so F1 for `partial` was 0.000 in all four runs, which
caps macro-F1 at 0.667 — below the target — no matter how well the other two
classes do.

Reporting dev macro-F1 as the headline would therefore be misleading in both
directions. The window was judged on accuracy, the confusion matrix, score
coverage, requirement coverage and validator warnings, each with its
denominator, and it was stopped once the remaining movement was a trade rather
than a gain.

M4 is settled on `dataset/final_test/`, which reserves one
dispersed/partially-missing document per rubric (`f02`, `f05`) so the `partial`
class has a real denominator. That corpus is annotated independently after the
freeze and is not read here.

## Scope and honesty limits

- Four prompt variants on 43 pairs with one repeat. Differences of a few points
  between v3, v4 and v5 are not established as reliable.
- The comparison is against labels corrected by the project's own review, not
  independent human ground truth.
- Selecting a prompt on dev is development, not evaluation. No number in this
  file is a result about the final system; the frozen campaign supplies those.
- `assessment_v2`, `v3` and `v5` are kept in `prompts/` so this table can be
  re-run.

## Reproduce

```sh
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_CONTEXT_LENGTH=16384 ollama serve   # separate terminal
for v in v2 v3 v4 v5; do
  RMA_PROMPT_VERSION=assessment_$v .venv/bin/python -m rubric_agent.cli \
    --gateway ollama:qwen2.5:7b-instruct eval --split dev --repeats 1 \
    --labels labels_v2.json --no-baseline \
    --json docs/tuning/dev_${v}prompt_v2labels.json \
    --report docs/tuning/dev_${v}prompt_v2labels.md
done
```
