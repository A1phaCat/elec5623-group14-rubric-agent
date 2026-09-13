# Governance, safety and limitations

## Human oversight (C1, NFR5)

* The system produces *provisional* criterion suggestions. There is no code path that records a grade anywhere.
* Export of a review record is refused while any criterion is `pending`. Accepted, edited and rejected decisions carry a UTC timestamp.
* Marker values override AI values in the export; the AI suggestion is kept in the same row so later analysis (M9) is possible.

## Privacy and data (C3, NFR6)

* `dataset/` is synthetic and group-authored. No student work is in this repository.
* The live gateway is opt-in: it is only offered in the UI when `RMA_MODEL_ENDPOINT` and `RMA_MODEL` are set, and it never appears in tests or CI.
* Before any real or de-identified submission is sent to a hosted model the group needs: tutor confirmation of the model provider, a written data-handling note, and de-identification of the file. Until then use the local-model option (Ollama) or the fixture.
* Uploaded files in the UI are written under `data/` (git-ignored) only when a PDF has to be read from disk; nothing is uploaded anywhere else.

## Secrets

* Keys are read from `RMA_MODEL_API_KEY` once, sent only in the request header, never printed, never written to the run log. `gateway.name` contains model and host only.
* The Azure key from Lab 1 stays in Azure/Foundry (course rule). Configure it through the environment on the machine that runs the demo; do not paste it into code, notebooks or chat.

Example (Azure AI Foundry):

```bash
export RMA_GATEWAY=live
export RMA_MODEL_ENDPOINT="https://<resource>.openai.azure.com/openai/deployments/<deployment>"
export RMA_MODEL="<deployment>"
export RMA_MODEL_API_KEY="<key>"
export RMA_API_KEY_HEADER=api-key
export RMA_API_VERSION=2024-10-21
rma demo --submission s4_decoy_eval
```

Example (local Ollama, no key):

```bash
export RMA_GATEWAY=live RMA_MODEL_ENDPOINT=http://localhost:11434/v1 RMA_MODEL=llama3.1:8b
```

## Model output is untrusted input (Lab 6 §6, §10)

* Every model response is parsed strictly against Listing 6.1; anything else is rejected with `invalid_model_output`.
* A transport failure produces an explicit `provider_error`, never a fabricated score.
* The validator checks the content, not just the shape: evidence IDs must exist in the retrieved set, scores must be on the rubric grid, and every positive sentence must carry a citation.
* Prompts are versioned files; the version is in every log line so a prompt change is auditable.

## Known limitations

1. **The fixture is not a model.** Numbers in `docs/EVALUATION.md` produced with `fixture-*` show that the harness works; M4 (sufficiency agreement) and M8 (score agreement) are expected to be poor with the fixture and must be re-measured with a real model.
2. **Text-only.** Scanned PDFs, images, tables rendered as images and handwriting are out of scope (C4).
3. **Lexical retrieval.** BM25 can miss paraphrased evidence; the S4 decoy defence relies on the assessment step, not retrieval.
4. **Small labelled set.** 62 pairs, one annotator pass, phrase-based relevance. The annotation round with two labellers and agreement statistics (proposal §8.1) is still to do.
5. **Human metrics missing.** M9–M11, M14 require marker sessions.
6. **English only.** Tokenisation and negation cues are English.

## Risk register (from proposal Table 9.1, status)

| Risk | Mitigation in code | Status |
|---|---|---|
| Hallucinated evidence | validator rejects unknown IDs and uncited claims | done, tested |
| Over-trust in AI score | scores shown as "suggested", export gate, marker override | done, tested |
| Model/API unavailable | fixture gateway; local model option; fail-closed errors | done |
| Privacy breach | synthetic data, opt-in live gateway, key only in env | done; approval process pending |
| PDF extraction failure | explicit `SubmissionParseError`; text-PDF only | done |
| Schedule slip | de-scoping order §10.3 (FR14 → re-ranking → UI polish → dataset size) | tracked in STATUS.md |

## AI use disclosure

See `AI_USE.md`. Claude in Cursor drafted this repository from the approved proposal; the group reviews, runs and owns the result. Any Canvas submission must include this disclosure.
