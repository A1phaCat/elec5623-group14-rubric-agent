# AI-Assisted Rubric Marking Agent

ELEC5623 Group 14 · Track A · Project Development draft  
Status: draft for the group to revise before the 3 November 2026 submission.  
Revised 4 October 2026 against the A2 rubric and supplied proposal feedback. Historical model-quality numbers are dated separately from current regression and smoke checks. Independent annotation and marker studies remain incomplete.  
Draft aid, 2026-10-04: Haolin Jin's proposal comments (6.5/10) are mapped to sections in `docs/MARKER_RESPONSE.md`. That note is not part of the submitted page count.

Group: Zongjian Li, Zhengyu Han, Yuchun Zheng, Yutong Liu, Zhaoxinyi Zhou.  
Tutor approval: Linghan Huang, 6 September 2026. The approved problem, users and product direction are unchanged.

## 1. Project summary

We built a decision-support agent that helps a marker review a long submission one rubric criterion at a time. It parses the rubric and the document, retrieves a few evidence spans, asks a model for a provisional score that must cite those spans, checks the answer, and lets the marker accept, edit or reject it. It does not submit a grade.

The historical local Qwen2.5-7B-Instruct run on 62 synthetic labelled pairs achieved sufficiency macro-F1 0.554, below the predeclared 0.75 target. Its surviving positive statements had citations under a heuristic detector. This shows a traceable workflow, not semantic correctness. A direct whole-document baseline agreed more often with the single-annotator sufficiency labels (accuracy 0.758 versus 0.613), but was not instructed to cite. We therefore separate citation-format compliance from grading quality and implement a same-prompt full-context comparison to test the retrieval choice more fairly.

## 2. Problem definition

University markers score long reports against analytic rubrics. The criteria are written down, but the relevant sentences are scattered. Two markers can attend to different passages. A general chatbot can score the document, and then nobody can check which passage the score used.

Primary user: a marker or tutor. The unit coordinator needs a record that can be audited. Students are affected because a provisional suggestion must stay reviewable. The prototype scope is one rubric and one text submission per session, public or synthetic or de-identified material, and a human confirmation before any export. Handwriting, images and writing a grade into an LMS are out of scope.

Success, as implemented and measured:

- Positive claims identified by the deterministic heuristic must cite allowed evidence ids; explicit cited quotes must occur in the cited unit. This does not establish entailment.
- Scores stay inside the criterion's allowed range.
- A marker can override the suggestion, and the suggestion is still stored.
- Fixed controls are direct-grading B2 and full-context-with-citations B3. Independent human scores and marker-time measurements remain required; oversight alone is not a measured manual baseline.

## 3. Related work and novelty

Evidence-first scoring, deterministic verification and retrieval-augmented generation are established work. Our contribution is an implemented marker-support workflow for long submissions and a limited, reproducible engineering study. The closest methods are compared below; their experiments have not been reproduced on our data.

| Closest work | Established method and overlap | Our implementation and remaining boundary |
|---|---|---|
| Evidence-First Scoring (EFS), Cai (2026) | Criterion-specific evidence extraction precedes scoring from the evidence and rubric; EFS is a method within a prompt-injection paper, not a separate paper title | We retrieve chunks using BM25 and present them for human review. This separation is prior work; our implementation has no measured prompt-injection guarantee |
| GradeAgentOps, Anghel et al. (2026) | Grading contracts, deterministic verification, bounded repair, optional memory and provenance; evaluated on 1,000 short answers with two expert graders | Validation and revision overlap directly. We focus on a long-submission review workflow and lack an equivalent independent expert study |
| RULERS, Hong et al. (2026a) | Locked rubric specifications, evidence verification and post-hoc score calibration | We parse rubric descriptors and provide provisional scores without learned calibration. Checking citations or keeping logs is not a unique contribution |
| RAG-assisted short-answer grading, Chu et al. (2025) | Retrieves domain knowledge using the question and answer context | We retrieve evidence within the submitted document, rather than external subject knowledge; both are retrieval-assisted grading |

