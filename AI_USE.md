# Generative AI use disclosure

- **Tool:** Claude (Anthropic) running in Cursor, 12–13 Sep 2026.
- **What it produced:** the initial code of this repository, the synthetic dataset generator, tests, documentation and the evaluation harness, working from the approved Group 14 Track A proposal and the ELEC5623 lecture/lab materials on Canvas.
- **What it did not do:** decide the product scope (that is the proposal), label data with a second annotator, run marker sessions, or choose the production model.
- **Human review:** the group is responsible for reading, running and modifying everything here before any Canvas submission. Each member's edits are recorded in git history under their own branch (see `CONTRIBUTING.md`).
- **In the product itself:** the assessment model is called only through `src/rubric_agent/gateway.py`; its output is treated as untrusted input and validated before a marker sees it (`docs/GOVERNANCE.md`).

Update this file whenever an AI tool contributes to a change.
