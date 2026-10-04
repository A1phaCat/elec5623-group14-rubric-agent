# Marker comments addressed

Draft aid, 2026-10-04. Not part of the submitted page count.

Proposal marker: Haolin Jin. Score: 6.5/10. This note does not change that mark and is not a resubmission. The approved direction stays Track A, a rubric marking agent, as approved by tutor Linghan Huang on 6 September 2026.

The sentences below are the rubric comments, quoted, then the section of `docs/FINAL_REPORT_DRAFT.md` that now answers them.

## Problem / motivation, 0.5/1.5

> They called an "evidence-first control architecture" the key innovation, but closely related work was already published. "Evidence-First Scoring explicitly separates criterion-specific evidence extraction from scoring."

Section 3 no longer treats that separation as the invention. Cai (2026) already defines Evidence-First Scoring as two stages: extract criterion-specific spans, then score from those spans and the rubric. GradeAgentOps, RULERS and a retrieval-augmented short-answer grader are named in the same section. The difference stated for this repository is BM25 top-5 over one submission, a fail-closed validator, human accept/edit/reject, export blocked until every criterion is decided, and no LMS write.

Requirements Engineering and Project Definition was 1.5/1.5. Section 2 keeps the same user, scope and out-of-scope list.

## Technical design, 1.5/2

> Still at the level of "BM25/keyword baselines, with embeddings or hybrid methods added only if they improve Recall@K" and "Likely components include...". Missing truly defined evaluation metrics.

Sections 4–6 state the decisions that are in the code: BM25 k=5, local `qwen2.5:7b-instruct`, temperature 0, prompt `assessment_v2`. Embeddings are not in the measured system. Section 7 names M4, M6, M8, M12 and M13, the targets, and the miss: M4 0.554 against 0.75.

## Analysis / evaluation, 1/2

> Compared manual marking, generic LLMs, Turnitin, Gradescope. Those are not the critical research alternatives. Should have compared Evidence-First Scoring, GradeAgentOps, RULERS, or at least current RAG-assisted assessment. The claim that evidence-first review is the key differentiator lost credibility.

Section 3 compares those systems. Turnitin and Gradescope stay only as products, not as the research comparison. Chu et al. (2025) is the retrieval-augmented assessment paper. The measured comparison is still the same model in one call (B2). Kappa stays about 0.48 for the agent and about 0.87 for B2. Unsupported claims stay 0 versus 1. The report does not claim the higher agreement. Second-annotator agreement and marker-session times are stated as not collected.

## Team, 1/1.5

> Missing clear allocation of work.

Section 10 does not fill five contribution rows. Git history on 4 October 2026 is two commits by `hanzhengyu202305-arch`. Each member has to write a row they can point to in git before 3 November 2026.

## References, 1/1.5

> Missing a lot of reference papers.

Section 10 adds the papers opened on 4 October 2026: Cai (2026), Anghel et al. (2026), Hong et al. (2026a, 2026b), Chu et al. (2025). Citations already in the draft were kept. Papers that could not be opened were not added.
