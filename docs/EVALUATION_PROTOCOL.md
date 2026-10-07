# Evaluation protocol — frozen definitions for the final project

Protocol version: **2026-10-04 / evaluator schema 2**. This addresses the proposal feedback about unspecified metrics and A2's Evaluation, evidence and critical analysis criterion (4 marks). Targets below are acceptance criteria, not achieved results. The final source package and report must identify the exact run artifacts used.

## Question and experimental systems

Question: does criterion-level retrieval plus citation validation provide useful, inspectable provisional marking while retaining adequate evidence coverage, scoring coverage and agreement with independent markers?

Use the same model deployment, temperature, rubric, submissions and labels for all systems. Keep prompt wording and any repairs fixed before the final test.

| System | Fixed implementation | What the comparison can test |
|---|---|---|
| A — proposed assistant | BM25, k=5; per-criterion `assessment_v4`; evidence IDs; deterministic validator; at most one corrective round; marker decision required | The complete implemented workflow |
| B2 — direct grading | Whole document + whole rubric in one call; `direct_grading_v1`; same gateway | Agreement and coverage against a simple model baseline; workflow and prompt both differ |
| B3 — full-context ablation | `--evidence-mode full_context`; every original evidence unit, with the same IDs, per-criterion prompt, validator and corrective round as A | The effect of limiting evidence through BM25; compare A and B3 at the same settings |
| Human reference | Two independent annotations, followed by recorded adjudication | Reference labels and annotation uncertainty; not a completed user study |

B3 is implemented. It is not a reproduction of Evidence-First Scoring, GradeAgentOps or RULERS. Cite and compare those works in Related Work; do not claim a quantitative win over a paper without a matched implementation and dataset. B2 is **not asked for evidence IDs**: a higher uncited-sentence rate is a property of that output format and is not evidence of hallucination. A versus B3 is the citation-compatible ablation.

No fine-tuning or embedding retriever is claimed. Changing model, k, prompts or validation rules creates a new experiment with a new manifest.

## Data, split and independence

The checked-in first-pass synthetic dataset currently contains **62 criterion–submission pairs, 13 submissions and 2 labelled rubrics**:

| Existing split | Submissions | Labelled pairs | Numeric gold scores |
|---|---:|---:|---:|
| dev | 9 | 43 | 38 |
| heldout | 4 | 19 | 16 |

These are synthetic fixtures, with known first-pass sufficiency inconsistencies documented in `dataset/LABELLING_GUIDE.md`. Their existing labels are not verified independent human ground truth. The 19-pair historical heldout split has already been evaluated; retain it as a regression split, not as a newly unseen final test. Never relabel it silently to improve a metric.

The final independent campaign will use **6 new synthetic submissions**, 3 under each of the two existing rubrics (**27 criterion pairs**: 3 × 5 engineering criteria + 3 × 4 proposal criteria). Include one ordinary, one dispersed/partially missing and one decoy/adversarial document per rubric. Generate or write the documents before annotation; keep whole submissions and any near-duplicate variants in the same split. A team member who is not tuning prompts holds these test inputs and labels until the code and prompts are frozen. This small test measures prototype behaviour, not generalisation to real university marking.

Before the campaign: freeze the existing development data, model settings, code and prompt hashes; record the six input hashes; set all six final-test submission IDs to `split="heldout"` in the separately versioned final-test corpus. No student personal data is required. The CLI currently uses the bundled dataset; a separate corpus can be evaluated through `evaluate_corpus(Path(...), ...)`. Do not overwrite `dataset/labels.json` with unreviewed labels.

## Annotation procedure — required, not yet completed