RULERS v1 is dated 13 January 2026, before our proposal. Its v3, dated 9 September, changes the title to *From Rubrics to Reliable Scores: Evidence-Grounded Text Evaluation with LLM Judges* (Hong et al., 2026b); this is a revision of the same work. Publication versions and primary-source links are recorded in `docs/RELATED_WORK.md`.

Lewis et al. (2020) provide the general retrieval-augmented generation framework. BM25 is our transparent lexical baseline (Robertson and Zaragoza, 2009), not a new retrieval algorithm. Liu et al. (2024) motivate testing whether information remains usable in a long context; they do not prove that K=5 improves our grading. Gao et al. (2023) distinguish citation quality from answer quality. Accordingly, a valid evidence id or recoverable quote does not prove semantic support. Our heuristic claim and substring checks require independent human assessment for that stronger conclusion.

The defensible contribution is the integration of criterion-wise retrieval, local-model suggestions, bounded correction and an accept/edit/reject workflow with separate AI and human values. Its value is tested through traceability, agreement, abstention and usability evidence. B2 compares the whole workflow against direct scoring; B3 holds the prompt, citation rules and validator fixed while changing context selection. These are engineering controls, not demonstrations of superiority over the named papers. A plain-RAG/no-repair ablation and independent marker studies would isolate further benefits. No time-saving or human-level agreement claim is currently supported.

Commercial tools provide workflow context, but do not replace the closest research comparison. Earlier exploratory repository notes are preserved separately as historical background; unverified claims that competitors lack a feature are excluded from this report.

## 4. System design

```text
Marker
  → Streamlit UI
      → parse rubric and submission
      → chunk into evidence units with page and section
      → BM25, top 5, per criterion
      → model gateway (one criterion + those units)
      → validator, then at most one revision
      → marker accept / edit / reject
      → JSON and CSV export, plus an append-only run log
```

Deterministic code covers parsing, chunking, retrieval, validation, review state and the log. The model is behind one interface: an offline fixture for tests, a local Ollama model, or an OpenAI-compatible endpoint such as Azure when environment variables are set. The diagram in `docs/ARCHITECTURE.md` matches this code.

The default BM25 path sends the retrieved units. B3 deliberately sends every indexed unit in document order through the same criterion prompt and validator. B2 uses the full document, truncated at 48,000 characters. Nothing in the repository writes a mark to Canvas or an LMS.

## 5. GenAI and agent component

Fixed next-evaluation configuration: local `qwen2.5:7b-instruct` via Ollama, temperature 0, maximum 700 output tokens, prompt `prompts/assessment_v4.md`, BM25 K=5 (`k1=1.5`, `b=0.75`). Keeping the historical model makes workflow changes easier to analyse; the prompt was selected in the dev-only window recorded in `docs/tuning/README.md` and frozen before the final-test annotation began. The model must judge only supplied evidence and produce schema-valid JSON. An invalid initial JSON response may be requested once more; the pipeline separately allows one validator-driven revision. These budgets permit up to three HTTP calls per criterion, not necessarily one call per run-log entry. See `docs/EVALUATION_PROTOCOL.md` for frozen metrics and controls.

Loop, for each criterion:

1. Retrieve. The query is the criterion name, repeated, plus the upper descriptors.
2. Assess. The model sees the criterion, the units, and the list of allowed ids.
3. Validate. Reject unknown ids, non-finite/out-of-range/off-grid scores, criterion mismatches, detected uncited factual claims, and quoted spans absent from their cited unit. Relevant checks cover explanations and feedback; they do not establish semantic support.
4. Revise once. The model sees its previous JSON and the validator's findings. The new answer is validated again. A second failure stays rejected.

That revision is the agent loop we actually run. It is not a general tool-calling harness. LangChain and MCP, as practised in Lab 7, fit a setting where the model must choose among external tools and the application checks the call before it runs. Here the "tools" are fixed steps the application always runs, and the model is not allowed to choose a write action. An extra orchestration or MCP layer has no demonstrated benefit for these fixed local steps. MCP can support read-only tools, but it is not required for this product. We keep the implemented pipeline and measure its behaviour.

