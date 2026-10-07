# Status — 4 October 2026

The user supplied the proposal result **6.5/10**, marked by **Haolin Jin**.
`docs/MARKER_RESPONSE.md` maps each deduction to current work. The saved A2 brief
allocates 4 implementation + 4 GenAI engineering + 4 evaluation + 3 novelty +
2 track alignment + 2 workflow + 1 documentation marks. This is not an estimated grade.

## Implemented in this revision

- Same Track A rubric-marking product and existing FR/NFR remain in place.
- `AGENTS.md` records the user's instruction to apply the tutor's actual feedback in future 5623 work.
- `docs/RELATED_WORK.md` and report §3 compare Evidence-First Scoring, GradeAgentOps, RULERS and RAG; evidence-first is not claimed as an invention.
- `docs/TEAM_DELIVERY.md` names proposed owners. **Zhengyu Han leads core GenAI engineering and evaluation design/interpretation.** Roles are not completed-contribution claims.
- Model scores reject non-finite values, wrong criteria, wrong range/grid and invalid cited quotes in feedback as well as explanations.
- Invalid/absent AI scores cannot be accepted. Human edits follow rubric range/grid. Invalid UI edits clear stale confirmation; export rechecks all decisions.
- B3 full-context ablation uses the same criterion prompt, citations, validator and correction budget, and is supported by logging/replay and CLI.
- Evaluation reports include denominators, A/B2 macro-F1, score coverage, conditional normalised MAE, per-criterion QWK, shared scored subsets, hashes and individual repeated outputs. One run cannot pass repeatability; empty denominators remain unmeasured.

## Verification and evidence limits

`docs/validation/README.md` records actual current checks and local-model smoke
runs. `EVALUATION_fixture_v2.md` and `EVALUATION_B3_fixture_v2.md` are offline
harness checks, **not LLM-quality evidence**. Their M4 failure is retained.

The 13 September reports remain historical snapshots. Their pooled QWK is
superseded by a scale-aware implementation and must not be compared directly
with new QWK. A citation's existence does not establish semantic support; M6
counts uncited detected sentences only. B2 was not instructed to cite.

Current local-model smoke checks use the existing Qwen2.5-7B installation; they
do not constitute a full labelled campaign or independent validation. The
prototype can reject a record and leave its score empty; a successful HTTP
call is not automatically a usable score.

## Remaining human/evidence work

1. Confirm proposed roles and record each member's actual reviewed contribution.
2. Complete independent annotation before adjudication, preserve both originals, and compute agreement.
3. Execute the frozen A/B2/B3 protocol on the fresh heldout corpus. Existing dev/heldout data have both been inspected.
4. Conduct 2–3 real marker sessions and record timing, overrides and usability observations.
5. Integrate final results, inspect report length/layout, verify the source package runs on the demo machine and rehearse without AI.

## Course facts and history

From the local A2 brief: source code plus one final report, suggested 8–12 pages
excluding references/appendices, due **3 November 2026, 23:59**; presentation
and Q&A on **4 November 2026**, with AI prohibited during the live assessment.
The separate presentation-format brief is not verified here. Older Week 8
updates are historical; this task did not refresh Canvas.
