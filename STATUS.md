# Status — 13 Sep 2026 (v0.3.0)

## Canvas facts (checked today)

- Assignments page: Interactive Oral 1 (2/2), Oral 2, Business Proposal (submitted, ungraded). No Project Development or Presentation assignment page yet.
- The Business Proposal **marking rubric** is on the assignment page (6 criteria, 10 marks). It is transcribed in `dataset/real/` and is the rubric used by the first UI example.
- Modules: Lab 6 uploaded today. Part A = mid-term quiz Wed 16 Sep 11:00 (paper, 1 h, Weeks 1–6, A4 cheat sheet). Part B = MCP + LangChain concepts: tools ≠ permission, validate arguments, fail with an explicit error, keep credentials out of prompts and logs. Those rules are applied in `gateway.py` / `validator.py`.
- Until a brief appears, the approved Group 14 proposal is the project definition.

## Done in code (all tested offline; live numbers from a local 7B model)

| Proposal item | Status |
|---|---|
| FR1–FR3 rubric ingest: block, table (numeric or banded headers, optional Max), numbered list, PDF; official Canvas rubric | done |
| FR4–FR5 TXT/PDF ingest with heading detection; 16-page real PDF → 66 units with section names | done |
| FR6 BM25 top-K or explicit empty; Recall@5 0.99 / Precision@5 0.78 | done |
| FR7 evidence in context (cited vs uncited, adjacent text, locator) | done (UI) |
| FR8 sufficiency label | done; macro-F1 0.55 with Qwen 7B (target 0.75) — see `docs/EVALUATION_NOTES.md` |
| FR9–FR11 constrained score, grounded explanation, fail-closed validator, one corrective round | done; M6 0.00, M7 1.00 live |
| FR12–FR13 accept/edit/reject, override with AI value retained, range-checked | done |
| FR14 draft feedback with citation check | done; M17 1.00 live |
| FR15 export JSON + CSV, all fields, session summary | done; M16 1.00 |
| FR16 / NFR7 run log incl. attempts; `rma replay`; Run-log page | done; M12 0.97 live |
| NFR3 latency ≤120 s for 10–20 pages | 51 s on the 12-page case with the 7B model (M2 Pro) |
| NFR5 export blocked while pending | done (unit + UI test) |
| NFR6 no student data; local model keeps text on the machine | done |
| B2 baseline + comparison | done; B2 QWK 0.87 but 45/45 claims untraceable |
| C5 provider-independent adapter: fixture / local Ollama / OpenAI-Azure | done; live run committed |
| Docs: architecture, traceability, governance, demo script, evaluation notes, contributing, CI (tests + lint + real case) | done |

## Needs the group / tutor (not code)

1. **Model decision.** We now have real numbers from candidate (b) (local Qwen 7B). If the group wants candidate (a) (Azure AI Foundry from Lab 1), set the `RMA_*` variables on one machine and run `rma --gateway live eval --report docs/EVALUATION_live_azure.md --json docs/evaluation_live_azure.json`; the Evaluation page will show both. Ask the tutor which provider is acceptable for the demo.
2. **Annotation round (the important one).** The live run shows the agent one step *more conservative* than our single-annotator labels on 20 of 62 pairs. A second labeller on the 62 pairs, with sufficiency and score labelled independently, decides whether that is a model problem or a label problem. Guide: `dataset/LABELLING_GUIDE.md` (add one worked example of "sufficient evidence, low score").
3. **Two to three marker sessions (S8)** for M9–M11, M14. The export now records session duration, override rate and intervention count, so the session only needs a stopwatch and the questionnaire from proposal §8.5.
4. **Fill in names** in `docs/REQUIREMENTS_TRACEABILITY.md`, `CONTRIBUTING.md` and `docs/DEMO_SCRIPT.md` (areas A1–A5), then each member pushes to their own branch so the contribution record exists.
5. **Demo machine.** Ollama + `qwen2.5:7b-instruct` (4.7 GB) installed and `OLLAMA_CONTEXT_LENGTH=16384`; pre-run the real case before the session (~2 min).
6. **Hybrid re-ranking** stays out: Recall@5 is 0.99 on the corpus (de-scoping rule §10.3).

## Honest limits

- The fixture is a descriptor-matching heuristic for tests and CI. It is not evidence about any model.
- The live numbers come from one 7B model on 62 synthetic pairs labelled by one person. They are enough to show the pipeline works end to end and to expose the labelling issue above; they are not the evaluation campaign.
- No gold labels exist for the real proposal case (our own marks are not released, and labelling our own work would not be independent).