Why a model at all: matching a descriptor to paraphrased student text is not a keyword rule. Why not only a model: the 7B baseline shows a fluent score can be untraceable. Retrieval, the id list and the validator are the ordinary software around that model.

## 6. What was implemented

Working in `rubric-marking-agent` (v0.3.0 plus dated working-tree improvements):

- Ingest of the rubric forms above, including the official proposal rubric transcribed from Canvas.
- PDF and text submissions. Our 16-page proposal becomes 66 units, median about 83 words, each with a section name. An earlier build treated each PDF page as one long block; that is fixed.
- Review UI with cited and uncited evidence, a side-by-side one-shot baseline, an evaluation page and a run-log page that can replay a logged call.
- A top-band checklist on each criterion. It lists which words from the full-marks descriptor appear in non-denying sentences. A sentence that says the text does not include metrics does not count as having metrics. It does not change the score.
- Quoted spans are checked in explanations and feedback; NaN/Infinity are rejected at schema and validator boundaries.
- Invalid AI suggestions cannot be accepted. A marker must explicitly edit with a valid rubric score or reject. Invalid UI edits reset the decision to pending and block export; valid overrides retain the original AI suggestion.
- B3 sends all indexed units through the same prompt, validator and correction budget; the selection method is logged and replayed.
- Tests and CI without a network or an API key. The fixture is a descriptor-matching stand-in. Its scores are not model evidence.

Reduced or omitted, on purpose:

- Dense or hybrid retrieval. The measured retriever is BM25 with k=5. On the labelled set, M3 Recall@5 is 0.992, which meets the 0.85 target. Embeddings are not in the measured system.
- A second corrective round. One revision is logged; a second failure stays insufficient.
- OCR, images, and any path that files a grade.
- Reordering evidence inside the prompt to avoid "lost in the middle". That would change the live system after the measured run, so it is recorded as a later experiment, not as a result.

The Week 13 demo script is `docs/DEMO_SCRIPT.md`. Screenshots in `docs/img/`
were captured on 7 October 2026 from the frozen build, so they show the system
the submitted source produces:

- `review_ui_live.png` — the real 16-page proposal against the official Canvas
  rubric with the local 7B model: 66 evidence units, six criteria in 98 s, two
  records repaired after validator feedback and two held as failing validation
  and unacceptable, every criterion still `pending`.
- `review_ui_evidence.png` — the evidence panel for one criterion, five units
  retrieved and five cited, each with page and section beside the explanation
  that cites it (FR7).
- `evaluation_page_frozen.png` — the Evaluation page on the frozen campaign,
  showing 11 of 12 automatic targets met and M4 marked below target rather than
  hidden.

## 7. Evaluation

### Fixed protocol and data

The scored corpus contains two labelled rubrics, 13 submissions and 62 criterion/submission pairs. A third half-mark rubric is a parser fixture. The synthetic texts and initial labels were AI-assisted, as disclosed in `AI_USE.md`; they are neither independently adjudicated labels nor real student performance. The 43-pair dev and 19-pair heldout splits are by submission, but both have been inspected. A confirmatory study requires a fresh untouched document split.

`docs/EVALUATION_PROTOCOL.md` fixes definitions, denominators and missing-data rules. The quality target is three-class sufficiency macro-F1 ≥0.75. Retrieval Recall@5 targets ≥0.85 on cases with annotated relevant evidence. Structural targets are ≥0.95 valid citation ids, ≤0.05 uncited-positive-sentence rate and 100% permitted scores. Boundary tests require zero unconfirmed exports. Report conditional normalised MAE and per-criterion QWK alongside numeric-score coverage and sample counts. Repeatability targets ≥0.90 over three runs; latency targets ≤120 seconds for the 10–20 page case. Human support and usability need independent observations.

The controls are B2, same-model one-shot grading, and B3, the same criterion prompt, citation rules, validator and correction budget with all indexed units instead of BM25 top five. B3 changes evidence selection and order. B2 is not asked to cite and cannot establish a factual-correctness advantage from citation counts. Neither control reproduces EFS, GradeAgentOps or RULERS. Current reports preserve code/prompt/input hashes, configuration, denominators and individual outputs.

