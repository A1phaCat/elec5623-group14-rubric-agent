# Defect → mitigation → re-test

Week 9 lab §1 asks for the loop Define → Test → Break → Observe → Mitigate →
Re-test, and its final discussion question asks which normal cases should be
re-checked after a mitigation. This is that record for the defects actually
found in this project.

Every number below comes from an artifact already in the repository. Nothing
here was re-run to produce this table, and no figure is estimated. The last
column is the part that is easy to skip and matters most: a mitigation that
fixes the broken case by breaking a working one is not an improvement.

## 1. The feedback check rejected imperative advice

| | |
|---|---|
| **Observed** | The first local-model smoke run rejected a record because the sentence *"Specify the metrics, baselines, scenarios, and labelled data for your evaluation plan"* was classified as an uncited factual claim. It is advice to the student, not an assertion about the submission. |
| **Evidence** | `validation/local_smoke_2026-10-04.json`: case `synthetic_decoy_B3`, 4 of 5 records accepted, `uncited_feedback_claim` ×1 |
| **Mitigated** | `validator.py` now exempts sentences opening with an imperative advice verb (`add`, `include`, `specify`, …) from the feedback claim check. |
| **Re-test, same input** | `validation/local_smoke_2026-10-04_final.json`: the same case, 5 of 5 accepted, `uncited_feedback_claim` ×0 |
| **Normal cases re-checked** | `synthetic_decoy` stayed 5/5 accepted. Crucially the real-PDF case **still** rejects its genuine `uncited_claim` ×1, so the exemption narrowed the check rather than disabling it. A regression test asserts that appending an uncited *factual* sentence to feedback still causes rejection. |

The second run also finished faster (own-proposal 100.6 s → 61.9 s), but that
is a warm cache and scheduling, not the mitigation. Each condition ran once, so
no speed-up is claimed.

## 2. An invalid AI suggestion could be accepted

| | |
|---|---|
| **Observed** | A review on 4 October found two output-boundary holes: a suggestion that failed validation could still be accepted by the marker, and an invalid edit in the UI left the previous confirmation in place, so an export could carry a decision the marker had implicitly withdrawn. |
| **Evidence** | Recorded in `CHANGELOG.md` for 4 October; the holes were found by inspection, not by a failing test, which is why regression tests came with the fix. |
| **Mitigated** | Acceptance now requires a valid, present score and a non-`insufficient` record; an invalid UI edit resets the decision to pending; export revalidates every decision instead of trusting the stored state. |
| **Re-test** | `tests/test_review_integrity.py`, including a headless Streamlit interaction. Both holes now fail closed. |
| **Normal cases re-checked** | The full suite, which includes accept, edit-with-a-valid-score and reject paths and the NFR5 export gate. A valid override still stores the marker's value **and** retains the AI's original suggestion, which is the behaviour FR13 requires and the one most at risk from a stricter gate. |

## 3. A parser failure made a baseline look perfect

| | |
|---|---|
| **Observed** | The first live B2 baseline returned one criterion object instead of five. Every record was rejected, so B2's uncited-claim rate read 0.00 — from a denominator of zero. A parsing failure was presenting as the best possible result. |
| **Evidence** | `EVALUATION_NOTES.md` §5 |
| **Mitigated** | `_direct_items` accepts the output shapes one-shot graders actually return, with one re-ask. Separately, every rate in the harness now returns `null` on an empty denominator instead of a number, and the reports print denominators beside every rate. |
| **Re-test** | The frozen campaign reports B2 with real denominators: 30 of 38 numeric-gold pairs scored, uncited positive claim rate 1.000 over 60 detected claims. |
| **Normal cases re-checked** | A unit test asserts an empty accumulator yields `null` rather than 0.0 for every rate, so the class of error cannot recur silently on any metric. |

## 4. A prompt sentence destroyed usable records

