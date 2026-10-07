# Reading the frozen development-corpus campaign — 7 October 2026

Artifacts: `docs/evaluation_dev_frozen/` (`A.json`/`A.md`, `B3.json`/`B3.md`,
`comparison.json`, `manifest.json`, per-checkpoint records and the raw local
request/response capture). This file is the human reading of them.

**What this is.** All three systems, same model, same inputs, same labels, run
under the frozen configuration (`docs/FREEZE.md`). 43 criterion pairs, 9
submissions, 2 rubrics, corrected labels `labels_v2.json`, 3 repeats for A and
B3, 1 for B2. Local `qwen2.5:7b-instruct`, temperature 0.

**What this is not.** The final test. These labels were reviewed by the project
itself, not by independent annotators, and the dev split is the split the
prompt was selected on (`docs/tuning/README.md`). It supersedes the 13
September numbers as the current description of the build; it does not settle
the project's claims. `dataset/final_test/` does that, after independent
annotation.

## Headline table

| | A (BM25 k=5) | B2 (one-shot, whole document) | B3 (full context, same prompt) |
|---|---:|---:|---:|
| Sufficiency macro-F1 | 0.439 | 0.434 | 0.401 |
| Sufficiency accuracy | **0.767** | 0.721 | 0.744 |
| Conditional normalised MAE | 0.222 | **0.050** | 0.318 |
| Conditional MAE (marks) | 0.847 | **0.167** | 1.227 |
| Numeric score coverage | **0.947** (36/38) | 0.789 (30/38) | 0.868 (33/38) |
| False-insufficient pairs | **2** | 8 | 5 |
| Uncited positive claim rate | **0.000** | 1.000 | **0.000** |
| Citation ids valid | 1.000 | n/a, not asked to cite | 1.000 |
| Precision@5 of supplied evidence | 0.739 | n/a | 0.165 |
| Repeatability over 3 runs | **1.000** | not measured (1 run) | **1.000** |
| Median latency per submission | 33.1 s | 11.0 s | 41.0 s |

Paired, on the pairs where both systems emitted a number:

| Comparison | Jointly scored | Left normalised MAE | Right normalised MAE |
|---|---:|---:|---:|
| A vs B2 | 29 | A 0.259 | **B2 0.034** |
| A vs B3 | 32 | **A 0.219** | B3 0.313 |

## Three things this campaign establishes

**1. Restricting evidence helps. The retrieval design earns its place.**
A and B3 differ in exactly one thing: A sees the BM25 top five units, B3 sees
every unit. Same prompt, same citation rules, same validator, same correction
budget. A is better on score error (0.219 vs 0.313 on the 32 jointly scored
pairs), on false-insufficient decisions (2 vs 5) and on accuracy. This is the
citation-compatible ablation and it is the one that tests the architecture.

The sharpest case is the keyword decoy, `s4_decoy_eval` C3, where the document
contains the sentence *"We mention evaluation only as a keyword without
specifying metrics or a baseline. This sentence is a decoy..."*. Reference:
`insufficient`. A: `insufficient`, correct. B3: `sufficient`, score 2.0,
explaining that this "matches the descriptor 'Metrics listed without a
procedure'". Both cited the same unit, `E-004`. The extra context did not give
B3 a different passage; it gave it the confidence to over-read the one it had.
Per-submission accuracy on that document is A 1.000 against B3 0.400.

