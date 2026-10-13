# Task 3: Trial Record

| Participant | Manual marking (first) | Tool marking (second) |
|---|---|---|
| P1 | s1_standard | s2_dispersed |
| P2 | s2_dispersed | s1_standard |

Rubric: `dataset/rubrics/engineering_report.md`

## Setup

| Item | Entry |
|---|---|
| Participant ID (P1/P2) | ____________________ |
| Date | ____________________ |
| Recorder code | ____________________ |
| Participant confirmed adult | □ Yes　□ No |
| Consent script read aloud | □ Yes　□ No |
| Participant consents | □ Yes　□ No |
| Model service | ____________________ |
| Model name | ____________________ |
| Prompt version / K | ____________________ |
| Real model call verified (not fixture) | □ Yes　□ No |
| Warmed up; same config for both | □ Yes　□ No |

**Consent script:**

> This is a prototype marking assistant for a university assignment. You will
> mark synthetic, made-up student work, never anyone's real submission. I will
> time how long each document takes and note when I have to help you use the
> interface. Afterwards I will ask five short questions. I am recording no
> personal information about you, and you may stop at any point. The scores you
> give are not used to grade anyone.

## Session 1: Manual Marking

| Item | Entry |
|---|---|
| Report ID | ____________________ |
| Start time | ____________________ |
| End time | ____________________ |
| duration_s (stopwatch) | ____________________ |

| Criterion | Max / Step | Score | Notes |
|---|---|---|---|
| C1 · Problem definition | 4 / 1 | ______ | ____________________ |
| C2 · Methodology | 4 / 1 | ______ | ____________________ |
| C3 · Evaluation plan | 4 / 1 | ______ | ____________________ |
| C4 · Results and discussion | 4 / 1 | ______ | ____________________ |
| C5 · Communication | 2 / 1 | ______ | ____________________ |

Difficulties / participant quotes:

________________________________________________________________________

## Session 2: Tool Marking

| Item | Entry |
|---|---|
| Report ID | ____________________ |
| Start time | ____________________ |
| End time | ____________________ |
| Stopwatch seconds | ____________________ |
| Tool-exported duration_s | ____________________ |
| Reason if times differ | ____________________ |
| Export file path | ____________________ |
| Export completed | □ Yes　□ No; reason: ____________________ |

| Criterion | AI score | Decision (accept/edit/reject) | Final score | Notes / quotes |
|---|---|---|---|---|
| C1 | ______ | __________ | ______ | ____________________ |
| C2 | ______ | __________ | ______ | ____________________ |
| C3 | ______ | __________ | ______ | ____________________ |
| C4 | ______ | __________ | ______ | ____________________ |
| C5 | ______ | __________ | ______ | ____________________ |

| Field (from export) | Entry |
|---|---|
| criteria_decided | ______ |
| accepted | ______ |
| edited | ______ |
| rejected | ______ |
| facilitator_interventions | ______ |
| evidence_items_opened_in_context | ______ |
| evidence_items_found_by_searching_document | ______ |

| Time | Issue / misreading | Participant quote | Recorder explanation |
|---|---|---|---|
| ______ | ______________ | ______________ | ______________ |
| ______ | ______________ | ______________ | ______________ |
| ______ | ______________ | ______________ | ______________ |

## Questionnaire

1 = strongly disagree, 5 = strongly agree

| Statement | Response |
|---|---|
| 1. I remained in control of the final score. | □ 1　□ 2　□ 3　□ 4　□ 5 |
| 2. The evidence saved me searching. | □ 1　□ 2　□ 3　□ 4　□ 5 |
| 3. I could tell which part of the submission each suggested score came from. | □ 1　□ 2　□ 3　□ 4　□ 5 |
| 4. I would trust this to prepare a first pass that I then check. | □ 1　□ 2　□ 3　□ 4　□ 5 |
| 5. The interface stayed out of my way. | □ 1　□ 2　□ 3　□ 4　□ 5 |

**What would you change first?**

________________________________________________________________________

________________________________________________________________________

## Deliverables

| Item | Status / Path |
|---|---|
| Manual record | ____________________ |
| Tool record | ____________________ |
| Tool export file | ____________________ |
| Questionnaire responses | ____________________ |
| Interface screenshot | ____________________ |
| Screenshot free of personal info / keys | □ Checked |
| Missing fields and reasons | ____________________ |

Output files: `P1_manual.json`, `P1_agent.json`, `P2_manual.json`, `P2_agent.json` (per `TEMPLATE.json`).