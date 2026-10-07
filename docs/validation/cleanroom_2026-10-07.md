# Clean-clone verification — 7 October 2026

What a marker does with the submitted source package: clone it, follow the
README, and run it. This is that rehearsal, executed rather than described.
It verifies the setup instructions and that nothing private ships; it says
nothing about model quality.

## Procedure

```sh
git clone <repo> repo && cd repo
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python scripts/generate_dataset.py
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests app scripts
.venv/bin/python -m rubric_agent.cli --gateway fixture demo --submission s4_decoy_eval
.venv/bin/rma --gateway fixture eval --split dev --repeats 1
```

Python 3.14.7, macOS arm64, no network access to any model provider and no API
key set.

## Result

| Check | Outcome |
|---|---|
| Fresh clone, tracked files | 156 |
| `pip install -e '.[dev]'` from a clean venv | succeeded with no manual steps beyond the README |
| `scripts/generate_dataset.py` | exit 0, and `git status --porcelain` stayed empty afterwards, so regenerating the synthetic corpus does not mutate committed labels |
| Full test suite | **128 passed** |
| `ruff check src tests app scripts` | passed |
| `python -m rubric_agent.cli` and the `rma` entry point | both ran the offline fixture path and printed per-criterion output |

The offline default matters here: a marker with no model access and no key can
still install the package, run every test and see the workflow end to end.

## Packaging audit

`python -m build --wheel` produced `rubric_marking_agent-1.0.0-py3-none-any.whl`,
47 entries. The build hook bundles only the prompts and the synthetic corpus:

- 6 prompt files under `rubric_agent/resources/prompts/`;
- 19 synthetic rubric/submission/label files under `rubric_agent/resources/dataset/`.

Checked absent from the wheel, and confirmed absent:

- `dataset/real/` and the group's own proposal PDF;
- `dataset/final_test/` and its annotation workspace;
- `docs/sessions/`, `labels_v2.json`, run logs, any `.env`.

## Secret and personal-data scan

- Pattern scan across all 156 tracked files for assignment-style credentials
  and for `sk-`, `ghp_` and `AKIA` literals: no matches.
- `dataset/real/group14_proposal_v2.pdf`: extracted all 16 pages of text and
  searched for every group member's given name, every student ID, and any
  nine-digit ID-shaped number. **No matches**, which confirms the cover-page
  removal recorded in `dataset/real/README.md`.
- No API key is required to run the tests, and the gateway only contacts a
  hosted endpoint when `RMA_*` variables are set explicitly.

## Still to do before submission

This rehearsal used the repository as it stands on 7 October. Repeat it on the
final package after the report is integrated, and refresh it if any dependency
or packaging file changes. The UI screenshots in `docs/img/` are dated
13 September and predate `assessment_v4`; they must be regenerated so the
assessed source matches the demonstrated system.
