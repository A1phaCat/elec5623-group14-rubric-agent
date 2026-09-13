# Real case: our own proposal against the official rubric

| File | What it is | Provenance |
|---|---|---|
| `elec5623_business_proposal_rubric.md` | The Canvas marking rubric for the Group Business Proposal (6 criteria, 10 marks). Level descriptors verbatim; criterion IDs R1–R6 are ours. | Canvas course 74325, assignment "Business Proposal", read 13 Sep 2026 |
| `group14_proposal_v2.pdf` | Group 14's own proposal (revision v2, 16 pages). **Cover page removed** so that no names or student IDs are in the repository. | `../../proposal_v2/`, built with pandoc |

Why it is here: proposal §6.5 asks for at least one real document alongside the
synthetic corpus, and NFR6 forbids using other students' work. Our own
proposal is the one long, real, rubric-marked document we are entitled to use.
It exercises the parts synthetic data cannot: real PDF text extraction
(paragraph breaks lost, numbered headings, tables), a 16-page evidence index,
and level descriptors written by a real assessor.

There are **no gold labels** for this pair: the tutor's marks are not released,
and marking our own work would not be an independent label. It is a demo and
robustness case, not part of the M4/M8 corpus.

```bash
rma demo --rubric dataset/real/elec5623_business_proposal_rubric.md \
         --submission dataset/real/group14_proposal_v2.pdf
rma --gateway ollama:qwen2.5:7b-instruct demo --rubric dataset/real/elec5623_business_proposal_rubric.md \
         --submission dataset/real/group14_proposal_v2.pdf
```
