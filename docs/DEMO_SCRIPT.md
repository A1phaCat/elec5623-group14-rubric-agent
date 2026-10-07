# Week 13 rehearsal and Q&A preparation

Updated 4 October 2026. This is an internal **8-minute rehearsal**, not a verified
presentation-duration requirement. Check the final Canvas brief. The live
assessed presentation and Q&A prohibit AI; this preparation material is for beforehand.

## Prepare

```sh
.venv/bin/python -m pytest -q
# If no local Ollama server is running:
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_CONTEXT_LENGTH=16384 ollama serve
# In another terminal:
.venv/bin/streamlit run app/streamlit_app.py
```

Pre-run the real PDF and keep the current results. Show rejected criteria openly.
If the model is unavailable, label the fixture explicitly as an offline software
demonstration. Existing screenshots from September are historical, not proof
that the current model passed. Current run evidence is in `validation/README.md`.

## Proposed presentation split

| Time | Member | Show and explain |
|---|---|---|
| 0–1 | Zongjian Li | The marker's problem, preserved requirements and how the three closest papers overlap; no evidence-first invention claim |
| 1–2 | Yuchun Zheng | Rubric/PDF parsing, page/section evidence locations and provenance |
| 2–4 | **Zhengyu Han** | Criterion prompt, local model, structured output, quote/range checks, one corrective loop; show a real rejection and explain why it remains unscored |
| 4–5 | Yutong Liu | A/B2/B3 controls, data/code hashes and reproducibility; show actual data, not anticipated numbers |
| 5–6.5 | Zhaoxinyi Zhou | Accept/edit/reject; invalid edit blocks export; marker override and original AI score in separate export columns |
| 6.5–8 | **Zhengyu Han** | Results with denominators/coverage, unmet F1 target, what independent labels and user studies can establish, limitations |

Assignments are proposals except the user's choice of Han as technical/evaluation
lead. Match final contribution claims to reviewed artifacts.

## Questions Han should be able to answer

**What is new if EFS, GradeAgentOps and RULERS already exist?**
We do not claim new evidence-first scoring or repair. We implement and evaluate
a particular long-submission marker workflow. Its contribution needs working
integration and honest results, not an unsupported first-of-its-kind claim.

**Why use a model?**
The model interprets paraphrased evidence against a rubric. Deterministic code
handles extraction, retrieval, schema/range/citation checks and human decisions.
BM25 alone cannot judge the quality of the writing.

**Why B3 as well as B2?**
B2 changes prompting and output rules along with context. B3 keeps the criterion
prompt, citation rules, validator and correction budget, and changes evidence
selection/order. It is a fairer retrieval ablation, not a reproduction of a paper.

**Does zero M6 prove no hallucinations?**
No. It means zero uncited sentences among the heuristic's detected surviving
positive claims. An irrelevant citation can exist. Semantic support needs
independent human checks, and abstentions must remain visible.

**Why does MAE need coverage?**
MAE uses numeric predictions. A system can abstain on difficult cases and look
accurate on the remainder. Show scored/reference counts, coverage and a shared
scored subset; report different rubric scales separately or normalise error.

**How many retries and what is logged?**
The initial schema parse can retry once; then the validator can ask for one
revision. That allows at most three HTTP calls per criterion. JSONL records a
criterion result, attempt count and first validation warnings, not every raw
HTTP response. Evaluation JSON saves all repeat outputs with manifests.

**Why local Qwen 7B?**
It is an available fixed candidate, needs no API key and keeps the checked
inputs on the machine. It is not selected because we have proved it best.
Changing model or prompt requires a separate measured run.

**What did AI assistance do, and what did you do?**
Disclose assistance using `AI_USE.md`, then point to code you reviewed, tests you
understand, experiments you executed and analysis you can defend. Do not say
all members reviewed work unless they actually did.
