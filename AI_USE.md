# Generative AI use disclosure

- **Tool:** Claude (Anthropic) running in Cursor, 12–13 Sep 2026.
- **What it produced:** the initial code of this repository, the synthetic dataset generator, tests, documentation and the evaluation harness, working from the approved Group 14 Track A proposal and the ELEC5623 lecture/lab materials on Canvas. On 13 Sep it also installed a local open-weight model (Ollama, `qwen2.5:7b-instruct`) on the group member's machine, ran the evaluation with it and committed the report (`docs/EVALUATION_live_qwen7b.md`), transcribed the Canvas marking rubric into `dataset/real/`, and added our own proposal PDF (cover removed) as the real test document.
- **What it did not do:** decide the product scope (that is the proposal), label data with a second annotator, run marker sessions, or choose the production model.
- **Human review:** the group is responsible for reading, running and modifying everything here before any Canvas submission. Each member's edits are recorded in git history under their own branch (see `CONTRIBUTING.md`).
- **In the product itself:** the assessment model is called only through `src/rubric_agent/gateway.py`; its output is treated as untrusted input and validated before a marker sees it (`docs/GOVERNANCE.md`).

- **Tool:** Cursor agent, 22 Sep 2026.
- **What it produced:** downloaded the new Canvas files into the course folder; drafted `docs/FINAL_REPORT_DRAFT.md` and `docs/WEEK8_TUTOR_UPDATE.md` from the existing repository and the 13 Sep evaluation files; added the Week 7 note in `docs/ARCHITECTURE.md`.
- **What it did not do:** run a new model evaluation, relabel data, invent marker-session results, or change the agent pipeline. The LangChain Lab 7 notebook was saved as course material and was not turned into this product.

- **Tool:** Cursor agent, 23 Sep 2026.
- **What it produced:** concurrent criterion calls in `run_pipeline`, a test that the calls overlap and stay in rubric order, and `scripts/export_second_pass.py`, which writes a blank labelling sheet.
- **What it did not do:** relabel the 62 pairs, run a new model evaluation, invent marker-session times, or change the prompt or the validator.
- **Also on 23 Sep:** a marker checklist (`src/rubric_agent/coverage.py`) shown on the review page. It does not alter scores or the 13 Sep metrics.

- **Tool:** Cursor agent, 23 Sep 2026 (related work and quote check).
- **What it produced:** a comparison in section 3 of `docs/FINAL_REPORT_DRAFT.md` with eight public GitHub grading repositories, and a validator check (`quote_not_in_evidence`) that a quote written next to an evidence id must occur in that unit, with unit tests.
- **What it did not do:** relabel the 62 pairs, rerun the model, or change the 13 Sep metrics.

- **Tool:** Cursor agent, 4 Oct 2026.
- **What it produced:** revised `docs/FINAL_REPORT_DRAFT.md` against Haolin Jin's proposal comments, and wrote `docs/MARKER_RESPONSE.md`. Publisher and arXiv pages were opened for Cai (2026), Hong et al. (2026, arXiv v1 and the current record) and Chu et al. (2025). GradeAgentOps was taken from the Crossref record for DOI 10.3390/ai7060198, including the deposited abstract.
- **What it did not do:** change the 6.5/10 proposal mark, resubmit the proposal, invent who did which work, invent metrics or quotations, relabel the 62 pairs, or rerun the model.

Update this file whenever an AI tool contributes to a change.
