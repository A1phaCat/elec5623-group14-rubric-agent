# Labelling guide (synthetic corpus)

Two people can label the same pair. Do not use real student work.

For each (rubric, submission, criterion):

1. Highlight the spans that actually address the criterion. Copy a distinctive phrase into `must_contain`.
2. Sufficiency:
   - `sufficient`: the span would let a marker score without hunting further
   - `partial`: some relevant text, but a marker would still need more
   - `insufficient`: the criterion is absent, or only a decoy keyword
3. Score on the rubric scale, or `null` when insufficient.
4. If you disagree, discuss once and keep one label. Record agreement later (proposal §8.1).
