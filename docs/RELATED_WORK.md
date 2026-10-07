# Related-work evidence and contribution boundary

Verified against primary sources on **4 October 2026**. This note supports section 3 of `FINAL_REPORT_DRAFT.md` and the final assessment's 3-mark novelty/positioning criterion. It corrects the proposal's claim that separating evidence collection from scoring is itself novel. Publisher, arXiv and GitHub URLs retain their official HTTPS scheme.

## Closest prior work

| Source and publication/version date | Verified scope | Consequence for this project |
|---|---|---|
| **Evidence-First Scoring (EFS)** in Cai (2026), published 31 March 2026; version of record 19 May 2026 | The “Defense design and evaluation” section proposes extracting criterion-specific spans, then scoring using those fields and the rubric. | The evidence-before-score architecture is prior art. EFS is a method within the article, **not a separate paper title**. Its proposal does not establish that our implementation resists prompt injection. |
| **GradeAgentOps**, Anghel et al. (2026), published 29 May 2026 | A grading contract, deterministic checks, bounded repair, optional rubric/consistency memory and provenance logs; evaluated on 1,000 short exam answers with two expert graders. | Verification, repair and logging overlap directly. Our long-document retrieval and marker workflow are application choices; superiority needs a shared experiment. |
| **RULERS**, Hong et al. (2026a), arXiv v1, 13 January 2026 | Locked rubric bundles, evidence verification and score calibration for essay and summarization evaluation. | Evidence checks and auditable rubric execution are established. Our implementation has no learned post-hoc calibration or equivalent locked checklist compiler. |
| **RAG**, Lewis et al. (2020) | Generation conditioned on retrieved passages. | BM25 retrieval from a submission is an application of retrieval-augmented generation, not a new retrieval method. |
| **Short-answer RAG grading**, Chu et al. (2025), arXiv:2504.05276, abstract opened 4 October 2026 | Retrieves domain material from the question and the student answer, then grades the short answer. | This repository retrieves units inside one submission for the score to cite. It does not retrieve an external knowledge base, and Chu et al. were not rerun. |

The RULERS record now has a v3 dated **9 September 2026**, titled *From Rubrics to Reliable Scores: Evidence-Grounded Text Evaluation with LLM Judges* (Hong et al., 2026b). Cite the January v1 when establishing what existed before the 8 September proposal; identify v3 explicitly when discussing the later revision. The arXiv record says “Accepted to EMNLP 2026 Main Conference”; the report cites the inspected arXiv versions rather than inventing proceedings pages.

## Canonical source register

Full author lists and publication details are in the report's reference list. All links below were checked on 4 October 2026.

