# Marker sessions — protocol and recording kit

**Status: not run. M9, M10, M11 and M14 are unmeasured.** Until real sessions
exist, the report says "not measured" for all four; it does not estimate them.

These four metrics are the only evidence the project will have about the human
half of the workflow, which is what A2 marks under product quality and
user/system workflow. They cannot be produced by running code.

## Metrics, exactly as declared in the proposal (§8.4)

| Metric | Definition | Target | Needs |
|---|---|---|---|
| M9 marker correction rate | criteria where the marker changed the AI score / criteria decided | reported, not a pass/fail | agent arm |
| M10 review time | median time per submission, agent arm vs manual arm | ≥20% reduction | **both arms** |
| M11 perceived usefulness and control | post-session 5-point items | control ≥ 4/5 | questionnaire |
| M14 usability | facilitator interventions per session; evidence items opened in context rather than by searching the document | ≤1 intervention per session; 100% of evidence | facilitator tally |

M10 is a comparison, so a session that only uses the tool cannot measure it.
Each participant must also mark at least one submission with the rubric alone
(baseline B1), timed. Without that arm, M10 stays unmeasured and only M9, M11
and M14 are reportable.

## Participants

Two to three consenting adults. Prefer group members who did **not** build the
review UI, plus peer volunteers. Tutor participation must be confirmed with the
unit coordinator first.

Record them as `P1`, `P2`, `P3`. Do not record names, student IDs, or anything
else about the person. These are convenience-sample non-expert participants,
not professional markers, and the report must say so.

## Materials

Use the synthetic corpus only. Suggested allocation, one submission per arm per
participant so neither arm is always the easy document:

| Participant | Manual arm (B1, rubric only) | Agent arm (tool) |
|---|---|---|
| P1 | `s1_standard` | `s2_dispersed` |
| P2 | `s2_dispersed` | `s1_standard` |
| P3 | `s7_partial_results` | `s4_decoy_eval` |

Do not use `dataset/final_test/` documents: they are reserved for the frozen
campaign and must not be seen before annotation.

## Before the session

1. Confirm the freeze is in place (`docs/FREEZE.md`); do not change the system
   between sessions, or the sessions are not comparable.
2. Start the model and pre-warm the case, because a cold first call distorts
   both the timing and the participant's impression:

   ```sh
   OLLAMA_HOST=127.0.0.1:11434 OLLAMA_CONTEXT_LENGTH=16384 ollama serve
   .venv/bin/python -m rubric_agent.cli --gateway ollama:qwen2.5:7b-instruct demo --submission s2_dispersed
   streamlit run app/streamlit_app.py
   ```

3. Read the participant the consent note below, verbatim.

> This is a prototype marking assistant for a university assignment. You will
> mark synthetic, made-up student work, never anyone's real submission. I will
> time how long each document takes and note when I have to help you use the
> interface. Afterwards I will ask five short questions. I am recording no
> personal information about you, and you may stop at any point. The scores you
> give are not used to grade anyone.

## Running a session

Manual arm first, so the tool does not teach the rubric before the baseline.

**Manual arm (B1).** Give the participant the rubric and the submission as
plain text. Start a stopwatch when they begin reading, stop it when they have a
score for every criterion. Record their scores.

**Agent arm.** Give them the tool. The session duration is recorded
automatically in the export, so the stopwatch is a cross-check rather than the
source. Tell them to accept, edit or reject each criterion and then export.

While they work, tally two things:

- **interventions**: every time you explain how to use the interface or they
  cannot proceed unaided. Answering "does this look right?" about *marking
  judgement* is not an intervention; explaining *the interface* is.
- **evidence opened in context**: each evidence item they inspect using the
  interface's own context view, versus each time they scroll or search the raw
  document instead. M14 wants the second number to be zero.

Do not coach, and do not defend the tool. A participant who misreads the
interface is data.

## Questionnaire

Five-point scale, 1 = strongly disagree, 5 = strongly agree. The first two
items are the ones the proposal declared; do not reword them.

1. I remained in control of the final score.
2. The evidence saved me searching.
3. I could tell which part of the submission each suggested score came from.
4. I would trust this to prepare a first pass that I then check.
5. The interface stayed out of my way.

Then one open question, recorded verbatim: **"What would you change first?"**

M11's declared target is item 1 ≥ 4/5. Report every item with its number of
respondents; five answers from two people is not a usability study.

## Recording a session

One JSON file per participant per arm in `docs/sessions/`, named
`<participant>_<arm>.json`. Copy `docs/sessions/TEMPLATE.json` and fill it in.
For the agent arm, paste the session summary straight from the tool's export so
the duration, override rate and intervention count are the tool's own numbers
rather than retyped.

Then:

```sh
.venv/bin/python scripts/summarise_sessions.py
```

This writes `docs/sessions/summary.json` with M9, M10, M11 and M14, each with
its denominator, and leaves any metric with no data as `null` with a reason. It
refuses to invent a value from a missing arm.

## Reporting rules

- Say "2 participants" or "3 participants" in the sentence that states each
  number. A median of two values is two values.
- Non-expert convenience participants, synthetic documents, one session each,
  no training, no counterbalancing beyond the table above.
- If the manual arm is missing, M10 is "not measured", not "no difference".
- A participant who accepted everything is a finding about automation bias
  (proposal risk R3), not a successful result. Report the correction rate
  beside the agreement numbers so a near-zero correction rate cannot be read as
  accuracy.
- Keep the raw per-session files in the repository. The summary is derived and
  can be recomputed.