### Current results: frozen campaign, local 7B, 7 October 2026

All three systems, one model, one set of inputs and labels, under the frozen
configuration in `docs/FREEZE.md`. 43 criterion pairs over 9 submissions and 2
rubrics, corrected labels `dataset/labels_v2.json`, three repeats for A and B3
and one for B2. Artifacts and per-call records are in
`docs/evaluation_dev_frozen/`; the reading below is `docs/EVALUATION_dev_frozen_notes.md`.

| | A (BM25 k=5) | B2 one-shot | B3 full context |
|---|---:|---:|---:|
| Sufficiency macro-F1 (target 0.75) | 0.439 | 0.434 | 0.401 |
| Sufficiency accuracy | **0.767** | 0.721 | 0.744 |
| Conditional normalised MAE | 0.222 | **0.050** | 0.318 |
| Numeric score coverage | **36/38** | 30/38 | 33/38 |
| False-insufficient pairs | **2** | 8 | 5 |
| Uncited positive claim rate | **0.000** | 1.000 | **0.000** |
| Repeatability, 3 runs | **1.000** | not measured | **1.000** |
| Median latency per submission | 33.1 s | 11.0 s | 41.0 s |

On the pairs where both systems emitted a number: A 0.219 against B3 0.313
(32 pairs), and A 0.259 against B2 0.034 (29 pairs).

Three results follow, and they do not all favour the product.

**Restricting evidence helps.** A and B3 differ only in context selection;
prompt, citation rules, validator and correction budget are identical. A is
better on score error, on false-insufficient decisions and on accuracy, and it
is faster. The clearest case is the keyword decoy `s4_decoy_eval` C3, where A
and B3 cite the *same* unit and B3 reads a sentence that announces itself as a
decoy as "Metrics listed without a procedure", scoring 2.0 where the reference
is `insufficient`. Per-submission accuracy there is A 1.000 against B3 0.400.
The extra context did not supply a better passage; it supplied confidence to
over-read the one already retrieved.

**The one-shot baseline agrees better on scores and cannot be audited.** B2's
conditional normalised MAE is 0.050 against A's 0.222, and on the jointly
scored subset 0.034 against 0.259. That is reported as a real result. B2 also
has no evidence pointer on any positive claim, abstains wrongly four times as
often as A, and produced nothing scorable on `p2_gaps`. B2 is not asked to
cite, so its uncited rate describes its output format rather than proving
hallucination; what it establishes is that a marker cannot check a B2 score.

**Two previously open targets now pass.** Repeatability is 1.000 over three
runs at temperature 0, where the September report measured 0.968 over two. The
median latency of 33.1 s meets NFR3's 120 s, against the 126 s serial UI run
that missed it.

M4 remains below target at 0.439 for a structural reason declared before the
run: corrected dev holds one `partial` pair, so a third of macro-F1 rests on a
single judgement, and A's F1 for `partial` is 0.000. macro-F1 therefore cannot
exceed 0.667 on this split regardless of the other classes. Per class, A scores
F1 0.873 on `sufficient` (support 37) and 0.444 on `insufficient` (support 5).
Accuracy, 0.767, describes the same 43 decisions without that distortion. M4 is
settled on `dataset/final_test/`, where `f02` and `f05` give `partial` a real
denominator.

Two limits belong with every number above. The dev split is the split the
prompt was selected on, so A's figures here are not an unbiased estimate. The
labels are the project's own corrected judgements rather than independent
ground truth.

### Historical results (local 7B, 13 September 2026)

| Metric | Agent, K=5 | B2 one-shot | K=10 control |
|---|---:|---:|---:|
| Sufficiency macro-F1 | 0.554 | Not in legacy table | 0.554 |
| Sufficiency accuracy | 0.613 | 0.758 | 0.613 |
| Legacy pooled QWK (superseded method) | 0.477 | 0.868 | 0.483 |
| Conditional MAE (raw marks) | 0.64 | 0.16 | 0.70 |
| Numeric-gold score coverage | 0.833 | Not in legacy table | Not recorded |
| Uncited positive sentences (heuristic) | 0.00 | 1.00 (45/45) | 0.00 |
| Repeatability, two runs | 0.968 | Not measured | Not measured |
| Median latency / 12-page case | 46.5 s / 50.6 s | Not measured | Not recorded |