- Cai, Y. (2026). *Prompt injection attacks on educational large language models for higher and vocational education*. Scientific Reports, 16, 15594. [Publisher article](https://www.nature.com/articles/s41598-026-46563-1), [DOI](https://doi.org/10.1038/s41598-026-46563-1). The publisher lists a 19 June affiliation correction; this is not a new EFS paper. No EFS implementation was reproduced here.
- Anghel et al. (2026). *GradeAgentOps: A Verification-First Framework for Evidence-Anchored LLM Exam Grading*. AI, 7(6), 198. [Publisher article](https://www.mdpi.com/2673-2688/7/6/198), [version and citation record](https://www.mdpi.com/2673-2688/7/6/198/notes), [official code at inspected HEAD](https://github.com/anghelcata/GradeAgentOps/tree/5f53ab176b34e82ca9ba1cbe909065ff087a3597). Repository visibility was checked; its experiments were not run.
- Hong et al. (2026a). *RULERS: Locked Rubrics and Evidence-Anchored Scoring for Robust LLM Evaluation*. [arXiv v1 record](https://arxiv.org/abs/2601.08654v1), [v1 full text, especially sections 3.1–3.3](https://arxiv.org/html/2601.08654v1), [official code at inspected HEAD](https://github.com/LabRAI/Rulers/tree/b282ac63296529626cb108d77cf13c09006064b4). The code snapshot was not benchmarked here.
- Hong et al. (2026b). *From Rubrics to Reliable Scores: Evidence-Grounded Text Evaluation with LLM Judges*. [arXiv v3 record](https://arxiv.org/abs/2601.08654v3).
- Lewis et al. (2020). [NeurIPS RAG paper](https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html).
- Chu, Y., He, P., Li, H., Han, H., Yang, K., Xue, Y., Li, T., Krajcik, J., & Tang, J. (2025). *Enhancing LLM-based short answer grading with retrieval-augmented generation*. [arXiv abstract opened 4 October 2026](https://arxiv.org/abs/2504.05276).
- Robertson and Zaragoza (2009). [BM25 source](https://doi.org/10.1561/1500000019).
- Gao et al. (2023). [ALCE citation-evaluation paper and metadata](https://aclanthology.org/2023.emnlp-main.398/).
- Liu et al. (2024). [Lost in the Middle paper and metadata](https://aclanthology.org/2024.tacl-1.9/).
- Ribeiro, M. T., Wu, T., Guestrin, C., & Singh, S. (2020). *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList*. ACL 2020, pp. 4902–4912. [Paper and metadata](https://aclanthology.org/2020.acl-main.442/), [DOI](https://doi.org/10.18653/v1/2020.acl-main.442). Author list, venue, pages and DOI taken from the ACL Anthology BibTeX record on 7 October 2026. Week 9 lab reference [2].

## Behavioural testing: what we borrowed from CheckList

Ribeiro et al. (2020) argue that held-out accuracy on a single test set hides
capability-specific failures, and propose organising tests around capabilities
with three templates we use directly: **minimum functionality**, **invariance**
(a perturbation that must not change the output) and **directional expectation**
(a perturbation whose effect has a known sign). Their central methodological
point for us is that the oracle can be the *expected relationship between
outputs* rather than a reference string, which is what makes the tests usable
with no gold label.

That is the whole reason this project can test behaviour now: independent
annotation of the final-test corpus is still pending, and a relation-based
oracle does not need it. `docs/EVALUATION_PROTOCOL.md` Addendum A applies the
invariance template to evidence presentation order and the directional template
to removing a decisive paragraph.

What we do **not** claim: CheckList is a general methodology and a tooling
package for NLP capability testing, with user studies showing it helps experts
find more bugs. We reuse two of its test templates on a handful of cases. We
have not reproduced its experiments, built templates at its scale, or evaluated
its tooling. Naming the templates correctly is attribution, not a contribution
claim, and our paired rates are reported under their own metric names so they
are not confused with its results.

## Contribution we can defend from the implementation

The contribution is an implemented **marker decision-support workflow for long submissions**, integrating criterion-wise BM25 retrieval, provisional model judgements, deterministic checks, one corrective round, review decisions and an export record. The evaluation contributes a limited, reproducible case study of the trade-off between traceability and agreement. None of these components is claimed to be the first of its kind.

| Local evidence | What it supports | What it does not establish |
|---|---|---|
| `src/rubric_agent/retriever.py`, `pipeline.py` | BM25 with `k1=1.5`, `b=0.75`; default K=5; positive-score units only; criterion name plus upper descriptors form the query | Dense retrieval is inferior, or K=5 is optimal outside the tested corpus |
| `src/rubric_agent/validator.py`, `textutil.py` | Allowed-id checks; a heuristic uncited-positive-sentence check; cited-quote substring checks | Semantic entailment, correct grading, or zero hallucination |
| `src/rubric_agent/pipeline.py` | At most one validator-driven revision after the initial assessment | A new autonomous planning algorithm |
| `src/rubric_agent/review.py` | Accept/edit/reject states; pending criteria block export; AI suggestion and marker decision retained separately | Human review improves accuracy or saves time without observed marker sessions |

The existing B2 comparison changes context selection, prompting and validation together. It tests a complete system choice, not the isolated causal benefit of retrieval. The K=10 control changes evidence availability but still cannot separate every pipeline component. Zero uncited claims under the local heuristic is a structural result, not a semantic-grounding finding.

## Comparisons still needed before stronger claims

Use a shared dataset, rubric, backbone and decoding settings for direct whole-document grading, plain BM25-assisted grading without validation/repair, and the full system. An EFS-style extraction-then-scoring comparator is appropriate but must be labelled an adaptation unless the published protocol is faithfully reproduced. A no-repair control isolates the extra corrective call. Keep unrun comparisons out of results tables.

Do not copy QWK values from different papers into a leaderboard against our 62 pairs: their datasets, score ranges, annotators and models differ. Independently annotate evidence support and scores; add a second annotator before claiming human-level agreement. For RULERS calibration, use a separate calibration split and report it. For any prompt-injection claim, collect benign/perturbed paired results rather than inferring robustness from JSON validity — **this one is now done**: predeclared in `EVALUATION_PROTOCOL.md` Addendum A.2 and measured in `docs/robustness/`, with the benign twin as the comparison rather than an inference from valid JSON.

Commercial tools and miscellaneous repositories can provide workflow context, but they do not replace these close scientific comparators. No claim that another tool lacks a feature is made from an absent README mention.

## RAG-assisted grading comparison

Chu, Y., He, P., Li, H., Han, H., Yang, K., Xue, Y., Li, T., Krajcik, J., & Tang, J. (2025). *Enhancing LLM-Based Short Answer Grading with Retrieval-Augmented Generation*. [Primary arXiv record](https://arxiv.org/abs/2504.05276), first submitted 7 April 2025, v2 revised 3 June 2025; record identifies an EDM 2025 short paper. Checked 4 October 2026. The method retrieves educational domain information using question/answer context; our corpus is the submitted document itself. We do not transplant its reported improvement to our data.

Current B3 (`--evidence-mode full_context`) is implemented with identical criterion prompts, citation requirements, validation and repair budget. It selects every original evidence unit in document order. Single-case local checks are in `validation/README.md`; full independent comparisons remain pending.
