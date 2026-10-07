# The freeze guard fired on a real mid-run change — 7 October 2026

Recorded because it is evidence that the reproducibility mechanism works under
conditions we did not stage, and because the incident is more informative than
a passing test.

## What happened

The first attempt at the frozen development-corpus campaign was running. Nine
of 63 checkpoints had completed. In a separate terminal the project version was
bumped from `0.3.0` to `1.0.0` in `src/rubric_agent/__init__.py`, to match the
`v1.0.0-frozen` tag.

That file is inside the hashed code manifest. On the next model call
`Campaign.assert_frozen()` recomputed the manifest, found it different from the
one recorded at startup, and aborted:

```
RuntimeError: Source/prompt/data changed during campaign;
checkpoint preserved, refusing mixed-source run
```

The nine completed checkpoints were left on disk, and no further calls were
made.

## Why this is the correct behaviour

The change was harmless in substance: a version string, with no effect on
retrieval, prompting or validation. The guard cannot know that, and should not
try. A campaign whose outputs came from two different source trees cannot
honestly report a single code hash, which is exactly the claim
`docs/FREEZE.md` and every generated report make. Aborting is cheaper than
discovering afterwards that half a results table came from a different build.

The guard also refused to resume into the same output directory, because the
startup identity no longer matched: `Frozen code, prompts, corpus, model or
settings differ; use a new output directory`. That is the second half of the
protection — a resume that silently continued would have produced the mixed
run the abort just prevented.

## What was done

The nine checkpoints were discarded rather than reused, the working tree was
committed so it would stop moving, and the campaign was restarted from zero
into a fresh directory. No partial result from the first attempt contributes to
any reported number.

## Practice this fixes

Finish all source and prompt edits before starting a campaign, and change
nothing but `docs/` while one is running. The manifest covers
`src/rubric_agent/**/*.py`, `prompts/*`, `scripts/run_campaign.py`, the label
file and every rubric and submission it names; everything else is safe to edit
mid-run.

A related slip is recorded in the history for the same reason: a `git add -A`
during the first attempt committed partial checkpoints and the in-progress
manifest. Campaign directories are now gitignored, so campaign artifacts enter
the repository once, complete, alongside the reports they support.
