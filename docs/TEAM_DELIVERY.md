# Named team delivery plan

Updated 7 October 2026. **Proposed allocation, pending each member's
confirmation.** Nothing here is a claim that the work is done, that anyone has
agreed, or that anyone authored anything. What has actually been committed is
generated from git history in `CONTRIBUTIONS.md`; read that for the record and
this for the plan. The A2 rubric awards group marks, so this is work
prioritisation, not an individual mark guarantee.

Everyone commits under their own GitHub account on the private repository, so
each person's contribution appears in the history under their own name. Nobody
commits on anyone else's behalf.

## The allocation

| Member | Task | Effort | What it produces, and where it lands |
|---|---|---|---|
| **Zhengyu Han** | Technical lead: implementation and evaluation, **AI-assisted and disclosed** (`AI_USE.md`). Annotator **B**. Week 10 and Week 12 interactive orals and the Week 13 technical section. Final report review and submission. | the bulk | the frozen build, the campaign, the robustness experiment, report §§4–8 |
| **Yuchun Zheng** | Annotator **A**: the 27 final-test pairs, working alone. | ~1.5 h | `dataset/final_test/annotation/annotator_A.csv`, uploaded through the GitHub web interface under their own account |
| **Zhaoxinyi Zhou** | 2–3 marker sessions with timing and the questionnaire, **each including the rubric-only arm**, plus screenshots of the frozen build. | ~2–3 h | `docs/sessions/*.json` naming them as facilitator; refreshed `docs/img/` |
| **Zongjian Li** | Verify the three closest papers against report §3 and own the novelty answer in the Week 13 Q&A. | ~2 h | a reviewed §3 and the ability to answer "what is actually new here" live |
| **Yutong Liu** | Clean-machine reproduction on their own laptop, following only the README, logging every snag. | ~1–2 h | a snag log; any README defect found is a real result |

## Why the annotation order matters

Han must finish **sheet B before sheet A is uploaded**. The two annotations are
only independent if neither annotator can see the other's answers, and the
agreement statistic is the only independent evidence this project will have
about its reference labels. If sheet A lands first and Han then fills sheet B,
the independence claim is gone and cannot be recovered.

So the sequence is fixed:

1. Han completes `annotator_B.csv` and commits it.
2. Only then does Yuchun Zheng upload `annotator_A.csv`.
3. `scripts/adjudicate_annotations.py agreement` runs on the untouched
   originals, and `agreement.json` is committed **before** anyone discusses a
   disagreement.
4. Adjudication, then `build`, then the frozen final-test campaign.

A packaged copy of the blank sheet and a Chinese instruction sheet for Yuchun
Zheng lives outside the repository at `5623/标注包_final_test/`. The sheet
survives Excel's "CSV UTF-8" byte-order mark, which is tested.

## Each task, in enough detail to start

**Yuchun Zheng — annotator A.** Read `annotation/INSTRUCTIONS.txt` once, then
fill `sufficiency`, `score` and `rationale` for all 27 rows. The one thing that
matters: sufficiency is about whether the *evidence* lets a marker pick a
descriptor, not about whether the work is good. Clearly documented weak work is
`sufficient` evidence for a **low** score. Do not look at any model output or at
the development corpus labels. Upload through GitHub's web interface so the
commit is under your account; no git installation needed.

**Zhaoxinyi Zhou — marker sessions.** `docs/MARKER_SESSIONS.md` has the
protocol, the consent note to read verbatim, and the questionnaire. The part
most easily missed: each participant must **also** mark a submission with the
rubric alone, timed, or M10 cannot be computed at all. Record sessions as
`docs/sessions/<participant>_<arm>.json` from `TEMPLATE.json`, then run
`scripts/summarise_sessions.py`.

**Zongjian Li — novelty.** Open Evidence-First Scoring (Cai 2026),
GradeAgentOps (Anghel et al. 2026) and RULERS (Hong et al. 2026a/b) from the
links in `RELATED_WORK.md`, check that report §3 describes each one correctly,
and be able to say in the Q&A where we overlap and what is narrowly ours. The
proposal lost a mark for claiming novelty that prior work already had; the
defence is accuracy, not a bigger claim.

**Yutong Liu — clean-machine reproduction.** Clone the repository on your own
laptop and follow the README exactly. Log every point where the instructions
were wrong, incomplete or needed guessing. A snag is a finding, not a
failure — the CI break fixed on 7 October was precisely this class of defect
(`pytest` behaved differently from `python -m pytest`), and it would have hit
you. Report what happened rather than working around it silently.