1. Two named team members independently read each rubric and full submission. Neither sees model outputs, first-pass labels or the other annotator's decisions. The existing `dataset/second_pass/to_label.csv` is a **blank template**, not completed evidence.
2. Each records relevant text spans, `sufficient` / `partial` / `insufficient`, the numeric rubric score or `null`, and a short rationale. Sufficiency means enough relevant evidence to assess the criterion, not high-quality work. Clearly documented weak work can have sufficient evidence and a low score.
3. Save both original annotation files unchanged. Report sufficiency Cohen's kappa, raw agreement and the three-class confusion matrix; report score MAE and QWK per rubric criterion for pairs where both humans gave numeric scores. Record the number of jointly scored pairs and abstentions. Constant-label QWK is undefined, not perfect agreement.
4. Discuss disagreements only after the independent files are saved. Create a third, adjudicated label file with the rationale and both annotator names. Hash all three files. Do not replace original labels or claim that model-generated annotations are independent human evaluation.
5. Run A, B2 and B3 on the adjudicated test labels once the system is frozen. Gold labels are read by the evaluator only; they must never enter gateway prompts. After inspecting final-test outcomes, any changes require a new experiment and cannot be reported as the original heldout run.

Named annotators, dates, completed annotation files and agreement values remain pending. Until they exist, all bundled-label model scores must be described as preliminary agreement with first-pass synthetic labels.

## Fixed metrics and targets

The experimental unit for M4 and scoring is a **rubric–submission–criterion pair**. Scores are computed on the first run; repeated runs are used only for M12. Repeats are not independent extra samples. The harness records denominators in JSON and Markdown. Empty denominators produce `null` / `n/a` and an unmeasured target, never a pass.

| Metric | Definition and denominator | Acceptance target |
|---|---|---|
| M1 rubric extraction | Number of labelled criterion IDs parsed / number of expected labelled criterion IDs | ≥ 0.95 |
| M2 locator completeness | Evidence units with positive page and nonempty section / all extracted units | 1.00; structural proxy |
| M3 Recall@5 | Macro mean of relevant units retrieved / all relevant units, over pairs with at least one relevant unit | ≥ 0.85 for A |
| M3 Precision@5 | Relevant units retrieved / returned units, macro averaged over the same nonempty-gold pairs | Report; no tuned cutoff |
| M4 sufficiency macro-F1 | Unweighted mean of F1 for sufficient, partial and insufficient; identical class list for A, B2 and B3; absent classes contribute zero | A ≥ 0.75 |
| M5 citation existence | Returned evidence IDs that exist in the allowed context / all returned evidence IDs | ≥ 0.95 |
| M5 support proxy | Returned evidence IDs matching a labelled phrase / all returned evidence IDs | Report; not human semantic support |
| M6 uncited positive claim rate | Positive sentences without recognised citation syntax / all detected positive sentences in non-insufficient explanations | A ≤ 0.05 |
| M6 relative reduction vs B2 | (B2 rate − A rate) / B2 rate, only when both defined and B2 > 0 | Historical proposal target ≥ 0.30; output-format diagnostic only |
| M7 score range validity | Outputs with a legal range/grid score, or insufficient with no score / all agent outputs | 1.00 |
| M8 score coverage | Emitted numeric scores / pairs with numeric gold scores; report scored count and abstained count | Report for every system; no success claim without it |
| M8 conditional MAE | Mean absolute mark error over scored pairs with numeric gold only | Report with coverage; not whole-dataset error |
| M8 conditional normalised MAE | Mean of absolute error / criterion maximum, over those same scored pairs | Primary cross-rubric score-error comparison; report |
| M8 conditional QWK | QWK computed separately per rubric/criterion; pair-weighted mean over defined groups | Report defined group and pair counts; never pool incompatible scales |
| M12 repeatability | Criteria with identical top-1 evidence ID and numeric score spread ≤ 10% of maximum across all repeats; all-null scores are stable, mixed null/numeric fails | ≥ 0.90, exactly 3 runs in final campaign |
| M13 median wall-clock latency | Median first-run submission latency, including parsing, retrieval, calls, validation and repairs | ≤ 120,000 ms; also report S5 separately |
| M16 export completeness | Export rows with every required field and an explicit simulated decision / all exported rows | 1.00; schema check, not usability evidence |
| M17 feedback citation validity | Nonempty feedback outputs whose cited IDs are in allowed context / nonempty feedback outputs | 1.00; ID validity, not semantic grounding |

M3 currently identifies relevant units through `must_contain` phrase matches. This can match negated or decoy text; it is a retrieval proxy and requires independent span annotation for a stronger claim. Pairs with no matched relevant unit are excluded from recall and reported separately; inspect them for annotation/chunking mismatches. B3 uses all units: its recall ceiling is a manipulation check, not evidence that retrieval improved.

