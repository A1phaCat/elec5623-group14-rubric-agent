# Status — 13 Sep 2026

## Canvas facts (checked today)

- Assignments page: Interactive Oral 1 (2/2), Oral 2, Business Proposal (submitted, ungraded). No Project Development or Presentation assignment page yet.
- Modules: Lab 6 uploaded today. Part A = mid-term quiz Wed 16 Sep 11:00 (paper, 1 h, Weeks 1–6, A4 cheat sheet). Part B = MCP + LangChain concepts: tools ≠ permission, validate arguments, fail with an explicit error, keep credentials out of prompts and logs. Those rules are applied in `gateway.py` / `validator.py`.
- Until a brief appears, the approved Group 14 proposal is the project definition.

## Done in code (all tested offline)

| Proposal item | Status |
|---|---|
| FR1–FR3 rubric ingest: block, table (0.5 steps), numbered list (2.5 steps), PDF | done |
| FR4–FR5 TXT/PDF ingest, locator on every unit | done |
| FR6 BM25 top-K or explicit empty; Recall@5 0.99 / Precision@5 0.78 on corpus | done |
| FR7 evidence in context (cited vs uncited, adjacent text, locator) | done (UI) |
| FR8 sufficiency label | done; quality depends on model |
| FR9–FR11 constrained score, grounded explanation, fail-closed validator (5 fault modes) | done |
| FR12–FR13 accept/edit/reject, override with AI value retained, range-checked | done |
| FR14 draft feedback with citation check (M17 = 1.0) | done |
| FR15 export JSON + CSV with all fields (M16 = 1.0) | done |
| FR16 / NFR7 run log with inputs+outputs; `rma replay` (M12 = 1.0) | done |
| NFR5 export blocked while pending | done (unit + UI test) |
| NFR6 synthetic data only; live gateway opt-in via env | done |
| NFR3 latency (S5, 12 pages): ms with fixture; measure again with live model | done for harness |
| B2 baseline + M6 comparison | done |
| C5 provider-independent adapter: OpenAI / Azure / Ollama client | done, tested with stub transport |
| Docs: architecture, traceability, governance, demo script, contributing, CI | done |

## Needs the group / tutor (not code)

1. **Model approval and access.** Decide hosted (Azure AI Foundry from Lab 1) vs local (Ollama 7–8B). Set `RMA_*` env on the demo machine, run `rma eval --gateway live --report docs/EVALUATION.md`, commit the report. Expect M4 and M8 to move a lot; the fixture's 0.43 macro-F1 is the floor, not a result.
2. **Annotation round.** Second labeller on the 62 pairs, agreement statistic, and human judgement for M5 (currently a phrase-overlap proxy). Guide: `dataset/LABELLING_GUIDE.md`.
3. **Two to three marker sessions (S8)** for M9–M11, M14. Script and questionnaire items are in the proposal §8.5; record time per submission and interventions.
4. **Fill in names** in `docs/REQUIREMENTS_TRACEABILITY.md`, `CONTRIBUTING.md` and `docs/DEMO_SCRIPT.md` (areas A1–A5), then each member pushes to their own branch so the contribution record exists.
5. **Optional public report** as a fourth rubric/submission pair (proposal §6.5 asks for at least one openly licensed real document).
6. **Hybrid re-ranking** only if a live-model run shows Recall@5 < 0.85 on held-out (de-scoping rule §10.3).

## Honest limits

The fixture is a descriptor-matching heuristic. It exists so the workflow, validator and metrics can be tested without a key. It is not evidence that a model would mark well; that measurement is item 1 above.
