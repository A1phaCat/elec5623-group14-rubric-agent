# Named team delivery plan

Updated 4 October 2026. **Proposed allocation, pending team confirmation.**
The user explicitly requested that Zhengyu Han own the core GenAI system and
evaluation work. Other assignments below are suggestions, not claims about
past authorship, consent or completed work. The A2 rubric awards group marks;
the mapping below is work prioritisation, not an individual mark guarantee.

| Member | Primary responsibility | Concrete deliverables | Requirements / A2 evidence |
|---|---|---|---|
| **Zhengyu Han** | **A4: technical lead, GenAI assessment and validation; evaluation design and interpretation** | Model/prompt/context decision record; schema and evidence validator; bounded corrective loop; B2/B3 experiment specification and result interpretation; report §§5, 7–8; explanation of accuracy/coverage/latency trade-offs | FR9–FR11, FR14; leads evidence for GenAI engineering (4 marks) and evaluation (4 marks) |
| Zongjian Li | A1: problem, rubric schema/parser and related-work audit | Check supported rubric forms and descriptors; verify the closest-paper comparison and citations; own report §§2–3 and parser examples | FR1–FR3; supports novelty/positioning (3 marks) and product completeness |
| Yuchun Zheng | A2: document ingestion, provenance and export; independent annotation coordination | Validate PDF locators; inspect export fields; arrange blinded second-pass labels and preserve disagreements; maintain data provenance | FR4–FR5, FR15; supports completeness and evaluation |
| Yutong Liu | A3: retrieval, logging and experiment execution | Verify BM25 ranking; run the frozen evaluation commands; preserve manifests/raw records; verify replay and compare full-context B3 | FR6, FR8, FR16; supports architecture and reproducibility under Zhengyu Han's protocol |
| Zhaoxinyi Zhou | A5: marker UI and usability study | Test accept/edit/reject/export workflow; conduct 2–3 consenting marker sessions; collect timings, overrides and usability notes; prepare current screenshots | FR7, FR12–FR13; workflow (2 marks), completeness and user evidence |

## Zhengyu Han: concentrated core work

Use the existing prototype and local Qwen2.5-7B-Instruct as the fixed candidate
for the next measured run. Own decisions and evidence rather than training a
new model or adding an unrelated framework. Codex can assist with code changes,
regression tests, reproducible experiment scripts, metric computation, literature
checks, report editing and rehearsal questions. Every result still comes from
an executed experiment or identified source, and every decision needs human review.

The highest-value package is: one defensible architecture, a tested validator,
an executable same-prompt full-context comparison, a table of real results with
coverage and uncertainty, and three explained failure cases. Han should be able
to explain why citation presence is weaker than semantic support, why a system
that abstains can show deceptively low MAE, and why B3 is a fairer retrieval
ablation than an unconstrained B2 prompt.

Independent human labels, real marker timings, teammates' acceptance of roles
and the live assessed Q&A cannot be supplied by an AI assistant. The source brief
prohibits AI during the live presentation/Q&A.

## Proposed milestones (internal targets, not school deadlines)

| Target | Output | Lead / check |
|---|---|---|
| 7 Oct | Confirm named roles; verify three closest works and freeze protocol | Li + Han / all members confirm |
| 14 Oct | Blinded second labels complete; discrepancies preserved before discussion | Zheng / Liu checks completeness |
| 21 Oct | Current-source agent/B2/B3 runs, provenance and failure analysis | Liu executes / Han interprets |
| 25 Oct | 2–3 marker sessions and current demo screenshots | Zhou / Zheng verifies exports |
| 29 Oct | Report integrated; contribution evidence and citations checked | Han + Li / all members review |
| 1 Nov | Clean-machine source rehearsal, report length and demo rehearsal | All five |

The local A2 brief states source code plus one report due 3 November 2026
23:59, and presentation/Q&A on 4 November. Recheck the final Canvas brief before
submission; the 8-minute script here is an internal rehearsal plan.

## Actual contribution register

Add completed evidence here as each member reviews or produces it. A task
assignment or AI-generated file is not evidence that the assigned person has
already done the work. Do not manufacture commits under another person's name.

| Member | Confirmed contribution evidence | Confirmation |
|---|---|---|
| Zhengyu Han | Pending member review of code, experiments and report sections | Core role requested by user; completed contribution not yet attested |
| Zongjian Li | Pending commits, reviewed references or parser validation record | Pending |
| Yuchun Zheng | Pending extraction/export checks and independent annotation records | Pending |
| Yutong Liu | Pending experiment manifests, logs and replay verification | Pending |
| Zhaoxinyi Zhou | Pending UI tests, session records and demo evidence | Pending |
