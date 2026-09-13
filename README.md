# AI-Assisted Rubric Marking Agent

ELEC5623 Group 14 · Track A · semester project prototype (v0.3.0).

A decision-support tool for human markers: it parses an analytic rubric and a
long text submission, retrieves evidence per criterion, asks a model for an
**evidence-constrained** provisional score, validates the answer (and sends the
validator's findings back to the model once if it broke a rule), and lets the
marker accept, edit or reject each criterion before anything is exported. It
is not an autonomous grader (Constraint C1).

![Review UI — our proposal on the official rubric, local Qwen 7B](docs/img/review_ui_live.png)

*Review page on the real case with the local 7B model: every claim in the explanation cites an evidence unit; each unit shows its page and section; the record was corrected once after the validator sent its findings back.*

```
rubric + submission → parse → chunk (E-001…) → BM25 top-K per criterion
        → model gateway (criterion + evidence only) → validator (fail-closed, 1 corrective round)
        → marker review (accept / edit / reject) → export JSON/CSV + run log → replay
```

## Quick start

```bash
cd rubric-marking-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
python scripts/generate_dataset.py        # synthetic corpus, safe to re-run
pytest -q                                 # 32 tests, offline, ~10 s
ruff check src tests app scripts          # lint (also in CI)
rma demo --submission s4_decoy_eval       # agent path on the keyword-decoy case
rma baseline --submission s4_decoy_eval   # B2: whole-document grading, for contrast
rma eval --report docs/EVALUATION.md      # M1–M17 harness on 62 labelled pairs
rma demo --log runs.jsonl && rma replay --log runs.jsonl   # M12 reproducibility
streamlit run app/streamlit_app.py        # marker UI + Evaluation + Run log pages
```

### The real case

The first example in the UI (and the command below) runs the agent over **our
own 16-page proposal PDF against the official Canvas marking rubric** (six
criteria, 10 marks, level descriptors verbatim). It is the only real document
in the repository; we own it and the cover page with names and IDs is removed.
See `dataset/real/README.md`.

```bash
rma demo --rubric dataset/real/elec5623_business_proposal_rubric.md \
         --submission dataset/real/group14_proposal_v2.pdf
```

### Models

| Gateway | How to select | Use |
|---|---|---|
| **fixture** (default) | nothing to set | deterministic offline stand-in; tests, CI, fault injection |
| **local Ollama** | run `ollama serve`, then `--gateway ollama:qwen2.5:7b-instruct` (the UI lists running models automatically) | real model, no key, nothing leaves the machine — this is candidate (b) of proposal §6.3 |
| **hosted / Azure** | `RMA_MODEL_ENDPOINT`, `RMA_MODEL`, `RMA_MODEL_API_KEY` (+ `RMA_API_KEY_HEADER=api-key`, `RMA_API_VERSION` for Azure), then `--gateway live` | candidate (a); see `docs/GOVERNANCE.md` for secret handling |

Live evaluation with the local model: `rma --gateway ollama:qwen2.5:7b-instruct eval --repeats 2 --report docs/EVALUATION_live_qwen7b.md --json docs/evaluation_live_qwen7b.json`
(about 50 min on an M2 Pro; results committed under `docs/`).

## What is in the box

| Path | Purpose |
|---|---|
| `src/rubric_agent/` | Package: parsers, chunker, retriever, gateway, validator, review, store, eval, CLI |
| `app/streamlit_app.py`, `app/pages/` | Marker UI (review · B2 comparison · export), Evaluation dashboard, Run-log viewer with replay |
| `prompts/` | Versioned prompts (`assessment_v2` current, `assessment_v1` kept, `direct_grading_v1` for B2) |
| `dataset/` | 3 synthetic rubrics (block, table, numbered), 13 submissions, 62 labelled pairs, labelling guide |
| `dataset/real/` | Official Canvas rubric (transcribed) + our proposal PDF |
| `tests/` | Acceptance tests mapped to FR/NFR IDs and scenarios S1–S8, plus headless UI tests |
| `docs/ARCHITECTURE.md` | Context and container diagrams, module table, failure handling |
| `docs/REQUIREMENTS_TRACEABILITY.md` | FR/NFR → code → test → metric → owner |
| `docs/EVALUATION.md`, `docs/EVALUATION_live_qwen7b.md` | Generated metric reports: fixture and local 7B model |
| `docs/EVALUATION_NOTES.md` | What the numbers mean: agent vs B2, the label/sufficiency finding, k=10 control run, latency |
| `docs/GOVERNANCE.md` | Oversight, privacy, secrets, limitations, risk register status |
| `docs/DEMO_SCRIPT.md` | Week 13 demo run-sheet and Q&A prep |
| `CONTRIBUTING.md` | Branch/PR rules and area ownership A1–A5 |
| `STATUS.md` | What is done, what needs people, what needs the tutor |
| `AI_USE.md` | Generative AI disclosure |

## Status against the course

Checked Canvas 13 Sep 2026: the Project Development (20%) and Presentation
(10%) briefs are still not published as assignment pages; Week 1 slides list
the expected evidence (working prototype aligned with the approved proposal,
repository history, architecture, evaluation, safety/governance, limitations,
contribution record, Week 13 demo with all-member Q&A). This repository targets
that list. See `STATUS.md` for the open items that need people or approvals
rather than code.

Also from Canvas: **Lab 6 (published 13 Sep) confirms the mid-term quiz on
Wed 16 Sep, 11:00, paper, 1 hour, Weeks 1–6, one A4 double-sided cheat sheet,
calculator allowed.** This repository does not help with that.
