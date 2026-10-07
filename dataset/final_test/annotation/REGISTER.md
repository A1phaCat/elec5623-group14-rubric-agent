# Final-test annotation register

**Status: not started. No pair has been labelled.** The two sheets in this
directory are blank templates, and `tests/test_annotation_workflow.py` asserts
they stay blank until real people fill them in. `dataset/final_test/labels.json`
does not exist yet, so a campaign on this corpus refuses to run.

This file is the record of who annotated what and when. Fill it in as the work
happens; do not pre-fill it.

| Sheet | Annotator (full name) | Date started | Date finished | Saw model output or dev labels first? |
|---|---|---|---|---|
| `annotator_A.csv` | | | | |
| `annotator_B.csv` | | | | |
| `adjudicated.csv` | both, after agreement.json was saved | | | n/a |

## What has to happen, in this order

The order matters: agreement computed after a discussion is not inter-annotator
agreement.

1. **Freeze first.** Code and prompts are frozen at tag `v1.0.0-frozen`. Do not
   change a prompt or the retriever after annotation begins; that would make
   these labels a tuning target.
2. **Two people label independently.** 27 pairs each, from the sheets in this
   directory. Neither looks at model output, at the other's sheet, or at
   `dataset/labels.json` / `labels_v2.json`. Read
   `INSTRUCTIONS.txt` once before starting and do not reinterpret it mid-sheet.
   Expect roughly 60–90 minutes: six documents, four or five criteria each.
3. **Save both originals unchanged and compute agreement before discussing
   anything.**

   ```sh
   .venv/bin/python scripts/adjudicate_annotations.py agreement
   ```

   This writes `agreement.json` with Cohen's kappa, raw agreement, the
   three-class confusion matrix, score MAE on jointly scored pairs, and every
   disagreement with both rationales. It also hashes both sheets. Commit this
   file before step 4.
4. **Adjudicate.** Now discuss the disagreements. Copy one sheet to
   `adjudicated.csv` and edit it to the agreed answer, keeping both originals
   untouched. Record in the table above who was present.
5. **Build the labels.**

   ```sh
   .venv/bin/python scripts/adjudicate_annotations.py build --adjudicated dataset/final_test/annotation/adjudicated.csv
   ```

   This writes `dataset/final_test/labels.json` plus
   `labels_provenance.json`, which carries the hashes of both originals and the
   adjudicated sheet so a report can prove which labels produced its numbers.
6. **Run the frozen campaign** (`docs/EVALUATION_PROTOCOL.md`). After looking at
   final-test results, any change to the system is a new experiment and cannot
   be reported as this run.

## Two things to get right

**Sufficiency is not quality.** This is the single error the development corpus
made, and correcting it is documented in `dataset/LABELS_V2_CHANGES.md`. A
section that plainly states its own gap ("risks are not discussed") is
*sufficient* evidence for a *low* score. Reserve `partial` for evidence that
points at content you cannot see.

**`f02` and `f05` exist to give `partial` a denominator.** They are the
dispersed/partially-missing documents, with appendices referenced but not
supplied and a diagram placeholder. On the development corpus `partial` ended
up with one gold pair, which made macro-F1 rest a third of its value on a
single judgement (`docs/tuning/README.md`). If `partial` is genuinely the right
answer somewhere, it is most likely here. Do not force it, and do not avoid it.

## Independence limit, to be reported as written

The six documents were authored with AI assistance inside this project
(`dataset/final_test/corpus.json`). The team has therefore seen this material
before, and these are not labels from an outside expert on real student work.
If a project member is one of the two annotators, the report must say so and
state that the sheet was completed after the freeze and before any final-test
model output existed. Precise disclosure is the claim; independence from the
development team is not.

`must_contain` is left empty by the build step, so M3 retrieval relevance is
**unmeasured** on this corpus and must be reported that way rather than
inherited from the development corpus.
