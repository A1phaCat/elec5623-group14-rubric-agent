# Dev-split sufficiency correction — labels.json to labels_v2.json

Reviewed 7 October 2026. Rebuild with `.venv/bin/python scripts/build_labels_v2.py`;
that script holds the declared corrections and refuses to run if any of them no
longer matches the source file.

`dataset/labels.json` is unchanged and remains the file used by every report
dated 13 September and 4 October. `labels_v2.json` is a separate file.

## Why

`LABELLING_GUIDE.md` rule 4 requires sufficiency and score to be labelled
independently. Sufficiency asks whether the text lets a marker score the
criterion without hunting further; the score asks how good the work is.
`docs/EVALUATION_NOTES.md` §2 explanation 2 records that the first pass instead
assigned sufficiency by quality band, so a clearly documented weak section was
labelled `partial`.

This matters for tuning. `docs/EVALUATION_NOTES.md` §2 shows the agent's errors
are almost all one step down from the labels (13 `sufficient`→`partial`,
7 `partial`→`insufficient`), and the §4 k=10 control shows the gap is not
retrieval coverage. Correcting the target before changing any prompt avoids
optimising toward the labelling confusion itself.

## Scope limits

- Only the **dev** split changed. The 19 heldout pairs are byte-identical and
  stay a usable regression split.
- Only the `sufficiency` field changed. Every `score` and every `must_contain`
  phrase is untouched, so M3 retrieval relevance is unaffected.
- 8 dev pairs carried `partial`. 7 were corrected; 1 was reviewed and kept.

## Changes

All seven corrected pairs share one pattern: the document states its own gap
plainly enough that a marker lands on the lower descriptor immediately. Each
already carried a definite numeric score in the first pass, which is itself a
sign the annotator did not need to hunt further.

| Rubric | Submission | Criterion | Score (unchanged) | partial to sufficient because |
|---|---|---|---:|---|
| engineering_report | s3_missing_eval | C4 | 2 / 4 | Results page states narrative results and admits there is no measurement section: a direct read on "Results without interpretation" |
| engineering_report | s4_decoy_eval | C4 | 2 / 4 | Results are anecdotal, discussion said the demo "felt fine" |
| engineering_report | s7_partial_results | C4 | 2 / 4 | "A single number is stated with no discussion of limitations" is the worked example in guide rule 4 |
| proposal_rubric | p2_gaps | C1 | 2.5 / 5 | Page states the problem and records that stakeholders and evidence of need are absent: verbatim the 2.5 descriptor |
| proposal_rubric | p2_gaps | C2 | 2.5 / 5 | "flat set without priority and without acceptance criteria": verbatim the 2.5 descriptor |
| proposal_rubric | p2_gaps | C3 | 2.5 / 5 | "described once; there are no iterations and no tests are planned": verbatim the 2.5 descriptor |
| proposal_rubric | p2_gaps | C4 | 2.5 / 5 | "timeline is given by week but risks are not discussed": verbatim the 2.5 descriptor |

## Reviewed and kept

**engineering_report / s7_partial_results / C5, kept `partial`.** The
Communication page reports consistent terminology in headings but never
mentions captions, and the 2/2 descriptor requires consistent headings,
captions *and* terminology. Deciding between 1 and 2 needs a caption the
document does not supply, so a marker would still have to hunt. This is what
`partial` is for. Compare `s3_missing_eval` and `s4_decoy_eval`, whose
Communication pages do name a figure caption and are labelled `sufficient`.

The five dev `insufficient` pairs were also re-read and left unchanged. Each
has a null score and a `must_contain` phrase confirming genuine absence or a
decoy only: `s3_missing_eval` C3, `s4_decoy_eval` C3, `s6_weak_problem` C1,
`s8_missing_method` C2 and C4.

## Consequence for the metric, stated before any tuning run

Class counts:

| Split | sufficient | partial | insufficient | total |
|---|---:|---:|---:|---:|
| dev, labels.json | 30 | 8 | 5 | 43 |
| dev, labels_v2.json | 37 | **1** | 5 | 43 |
| heldout, both files | 11 | 5 | 3 | 19 |
| all, labels_v2.json | 48 | 6 | 8 | 62 |

Corrected dev holds **one** `partial` pair. M4 is an unweighted mean of three
per-class F1 scores, so one third of that metric now rests on a single pair and
a few false `partial` predictions can move it sharply. Dev macro-F1 must
therefore be read together with accuracy and the per-class denominators, and a
dev macro-F1 movement of a few points is not a reliable improvement signal.

This is a property of the corpus, not of the correction. Applying guide rule 4
consistently shows that genuine `partial` evidence — where a marker must keep
hunting — is rare in these short synthetic documents, because each document
tends to state its own gaps. The first pass produced a fuller `partial` class
only by using it for weak work.

Two consequences carried forward:

1. The dev tuning window judges changes on accuracy and the full confusion
   matrix as well as macro-F1, and records per-class denominators every time.
2. The final-test annotation must deliberately include criteria whose evidence
   is genuinely scattered or incomplete, so the three-class metric has a
   measurable `partial` class. `dataset/final_test/` already reserves one
   dispersed/partially-missing document per rubric (`f02`, `f05`) for this.

## Independence limit

These corrections were made by the project's own AI-assisted review against the
rubric descriptors and the guide, not by an independent annotator. They are a
corrected development target, not human ground truth. The independent
two-annotator round in `docs/EVALUATION_PROTOCOL.md` applies to
`dataset/final_test/` and is unaffected by this file.