Source: `EVALUATION_live_qwen7b.md` and the K=10 note. These are historical measurements under `assessment_v2`, superseded by the frozen campaign above and kept only to show what changed. The old QWK pooled incompatible rubric scales, and MAE excluded abstentions while mixing raw marks. The revised harness uses within-criterion QWK and normalised MAE, and reports coverage and jointly scored samples. Do not use historical QWK values to establish superiority. M4 missed its target. The K=10 control did not improve macro-F1, which weakens a retrieval-only explanation on this small corpus; it does not establish a general causal conclusion.

The historical real-PDF UI run took about 126 seconds on the serial build, above the 120-second target. Current code submits criterion calls concurrently, but the model server can still queue them. Current-build checks are reported separately in `docs/validation/README.md`; a smoke check does not replace the labelled campaign.

### Current-code verification (4 October 2026)

The final software suite passed 92 regression tests, including headless UI interactions. Offline A/B3 campaigns preserve the failed fixture macro-F1 target and are not model-quality results. The current local Qwen smoke run took 33.81 s for the decoy BM25 path, 38.29 s for the same-prompt full-context B3 path, and 61.85 s for the 16-page own-proposal PDF. The PDF yielded five valid provisional scores and one citation-rule rejection; the rejected score remains null. Each condition ran once, so these timings do not establish a speed-up, repeatability or general quality. The final run's source hashes match the current implementation. Full records and limitations are in `docs/validation/README.md`.

### Failure analysis and unmeasured outcomes

Three traces from the frozen campaign, one per scenario the protocol requires.
Each shows the retrieved span, the output and the reference; reproduce any of
them with `scripts/extract_traces.py`.

**Decoy, `s4_decoy_eval` C3.** The only retrieved unit is *"We mention
evaluation only as a keyword without specifying metrics or a baseline. This
sentence is a decoy and does not include Recall@5, labelled data, or test
scenarios."* Reference `insufficient`. A answered `insufficient`, citing
`E-004`. B3, given the whole document, cited the same unit and answered
`sufficient` 2.0. The failure is interpretive, not retrieval.

**Dispersed, `s2_dispersed` C1.** Two relevant sentences sit on pages 1 and 7
with four pages of deliberate filler between them. A retrieved and cited both
(`E-001` Opening, `E-007` Users), then judged `partial` 2.0 against a reference
of `sufficient` 4.0. Retrieval succeeded and the descriptor judgement differed:
M3 Recall@5 is 1.000 across the corpus, so finding evidence is not the
bottleneck.

**Ordinary but hardest, `s8_missing_method`.** A's worst document at 0.200
accuracy. For C1 the submission says only *"The scoped marking-workload gap is
unverifiable provisional scores."* The 4-mark descriptor requires a problem
"scoped with affected users and a testable gap"; the 2-mark descriptor is
"stated but not scoped". The reference says `sufficient` 4.0, and all three
systems independently declined to award 4: A `partial` 2.0, B3 `sufficient`
2.0, B2 `insufficient`. The same pattern recurs on C3.

We read that as a doubtful reference label rather than a system failure, and we
deliberately did not change it. Editing a label after seeing model output is
fitting the target to the predictions, which is the error this project already
corrected once (`dataset/LABELS_V2_CHANGES.md`). The observation stands as a
further reason the conclusions wait for independently annotated data.

Of A's 43 decisions, 10 are wrong and 6 of those are one step below the
reference, so the conservative bias is reduced from the September build but not
eliminated. The corrective round was used on 11.6% of calls and two records
finished carrying a feedback-citation warning, which a marker sees.

