# Validation evidence — 4 October 2026

These are executed checks on the current working tree. They do not replace
independent human annotation, a full model-quality benchmark or a user study.

> **Superseded in part.** This file is the 4 October record and is kept at its
> own date. Current evidence lives in:
>
> - `../EVALUATION_dev_frozen_notes.md` and `../evaluation_dev_frozen/` — the
>   frozen A/B2/B3 campaign under `assessment_v4`, which replaces the smoke
>   runs below as the description of model behaviour;
> - `cleanroom_2026-10-07.md` — clean-clone install, 128 tests, wheel audit and
>   personal-data scan;
> - `freeze_guard_2026-10-07.md` — the manifest guard aborting a real run;
> - `../tuning/README.md` — why `assessment_v2` was replaced.
>
> The 92-test figure and the `assessment_v2` smoke timings below are historical.

## Offline software verification

- Full regression suite: **92 tests passed**, including headless Streamlit review/export interaction, model-output faults, evaluation integrity and B3 replay.
- `ruff check src tests app scripts`: passed.
- `git diff --check`: passed.
- A/B2 fixture campaign: 62 labelled pairs, 13 submissions, 2 labelled rubrics, 3 repeats. Artifacts: `../EVALUATION_fixture_v2.md` and `../evaluation_fixture_v2.json`.
- B3 fixture campaign: same inputs and 3 repeats. Artifacts: `../EVALUATION_B3_fixture_v2.md` and `../evaluation_B3_fixture_v2.json`.

Both fixture campaigns fail M4 macro-F1 ≥0.75, as recorded; the fixture is a
heuristic software stand-in, not Qwen or model-quality evidence. B3 omits B2,
so relative reduction versus B2 is unmeasured, not passed. Both evaluator
artifacts identify the same final package source hash:
`ff771e0ee7b7a6a582db885bfba86ec84b20897d5322117968ffd42208da3444`.

## Actual current-code local-model smoke run

Final artifact: `local_smoke_2026-10-04_final.json`, produced by
`scripts/validate_local_model.py` with existing local `qwen2.5:7b-instruct`,
temperature 0 and maximum 700 output tokens. The temporary local Ollama server
used `OLLAMA_CONTEXT_LENGTH=16384` and one model worker. Pipeline criterion
requests can overlap, but the server queues model work. No hosted inference
or API key was used. Model digest, server version, timestamps and per-file
hashes are preserved in JSON. After completion, **every source/input/prompt
hash in the final artifact matched the current files**.

| Case | Context | Pages / units | Wall-clock time | Validator-accepted records | Numeric suggestions |
|---|---|---:|---:|---:|---:|
| Synthetic evaluation-keyword decoy | BM25 K=5 | 6 / 6 | 33.81 s | 5/5 | 3/5 |
| Same synthetic decoy, B3 | All indexed units | 6 / 6 | 38.29 s | 5/5 | 3/5 |
| Own proposal PDF, official proposal rubric | BM25 K=5 | 16 / 66 | 61.85 s | 5/6 | 5/6 |

A validator-accepted **insufficient** record can legitimately contain no score;
this is different from human acceptance. Neither synthetic path awarded a
score to C3 (evaluation plan), whose evidence only mentions evaluation words.
Both also abstained on C4. B2's actual structured decoy result is saved in the
same artifact. These few observations cannot establish that one system is
more accurate or faster across the corpus.

The real PDF's R1 stayed rejected after the bounded revision because a positive
statement lacked a citation (`uncited_claim:1`). The score remains null and the
reviewer must explicitly edit or reject. Its five remaining suggestions are
provisional, not reference grades. The user's actual 6.5/10 proposal outcome is
feedback for project improvement, not automatically a gold label for this
possibly different proposal PDF/version.

The PDF run was under 120 seconds on this occasion. This **does not establish
median/p95 latency, repeatability, or a speed-up over the historical 126-second
run**: warm-up, scheduling, model outputs and validation differ.

## Diagnostic first run and fix

`local_smoke_2026-10-04.json` is retained as the first diagnostic run. It exposed
a false positive: “Specify the metrics, baselines, scenarios, and labelled data
for your evaluation plan” was classified as an uncited factual statement.
The feedback check now recognises this imperative advice. A regression also
checks that appending an uncited factual sentence still causes rejection.

The first run's PDF time was 100.58 seconds. Its manifest predates the final
`eval.py` edits, which were concurrent but are not imported by the smoke
script. Treat that artifact as diagnostic only. The final rerun above has an
exact current-source manifest and shows B3's advice no longer fails that check.
No historical live benchmark was overwritten.

## Reproduce

Start the local server if needed, from a separate terminal:

```sh
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_CONTEXT_LENGTH=16384 ollama serve
```

From the project root:

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests app scripts
.venv/bin/python scripts/validate_local_model.py --output docs/validation/local_smoke_next.json
```

The script refuses to overwrite an existing artifact. Choose a new output path
for each run. Full A/B2/B3 commands, fixed metrics and the independent-annotation
plan are in `../EVALUATION_PROTOCOL.md`. Do not present this smoke run as the
completed independent campaign.