**2. The one-shot baseline agrees better on scores and cannot be checked.**
B2's score error is far lower: 0.034 against A's 0.259 on their 29 jointly
scored pairs. That is a real result and it is reported as such. It is also
unauditable. Every one of B2's positive claims lacks an evidence pointer
(uncited rate 1.000 against A's 0.000), because B2 is not asked to cite — so
this is a property of its output format, not proof of hallucination. What it
does mean is that a marker cannot see which passage produced a B2 score.

B2 is also the most likely to abstain wrongly: 8 false-insufficient pairs
against A's 2, and the lowest coverage (30/38 against 36/38). On
`s7_partial_results` its accuracy is 0.400 against A's 0.800, and on `p2_gaps`
it emitted no scorable output at all.

The honest summary for the presentation: with a 7B local model, evidence-first
marking produces fully traceable judgements and more usable suggestions, while
the one-shot grader lands closer to our reference scores. Whether that gap
survives independent labels is what the final test decides.

**3. Two previously open targets now pass.**

- **M12 repeatability 1.000** over three runs at temperature 0, for both A and
  B3. Previously measured over two runs at 0.968, and unmeasurable in any
  single-run report.
- **M13 median latency 33.1 s** per submission against the 120 s NFR3 target.
  The comparable historical figure is the 126 s UI run on the serial build,
  which missed the target. Criterion calls now overlap. B3 costs 41.0 s for a
  worse result, so the full-context path is slower *and* less accurate here.

Every other automatic target passes: M1 1.000, M2 1.000, M3 Recall@5 1.000,
M5 citation validity 1.000, M7 1.000, M16 1.000, M17 1.000, and M6 relative
reduction against B2 of 1.000 against a 0.30 target.

## The one failing target, and why the split cannot settle it

**M4 sufficiency macro-F1 0.439 against a 0.750 target.** The cause is
structural and was stated before this run
(`dataset/LABELS_V2_CHANGES.md`, `docs/tuning/README.md`): the corrected dev
split holds **one** `partial` pair. macro-F1 is the unweighted mean of three
per-class F1 values, so a third of it rests on that single judgement. A
predicted `partial` five times and was right none of them, so F1 for `partial`
is 0.000 and macro-F1 cannot exceed 0.667 whatever the other classes do.

Per class for A, with the supports the mean rests on:

| Class | Precision | Recall | F1 | Gold support | Predicted |
|---|---:|---:|---:|---:|---:|
| sufficient | 0.912 | 0.838 | 0.873 | 37 | 34 |
| partial | 0.000 | 0.000 | 0.000 | **1** | 5 |
| insufficient | 0.500 | 0.400 | 0.444 | 5 | 4 |

Accuracy, 0.767, is the more readable summary of the same 43 decisions. M4 is
settled on `dataset/final_test/`, where `f02` and `f05` are written so that
`partial` has a real denominator.

## Failure analysis

**Retrieval is not the bottleneck.** M3 Recall@5 is 1.000: on every pair with
annotated relevant evidence, the top five contained it. `s2_dispersed` is the
case built to break retrieval — two relevant sentences on pages 1 and 7 with
four pages of deliberate filler between them — and A retrieved both (`E-001`
Opening, `E-007` Users) and cited both. It then judged `partial` 2.0 against a
reference of `sufficient` 4.0. The evidence was found; the descriptor
judgement differed.

**A's remaining errors are concentrated and one-directional.** Of 43 pairs, A
missed 10, and 6 of those are one step below the reference. Its worst document
is `s8_missing_method` at 0.200 accuracy.

**On that document the reference label is the doubtful party.** For
`s8_missing_method` C1 the document says only *"The scoped marking-workload gap
is unverifiable provisional scores."* The rubric's 4-mark descriptor requires a
problem "scoped with affected users and a testable gap" and the 2-mark
descriptor is "stated but not scoped". The reference says `sufficient` 4.0. A
said `partial` 2.0, B3 said `sufficient` 2.0 and B2 said `insufficient` — all
three systems, independently, declined to award 4. The same pattern appears on
C3.

That is a signal the label deserves re-examination, and it is **not** acted on
here. Changing a dev label after seeing model output is fitting the target to
the predictions, which is the error this project already corrected once. The
label stays; the observation is recorded; and it is another reason the
conclusions wait for independently annotated data.

**Validator behaviour.** A used its corrective round on 11.6% of calls and
finished with two records carrying `uncited_feedback_claim`, which a marker
sees as a warning on an otherwise usable record. B3 needed the round more often
(16.3%) and finished with six warnings. No run produced an out-of-range score,
an unknown evidence id or a non-finite value.

## Limits to state wherever these numbers appear

- 43 pairs, 9 synthetic submissions, one 7B model, one machine. Differences of
  a few points are not established as reliable.
- The dev split selected the prompt, so A's numbers here are not an unbiased
  estimate of A's performance.
- Labels are the project's own corrected judgements, not independent ground
  truth.
- MAE and QWK are conditional on an emitted score and must be read with
  coverage; the systems abstain on different pairs, which is why the paired
  table exists.
- B2 ran once, so its repeatability is unmeasured rather than poor.
- QWK is low for every system (A 0.081, B2 0.000, B3 0.011) because most pairs
  sit in one or two score levels on this corpus; it is reported for
  completeness and carries little information here.
- M9, M10, M11 and M14 are not measured at all. No marker has used the tool
  under observation.

## Reproduce

```sh
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_CONTEXT_LENGTH=16384 ollama serve
.venv/bin/python scripts/run_campaign.py --corpus dataset --labels labels_v2.json \
    --split dev --output docs/evaluation_dev_frozen
.venv/bin/python scripts/extract_traces.py --submission s4_decoy_eval --criterion C3
```

36 minutes on an M2 Pro. The runner checkpoints every unit and refuses to mix
sources; `docs/validation/freeze_guard_2026-10-07.md` records it aborting a
first attempt when the working tree changed mid-run.
