# Status — 7 October 2026

Frozen at tag **`v1.0.0-frozen`** (`docs/FREEZE.md`). 27 days to the Project
Development deadline, 3 November 2026 23:59; presentation and Q&A 4 November.

The proposal scored **6.5/10**, marked by **Haolin Jin**.
`docs/MARKER_RESPONSE.md` maps each deduction to the work it requires and to
the A2 weights: 4 implementation + 4 GenAI engineering + 4 evaluation +
3 novelty + 2 track alignment + 2 workflow + 1 documentation. None of that is
an estimated grade.

## Done since 4 October

- **Dev label correction.** The first-pass labels assigned sufficiency by
  quality band, contradicting `dataset/LABELLING_GUIDE.md` rule 4. Seven of
  eight dev `partial` pairs were corrected with written reasons and one was
  reviewed and kept (`dataset/LABELS_V2_CHANGES.md`). `labels.json` is
  untouched; heldout is byte-identical.
- **Prompt selection, dev split only.** Four variants, recorded in
  `docs/tuning/README.md`. `assessment_v4` selected. Sufficiency accuracy
  0.767 against the previous build's 0.581, one-step-down errors 16 → 6, score
  coverage 36/38, FR14 exercised again. v3 scored higher on accuracy but
  destroyed five records through a prompt sentence the validator rejects and
  stopped producing feedback; v5 is recorded as rejected for pushing four of
  five absent criteria to `sufficient`.
- **Freeze.** Model, decoding, prompts, retrieval, budgets and repeats fixed
  with manifest digests, dated before annotation begins.
- **Annotation workspace.** Blank sheets for the 27 final-test pairs, plus
  agreement and adjudication tooling that refuses incomplete input
  (`dataset/final_test/annotation/REGISTER.md`).
- **Marker-session kit.** Protocol, verbatim consent note, the proposal's own
  questionnaire items, and a summariser that reports unmeasured metrics as
  `null` with a reason (`docs/MARKER_SESSIONS.md`).
- **Contribution register from git.** `docs/CONTRIBUTIONS.md`, generated.
- **Clean-clone rehearsal and packaging audit.**
  `docs/validation/cleanroom_2026-10-07.md`: 128 tests pass from a fresh clone
  with no key and no network; the wheel ships no private document; the bundled
  proposal PDF contains no name or student ID.
- **Campaign runner** takes `--corpus`, so the frozen final test runs through
  the same code path as the development corpus.
- **Robustness, separate from M1–M17.** Injection resistance 0.972 on 36
  pairs (target 1.00, missed: one planted claim was asserted, and one
  abstention became a full mark). Order invariance 0.750 on 12 permutations
  (target 1.00). Removing the decisive paragraph never raised a judgement
  (0/4). Record: `docs/robustness/RESULTS.md`. Prompts and final-test inputs
  are unchanged (`scripts/check_freeze.py`).

## Blocked on people, not code

These are the remaining marks and none of them can be produced by running
something.

1. **Independent annotation of the 27 final-test pairs.** Two people, each
   working alone, then agreement computed from the untouched originals, then
   adjudication. Procedure and the two likely mistakes are in
   `dataset/final_test/annotation/REGISTER.md`. Until this exists,
   `dataset/final_test/labels.json` does not exist and the final campaign
   refuses to run.
2. **Two to three marker sessions, each with a manual arm.** Without the
   timed rubric-only arm, M10 cannot be measured at all.
3. **The other four members' contribution evidence.** The register currently
   shows every commit under one identity. `docs/TEAM_DELIVERY.md` lists what
   each member can do that leaves a verifiable artifact.

## Measurement state

| Metric | Where it stands |
|---|---|
| M1, M2, M5, M7, M16 | pass on every run |
| M3 Recall@5 | 1.000 on the dev corpus; **unmeasured on final_test**, whose labels carry no `must_contain` |
| M4 sufficiency macro-F1 | below target on dev for a structural reason: corrected dev holds one `partial` pair, so a third of the metric rests on it. Settled on final_test, where `f02`/`f05` give the class a real denominator |
| M6 uncited positive claims | 0.000 in every run; B2's rate reflects its output format, not hallucination |
| M8, M12, M13 | current frozen development-corpus campaign in progress |
| M9, M10, M11, M14 | **not measured**; need the sessions above |
| Addendum A robustness | measured 7 Oct; injection and order-invariance targets missed, directional target met. Not part of M1–M17 |
| Faithfulness sample | sheet drawn, **not filled in** (`docs/faithfulness/sample_blank.csv`) |
| M15 audit | the packaging and personal-data audit is done; the marker-session half is not |

## Honest limits

The fixture is a descriptor-matching heuristic; its numbers are not model
evidence. The 13 September reports are historical snapshots whose pooled QWK
is superseded and must not be compared with current QWK. All labels so far are
synthetic and reviewed by the project itself, not independent ground truth. A
citation that exists does not establish semantic support.

## Next

Annotation, then the frozen final-test campaign, then sessions, then integrate
`docs/FINAL_REPORT_DRAFT.md` and refresh the screenshots in `docs/img/`, which
predate `assessment_v4`. Recheck Canvas for the separately released
presentation brief.
