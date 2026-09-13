# Reading the evaluation results (13 Sep 2026)

`docs/EVALUATION.md` (fixture) and `docs/EVALUATION_live_qwen7b.md` (local
Qwen2.5-7B-Instruct via Ollama, temperature 0, prompt `assessment_v2`, k=5,
2 repeats) are generated files. This note is the human reading of them, written
the same day, so the group knows what the numbers do and do not say before the
Week 11–12 evaluation campaign.

## 1. What a real model changed

| Metric | Fixture | Qwen 7B (agent) | Qwen 7B (B2 one-shot) | Target |
|---|---|---|---|---|
| M4 sufficiency macro-F1 | 0.405 | **0.554** | — (accuracy 0.758) | ≥ 0.75 |
| M4 sufficiency accuracy | 0.484 | 0.613 | 0.758 | — |
| M8 QWK (score agreement) | 0.179 | **0.477** | **0.868** | report |
| M8 MAE (marks) | 0.93 | 0.64 | 0.16 | report |
| M6 unsupported-claim rate | 0.000 | **0.000** | **1.000** (45/45) | ≤ 0.05 |
| M5 citation exists / supports (proxy) | 1.00 / — | 1.00 / 0.94 | n/a | ≥ 0.95 |
| M12 repeatability | 1.000 | 0.968 | — | ≥ 0.90 |
| M13 median latency, 12-page case | ~0 s | 46 s / 51 s | — | ≤ 120 s |
| Corrective round needed | n/a | 11.3 % of calls (7 first-attempt `uncited_claim`, 1 left) | — | — |

Twelve of thirteen targets are met with the local model. The one that is not,
M4, is the interesting one.

## 2. The finding: the agent is more conservative than both the labels and B2

Confusion on the 62 pairs (gold → agent): sufficient→sufficient 26,
**sufficient→partial 13**, sufficient→insufficient 2, partial→partial 5,
**partial→insufficient 7**, partial→sufficient 1, insufficient→insufficient 7,
insufficient→partial 1. Almost every error is one step *down*.

B2 — the same model, whole document and whole rubric in one call — agrees with
the labels better (QWK 0.87 vs 0.48) while having **no traceable claim at all**
(45/45 positive claims without an evidence pointer, which is what the product is
built to prevent).

Three explanations, not mutually exclusive:

1. **Synthetic labels are lenient.** The corpus was written and labelled by one
   person in one pass; a sentence that *names* the descriptor was labelled as
   meeting it. The model, told to "judge only what the evidence shows", reads
   `s1_standard` C4 ("the discussion notes that scores remain provisional") as
   *results without interpretation* (2/4) — a defensible reading; the label
   says 4/4. B2 is more generous and therefore closer to the lenient labels.
   This is exactly why proposal §8.1 requires a second annotator and an
   agreement statistic before the numbers are quoted.
2. **`sufficiency` means two things.** The labelling guide defines it as evidence
   adequacy ("the span lets a marker score without hunting further"), but the
   generator assigned it by quality level (strong text = sufficient, weak =
   partial). The prompt follows the guide, so "partial evidence about a weak
   section" and "sufficient evidence of a weak section" collapse differently on
   the two sides. Action: the annotation round must label sufficiency and
   score independently, and the guide gets one worked example of *sufficient
   evidence, low score*.
3. **The evidence-only instruction makes a 7B model cautious.** Rule 5 of the
   prompt forbids assuming the rest of the document says more. On 6–12 page
   synthetic documents where k=5 already covers most units, that caution costs
   agreement without buying anything. A discriminating run with k=10 (every
   unit visible) is recorded below; if agreement rises to B2 levels the cost
   is retrieval coverage, if not it is the prompt/labels.

## 3. What this means for the product claim

The proposal's hypothesis is two-part: the agent should (a) make every judgement
traceable and (b) stay comparable to direct grading on agreement. On this
corpus and model, (a) holds completely (M5 1.00, M6 0.00 vs 1.00) and (b) does
not yet (QWK 0.48 vs 0.87). The honest statement for the presentation is:

> With a 7B local model, evidence-constrained marking removes untraceable claims
> entirely at the cost of lower agreement with our single-annotator labels; the
> one-shot grader agrees better but cannot be checked. Whether the agreement gap
> is real or a labelling artefact is what the two-annotator round in Week 11
> decides.

Things that would be *wrong* to do: tune the prompt until the synthetic labels
are matched (that is fitting to one person's guesses), or loosen the validator.

## 4. Discriminating run: k=10, repeats=1, no baseline

With k=10 every unit of every synthetic document is in the evidence set, so the
agent sees exactly what B2 sees, only chunked and with IDs. Result (same model,
same prompt): **M4 macro-F1 0.554, accuracy 0.613, QWK 0.483, MAE 0.70** —
indistinguishable from k=5 (0.554 / 0.613 / 0.477 / 0.64). M6 stays 0.000 and
the corrective round rate stays 11.3 %.

So the agreement gap is **not** retrieval coverage. It is the combination of
the evidence-only instruction and the way the first-pass labels were written
(explanations 1 and 2 above). That is good news for the architecture — the
retriever is not losing evidence — and it points the Week 11 effort at the
labels and at the sufficiency definition rather than at the search component.
Hybrid re-ranking stays de-scoped (proposal §10.3).

## 5. Smaller observations

- **Validator ↔ model loop works.** 7 first attempts failed the citation rule; 6
  were fixed by the single corrective round, 1 stayed rejected (no score, marker
  sees the warning). Before the claim-rule refinement in 0.3.0 the first run
  rejected 19 first attempts, mostly for sentences such as "this aligns with the
  descriptor for 4.0" — a judgement, not a claim about content. Counting those as
  unsupported claims was a measurement error, now fixed and unit-tested.
- **B2 needed a robust parser.** The first live B2 run returned one criterion
  object instead of five and every record was rejected, which made "B2 unsupported
  rate 0.00 (0/0)" look like a win. It was a parsing failure. `_direct_items`
  now accepts the shapes one-shot graders return, with one re-ask.
- **Latency.** 46 s median per 5-criterion submission on an M2 Pro (≈ 8–10 s per
  call, more with a corrective round). Within NFR3 on the corpus, but the real
  16-page proposal with six criteria and three corrective rounds took **126 s**
  in the UI — just over the 120 s target for 10–20 pages. Options, in order:
  run the six criteria concurrently (`OLLAMA_NUM_PARALLEL`), cap `max_tokens`
  lower for the revision call, or a smaller/faster model for the sufficiency
  step. The demo should pre-run the real case and show progress per criterion.
- **Real PDF.** Our proposal PDF exposed that PDF extraction loses paragraph
  breaks; before the chunker fix each page was one 300–450-word unit with the
  section "body". After the fix: 66 units, median 83 words, every unit with a
  real heading. Retrieval on the official rubric then lands where a marker would
  look (R5 → milestones, responsibility areas, feasibility).