| | |
|---|---|
| **Observed** | `assessment_v3` raised sufficiency accuracy from 0.581 to 0.837, the best of the four variants, but told the model a `partial` record *may* leave the score null. The validator treats a non-`insufficient` record with no score as critical and fail-closes it, so five records were discarded. The same prompt also stopped producing draft feedback, leaving FR14 unexercised and M17 unmeasurable. |
| **Evidence** | `tuning/dev_v3prompt_v2labels.json`: final warnings `{"missing_score": 5, ...}`, feedback outputs 0, M17 `null`, 34 of 38 scored |
| **Mitigated** | `assessment_v4` states the contract the validator enforces — `sufficient` or `partial` must carry a number, `insufficient` must be null, and if no descriptor can be named the answer is `insufficient` — and requires feedback for any scored record. |
| **Re-test, same split and labels** | `tuning/dev_v4prompt_v2labels.json`: `missing_score` ×0, feedback outputs 40, M17 1.000, 36 of 38 scored. |
| **Normal cases re-checked** | Accuracy fell from v3's 0.837 to 0.767, and this is reported rather than hidden: making a `partial` score mandatory also made `partial` usable again and the model spent it on four `sufficient` pairs. The selected prompt is therefore **not** the one with the best headline accuracy. Validator warnings returned to the previous build's level (2, both `uncited_feedback_claim`). |

## 5. A mitigation that was rejected for breaking a working case

| | |
|---|---|
| **Observed** | `assessment_v5` tightened the `partial` bar to reduce the one-step-down bias further, and succeeded: 3 such errors, the fewest of any variant. |
| **Evidence** | `tuning/dev_v5prompt_v2labels.json` |
| **Why it was rejected** | It pushed **four of the five genuinely absent criteria** to `sufficient`, collapsing F1 for `insufficient` from 0.444 to 0.222. Crediting a criterion that is not in the document is a worse failure than under-scoring one that is. |
| **Outcome** | Discarded; `assessment_v4` retained. The attempt is kept in `prompts/` and in the tuning record because a rejected mitigation is part of the evidence. |

This row exists because it is the lab's final discussion question answered in
the negative: the metric the change targeted improved, and the change was still
wrong.

## 6. The test suite passed only when invoked one particular way

| | |
|---|---|
| **Observed** | The first push to GitHub failed CI on both Python versions. Five test modules that import the helper scripts raised `ModuleNotFoundError: No module named 'scripts'`. |
| **Evidence** | GitHub Actions run 37563799595 |
| **Observed cause** | `python -m pytest` puts the working directory on `sys.path`; a bare `pytest` does not. Local runs used the former, CI and the README use the latter, so the suite's result depended on the caller. |
| **Mitigated** | `pythonpath = ["."]` declared in `pyproject.toml`, which fixes every caller rather than changing how CI invokes pytest. No test was weakened. |
| **Re-test** | Both invocations collect and pass the same 128 tests locally; CI green on 3.11 and 3.12 (run 37564255365). |
| **Normal cases re-checked** | The whole suite, since the change affects collection rather than any single test. |

Worth recording because the broken case was *the documented instructions*: a
teammate following the README would have hit this, and the reproduction task
assigned in `TEAM_DELIVERY.md` exists to find exactly this class of defect.

## 7. A defect found before it cost anyone their work

| | |
|---|---|
| **Observed** | `adjudicate_annotations.py` read the annotator sheet as plain UTF-8 and indexed `row["pair"]`. Excel's "CSV UTF-8" prepends a byte-order mark, which makes the first column name `\ufeffpair`, so the lookup raises `KeyError` — at adjudication, after 1.5 hours of annotation was already done. |
| **Evidence** | Reproduced directly: under `utf-8` the field names begin `['\ufeffpair', 'rubric_id', …]` and `row["pair"]` raises; under `utf-8-sig` they begin `['pair', …]`. |
| **Mitigated** | Sheets are read with `utf-8-sig`; a non-UTF-8 file is told to re-save as "CSV UTF-8"; a renamed or missing column is named in the error. |
| **Re-test** | Four tests: a BOM sheet parses to 27 pairs, a latin-1 sheet raises the re-save message, a renamed header names the missing column, a header-only file is rejected. |
| **Normal cases re-checked** | The existing annotation suite still passes, including the blank-sheet state and every validation rule (bad label, off-grid score, score on an `insufficient` row). The blank-sheet assertion was also relaxed to *blank or validly complete*, because as written it would have failed CI the moment a teammate did the work. |

This is the only row where the defect was found by reading the code against a
known user behaviour rather than by a failure. Everything else here was found
by running something.

## What this record shows about the process

Two of the seven defects were produced by a change intended as an improvement
(rows 4 and 5), and one by the test harness rather than the product (row 6).
That is the argument for keeping the before/after artifacts and the rejected
attempts: without `local_smoke_2026-10-04.json` beside `..._final.json`, and
without the v3 and v5 runs beside v4, three of these rows would be unverifiable
assertions.
