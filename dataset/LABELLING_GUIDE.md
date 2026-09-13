# Labelling guide (synthetic corpus)

Two people can label the same pair. Do not use real student work.

For each (rubric, submission, criterion):

1. Highlight the spans that actually address the criterion. Copy a distinctive phrase into `must_contain`.
2. Sufficiency:
   - `sufficient`: the span would let a marker score without hunting further
   - `partial`: some relevant text, but a marker would still need more
   - `insufficient`: the criterion is absent, or only a decoy keyword
3. Score on the rubric scale, or `null` when insufficient.
4. **Label sufficiency and score independently.** Sufficiency is about the
   evidence, the score is about the work. Worked example: a Results section
   that presents numbers but never interprets them is *sufficient* evidence
   (a marker can score it without reading further) for a *low* score
   ("Results without interpretation", 2/4). Do not write `partial` because the
   work is weak; write `partial` only when you had to keep hunting.
   The first-pass labels (Sep 2026) did not follow this rule consistently —
   see `docs/EVALUATION_NOTES.md` §2 — so the second pass should re-examine
   every `partial`.
5. If you disagree, discuss once and keep one label. Record agreement later (proposal §8.1).