The JSON retains `M6_unsupported_rate` and `unsupported_claims` as legacy field names for compatibility; **their meaning is uncited-positive-claim rate/count**. Regex citations do not establish truthful content. M17 can pass for text with no citation IDs because an empty set is a subset; the separate validator governs whether the output is acceptable. Do not interpret this target as a human grounding score.

For A versus B2, the harness additionally reports normalised MAE on their **intersection of jointly scored pairs**, with the intersection size. This controls differing abstention subsets for that comparison, but says nothing about excluded cases. Compare A/B3 likewise from their saved outputs. Never write “lower MAE means a better grader” while omitting abstentions or differing sample counts. QWK in schema 2 intentionally differs from historical reports that pooled score scales.

M9, M10, M11, M14 and the M15 audit require a real marker session. Report “not measured” unless an actual participant protocol, observations and sample counts are available. Cost/token measurements are not currently collected; do not estimate them as measured costs. Latency depends on the recorded machine/runtime and model service load; fixture timings are not model performance.

## Reproducible procedure and artifacts

The gateway must not see gold labels. Use temperature 0, k=5, at most one corrective round and three repeats. Preserve the pipeline's default concurrent criterion execution for A/B3 and record hardware and server concurrency when using a local model. Evaluate all systems on identical corpus hashes. The reports record UTC timestamp, gateway class, nonsecret model settings, Python/package/platform information, git commit/dirty flag, and SHA-256 manifests for source code, prompt files and input/label files.

Offline regression, safe to run without credentials:

```sh
.venv/bin/python -m rubric_agent.cli --gateway fixture eval --split all --repeats 3 --k 5 --json docs/evaluation_fixture_v2.json --report docs/EVALUATION_fixture_v2.md
.venv/bin/python -m rubric_agent.cli --gateway fixture eval --split all --repeats 3 --k 5 --evidence-mode full_context --no-baseline --json docs/evaluation_B3_fixture_v2.json --report docs/EVALUATION_B3_fixture_v2.md
.venv/bin/python -m pytest tests/test_evaluation_integrity.py
```

An actual model campaign uses a configured `--gateway live` or an available local Ollama gateway, with distinct filenames and captured logs. Run this only once the model and test corpus are fixed; fixture results are never relabelled as live. These commands are the form of the bundled heldout regression, not a claim that the fresh six-document test has been collected:

```sh
.venv/bin/python -m rubric_agent.cli --gateway ollama:qwen2.5:7b-instruct eval --split heldout --repeats 3 --k 5 --json data/final_A_B2.json --report docs/EVALUATION_final_A_B2.md --log data/final_A_calls.jsonl
.venv/bin/python -m rubric_agent.cli --gateway ollama:qwen2.5:7b-instruct eval --split heldout --repeats 3 --k 5 --evidence-mode full_context --no-baseline --json data/final_B3.json --report docs/EVALUATION_final_B3.md --log data/final_B3_calls.jsonl
```

The JSON's `run_outputs` saves every repeat's validated assessment and retrieved IDs, and the direct B2 structured drafts, keyed by rubric and submission. Reconstruct source evidence from the hashed inputs; use these actual records for paired comparisons and failure analysis. Optional JSONL logs cover first-run agent calls only; they are not the full experiment. Provider raw responses and token usage are not collected. Check artifacts for credentials or personal data before packaging them.

## Required final analysis

Report A/B2/B3 macro-F1, conditional normalised MAE, score coverage and counts in the same table. Include false-insufficient decisions, validator abstentions and any score disagreement. Select at least one ordinary, one dispersed/missing and one decoy failure/success trace; show the actual retrieved span, output, validation/revision and human reference.

Report per-submission results because criteria from one document are correlated. If confidence intervals are added, bootstrap **whole submissions**, not 27 criterion rows as independent samples, and disclose the small six-document test. Do not claim statistical significance from the existing preliminary corpus. Distinguish measured trade-offs from hypotheses about why they occurred, and retain failed targets in the report.

The source and final report should present the actual implemented system, its limitations and independently supported results. Completing the protocol is separate from meeting its targets.