**Zhengyu Han — orals and submission.** AI assistance is disclosed in
`AI_USE.md` and is permitted for the 20% development component. It is
prohibited during the Week 10, Week 12 and Week 13 live assessments, so the
technical explanation has to be genuinely held, not read. Be able to explain:
why restricting evidence beat full context, why the one-shot baseline agrees
better on scores while being uncheckable, why macro-F1 is misleading when one
class has a single gold pair, and what the injection test actually showed.

## What an AI assistant cannot supply

Stated plainly because the rest of the build is AI-assisted and disclosed, and
the boundary is what makes the disclosure meaningful.

- **Independent human labels.** Two people must read the 27 pairs separately.
  An AI filling either sheet would destroy the only independent evidence about
  our reference labels.
- **The manual faithfulness judgements.** `docs/faithfulness/sample_blank.csv`
  is deliberately blank. A model judging whether its own citation supports its
  own claim is not human evidence.
- **Real marker timings and observations.** A stopwatch on a real person.
- **Teammates' acceptance of these roles.** This document is a proposal until
  each person says yes.
- **The live assessments.** AI is prohibited in the Week 10, Week 12 and Week 13
  rooms, so the explanation has to be genuinely understood.

## Proposed milestones (internal targets, not school deadlines)

| Target | Output | Who |
|---|---|---|
| ~~7 Oct~~ **done** | code and prompts frozen (`FREEZE.md`); A/B2/B3 campaign run; robustness experiment predeclared and run; CheckList cited | Han |
| 10 Oct | **sheet B complete and committed** — gates everything below | Han |
| 14 Oct | sheet A uploaded; `agreement.json` committed from the untouched originals, before any discussion | Zheng, then Han runs agreement |
| 16 Oct | adjudicated labels built; frozen final-test campaign run | Han |
| 21 Oct | 2–3 marker sessions with both arms; refreshed screenshots | Zhou |
| 21 Oct | clean-machine reproduction and snag log | Liu |
| 24 Oct | report §3 verified against the three papers | Li |
| 29 Oct | report integrated; contribution register regenerated; references checked | Han, all review |
| 1 Nov | clean-clone rehearsal on the submission package; demo rehearsal without AI | all five |
| 3 Nov 23:59 | source plus report submitted | Han |
| 4 Nov | presentation and Q&A, no AI | all five |

Week 10 (14 Oct) and Week 12 (28 Oct) labs hold interactive orals. Confirm
their scope with the tutor; AI is prohibited in them.

The A2 brief states source code plus one report due 3 November 2026 23:59, and
presentation/Q&A on 4 November. Recheck the final Canvas brief before
submission, since the presentation format was to be released separately.

## Actual contribution register

**Do not hand-write this table.** It is generated from git history:

```sh
.venv/bin/python scripts/contribution_register.py --markdown   # writes docs/CONTRIBUTIONS.md
```

`docs/CONTRIBUTIONS.md` lists, per member, the number of commits, the files
touched, the ownership areas those files fall into, and every commit SHA with
its date and subject. A marker can check any line of it with `git show`. This
is the answer to the proposal comment that work was not assigned to named
people: not a better-worded table, a verifiable one.

As of 7 October 2026 the register shows **all commits under one identity,
Zhengyu Han**. The other four members have no committed contribution evidence
in this repository yet. That is the honest state, and it is what the report
must say until it changes.

### How each member creates evidence

A task assignment is not evidence. An AI-generated file is not evidence that
the assigned person did the work. Do not commit under another person's name.

| Member | What produces verifiable evidence |
|---|---|
| Zhengyu Han | already recorded in `docs/CONTRIBUTIONS.md` |
| Zongjian Li | commits to the rubric parser or `docs/RELATED_WORK.md`; a reviewed reference list with the papers actually opened |
| Yuchun Zheng | a completed annotation sheet in `dataset/final_test/annotation/` with their name in `REGISTER.md`; commits to ingestion or export checks |
| Yutong Liu | the campaign they executed (`manifest.json` carries the settings and hashes) plus commits to `scripts/` or the logs |
| Zhaoxinyi Zhou | session files in `docs/sessions/` naming them as facilitator; commits to `app/` or `tests/test_ui.py`; the refreshed screenshots |

Work that leaves no commit still counts, but it has to leave *some* artifact:
an annotation sheet, a session record, a campaign manifest. Each of those names
a person, and each is referenced from the report.

### First step for the other four

Each member clones the repository, configures their own `user.name` and
`user.email`, does their piece on a branch, and pushes it. Then add their git
identity to `MEMBERS` in `scripts/contribution_register.py` and regenerate.
Until their identity is listed there, their commits appear under "unmapped git
identities" rather than being silently credited to anyone.