- Decoy wording can appear relevant to retrieval while lacking actual criterion content. Keep the retrieved passage and output together in the failure trace.
- Seven historical first attempts failed the citation rule; six were repaired by one revision and one remained rejected. This demonstrates bounded correction on those cases, not semantic correctness.
- The initial B2 parser lost criteria, making a zero-denominator uncited rate look successful. Current empty denominators are `n/a`, and missing outputs remain visible.
- The 4 October review found that invalid AI suggestions could be accepted and invalid UI edits could retain an earlier confirmation. Both are fixed with regression tests; the output boundary now revalidates human decisions.
- No inter-annotator agreement or marker stopwatch results exist. These requirements remain unmeasured.

M6=0 means no uncited sentence among the detector's surviving positive statements. Rejected outputs and unrecognised claims limit that measure. An existing citation or exact quote does not prove a judgement correct. Apparent agreement can also reflect the AI-assisted synthetic corpus and lenient first labels.

## 8. Reflection and next steps

The useful engineering result is an inspectable workflow: source locations, provisional judgements, explicit validation failures and separate human decisions. Evidence-first scoring and repair are prior work; the project must earn its contribution through reliable integration and measured behaviour on the stated use case.

The main unresolved problem is evaluation validity. The first labels sometimes conflate weak writing with insufficient evidence. Independently label sufficiency and quality, preserve disagreements, then adjudicate. A well-documented weak section can have sufficient evidence and a low score. Changing prompts to fit the old labels would not resolve this issue.

Next, complete two independent annotation passes, run A/B2/B3 with frozen inputs and manifests, and conduct 2–3 marker sessions. Report at least three actual traces covering ordinary, dispersed/missing and decoy cases. Compare quality together with abstentions and timing. Concurrent calls can change runtime behaviour; measure rather than assume stable scores or lower latency. Claims about calibration, prompt-injection robustness or time savings remain outside the demonstrated evidence.

## 9. Responsible use

The real course document used in the demo is the group's own proposal, with the cover removed. The synthetic corpus was AI-assisted and its labels remain preliminary. Public repository excerpts exist as exploratory inputs but are not part of the 62-pair benchmark. The reported model run was local, so submission text did not leave the machine. A hosted endpoint is possible and is not the source of the numbers above. Uploading another student's work to a hosted model is not part of this prototype.

The misuse we designed against is an autonomous grade. Export is blocked while any criterion is undecided, and there is no code path that files a mark. A convincing explanation can still be wrong about quality. That is why the marker's value replaces the suggestion and the suggestion is kept for audit. Bias in descriptors and in the single annotator is unmeasured until the second labelling pass.

## 10. Team contributions and references

This named allocation is proposed for team confirmation, not an assertion of completed work. The user selected Zhengyu Han to lead the core system and evaluation. Before submission every member must attach reviewed code, experiment or document evidence using `docs/TEAM_DELIVERY.md`.

| Member | Proposed substantive responsibility | Completion evidence |
|---|---|---|
| Zongjian Li | A1: rubric parser/schema, problem definition and closest-work/reference audit | Pending confirmation and evidence |
| **Zhengyu Han** | **A4 and technical lead: model/prompt/validator/corrective loop; evaluation design and interpretation; report §§5, 7–8** | Role selected by user; implementation review and experiment ownership to be attested |
| Yuchun Zheng | A2: PDF ingestion, provenance, export, blinded annotation coordination | Pending confirmation and evidence |
| Yutong Liu | A3: retrieval/logging, frozen experiment execution and reproducibility checks | Pending confirmation and evidence |
| Zhaoxinyi Zhou | A5: review UI, marker study and demo workflow | Pending confirmation and evidence |

Generative AI was used to draft repository code, tests, this draft and the evaluation harness, as recorded in `AI_USE.md`. The group remains responsible for the design, the citations and every number that is submitted. The live metrics were produced by running the local model on the dataset in this repository, not by asking a model to invent them.

### References

Cai (2026), Anghel et al. (2026), Hong et al. (2026a, 2026b) and Chu et al. (2025) were opened on 4 October 2026. The other entries were already in this draft and were not re-opened that day.

Anghel, C., Anghel, A. A., Craciun, M. V., Cocu, A., Vulpe, D.-E., Andrei, C. A., Maier, C., Scheau, C., Dragosloveanu, S., & Cergan, R. (2026). GradeAgentOps: A verification-first framework for evidence-anchored LLM exam grading. *AI, 7*(6), 198. https://doi.org/10.3390/ai7060198

