# Generative AI use disclosure

- **Tool:** Claude (Anthropic) running in Cursor, 12–13 Sep 2026.
- **What it produced:** the initial code of this repository, the synthetic dataset generator, tests, documentation and the evaluation harness, working from the approved Group 14 Track A proposal and the ELEC5623 lecture/lab materials on Canvas. On 13 Sep it also installed a local open-weight model (Ollama, `qwen2.5:7b-instruct`) on the group member's machine, ran the evaluation with it and committed the report (`docs/EVALUATION_live_qwen7b.md`), transcribed the Canvas marking rubric into `dataset/real/`, and added our own proposal PDF (cover removed) as the real test document.
- **What it did not do:** decide the product scope (that is the proposal), label data with a second annotator, run marker sessions, or choose the production model.
- **Human review:** the group is responsible for reading, running and modifying everything here before any Canvas submission. Each member's edits are recorded in git history under their own branch (see `CONTRIBUTING.md`).
- **In the product itself:** the assessment model is called only through `src/rubric_agent/gateway.py`; its output is treated as untrusted input and validated before a marker sees it (`docs/GOVERNANCE.md`).

Update this file whenever an AI tool contributes to a change.