Bloxham, S., den-Outer, B., Hudson, J., & Price, M. (2016). Let's stop the pretence of consistent marking: Exploring the multiple limitations of assessment criteria. *Assessment & Evaluation in Higher Education, 41*(3), 466–481. https://doi.org/10.1080/02602938.2015.1024607

Brookhart, S. M. (2013). *How to create and use rubrics for formative assessment and grading*. ASCD.

Cai, Y. (2026). Prompt injection attacks on educational large language models for higher and vocational education. *Scientific Reports, 16*, 15594. https://doi.org/10.1038/s41598-026-46563-1

Chu, Y., He, P., Li, H., Han, H., Yang, K., Xue, Y., Li, T., Krajcik, J., & Tang, J. (2025). *Enhancing LLM-based short answer grading with retrieval-augmented generation* (arXiv:2504.05276). https://doi.org/10.48550/arXiv.2504.05276

Gao, T., Yen, H., Yu, J., & Chen, D. (2023). Enabling large language models to generate text with citations. In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing* (pp. 6465–6488). Association for Computational Linguistics. https://doi.org/10.18653/v1/2023.emnlp-main.398

Gradescope. (2025). *AI-assisted grading and answer groups*. Gradescope Guides. Retrieved September 12, 2026, from https://guides.gradescope.com/hc/en-us/articles/24838908062093-AI-assisted-grading-and-answer-groups

Hong, Y., Yao, H., Shen, B., Xu, W., Wei, H., & Dong, Y. (2026a). *RULERS: Locked rubrics and evidence-anchored scoring for robust LLM evaluation* (arXiv:2601.08654, version 1, 13 January 2026). https://arxiv.org/abs/2601.08654v1

Hong, Y., Yao, H., Shen, B., Xu, W., Wei, H., & Dong, Y. (2026b). *From rubrics to reliable scores: Evidence-grounded text evaluation with LLM judges* (arXiv:2601.08654, version 3, 9 September 2026). https://arxiv.org/abs/2601.08654v3

Jonsson, A., & Svingby, G. (2007). The use of scoring rubrics: Reliability, validity and educational consequences. *Educational Research Review, 2*(2), 130–144. https://doi.org/10.1016/j.edurev.2007.05.002

Karpukhin, V., Oğuz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W. (2020). Dense passage retrieval for open-domain question answering. In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing* (pp. 6769–6781). Association for Computational Linguistics.

Lee, G.-G., Latif, E., Wu, X., Liu, N., & Zhai, X. (2024). Applying large language models and chain-of-thought for automatic scoring. *Computers and Education: Artificial Intelligence, 6*, 100213. https://doi.org/10.1016/j.caeai.2024.100213

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*, 9459–9474.

Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024). Lost in the middle: How language models use long contexts. *Transactions of the Association for Computational Linguistics, 12*, 157–173.

Min, S., Krishna, K., Lyu, X., Lewis, M., Yih, W.-t., Koh, P. W., Iyyer, M., Zettlemoyer, L., & Hajishirzi, H. (2023). FActScore: Fine-grained atomic evaluation of factual precision in long form text generation. In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing* (pp. 12076–12100). Association for Computational Linguistics. https://doi.org/10.18653/v1/2023.emnlp-main.741

Robertson, S., & Zaragoza, H. (2009). The probabilistic relevance framework: BM25 and beyond. *Foundations and Trends in Information Retrieval, 3*(4), 333–389. https://doi.org/10.1561/1500000019

Turnitin. (n.d.). *Grading with rubrics and grading forms*. Turnitin Guides. Retrieved September 12, 2026, from https://guides.turnitin.com/hc/en-us/articles/35739418092941--New-Grading-with-rubrics-and-grading-forms

Zhang, D.-W., Boey, M., Tan, Y. Y., & Jia, A. H. S. (2024). Evaluating large language models for criterion-based grading from agreement to consistency. *npj Science of Learning, 9*, 79. https://doi.org/10.1038/s41539-024-00291-1
