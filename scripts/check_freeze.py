"""Check that the working tree still matches the frozen configuration.

The freeze is only meaningful if it is checkable. Two questions, in order of
importance:

1. Can this tree reproduce the committed campaign results? The authority is
   `docs/evaluation_dev_frozen/manifest.json`, which the runner wrote from the
   tree it actually executed on and re-verified around every model call.
2. Do the aggregate digests quoted in `docs/FREEZE.md` still describe this
   tree? These are for a human reader and are recomputed here so the prose
   cannot drift away from the files.

    .venv/bin/python scripts/check_freeze.py

Non-zero exit if the tree can no longer reproduce the campaign, so later work
can be guarded by it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE_DOC = ROOT / "docs/FREEZE.md"
CAMPAIGN = ROOT / "docs/evaluation_dev_frozen/manifest.json"

# Quoted in docs/FREEZE.md. The `code` value was computed from the
# v1.0.0-frozen tag, which still carried __version__ = "0.3.0"; the version
# string was bumped to 1.0.0 in the next commit, before the campaign ran. See
# the note in docs/FREEZE.md.
FREEZE_DOC_DIGESTS = {
    "code_at_tag": "534309638b31f4bc59cb8845b3acc1e2699471bd924a62de52fde5186ea301ba",
    "prompts": "d80612d16c4bec4584d7baafa9721e256caee3534df7e65a8ae40ba8d9ed4706",
    "final_test_inputs": "14f72e5c491f0729ca1f539feae20e13bae26a8a91332d1d8779c507bb49eaa3",
    "dev_corpus": "ac15a11f9bce6bc31b8c10706e863f139c12e4cc233d0b4c50b215e38b0ef3cd",
}


def aggregate(paths: list[Path]) -> tuple[str, dict[str, str]]:
    files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(set(paths)) if p.is_file()}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), files


def current_scopes() -> dict[str, tuple[str, dict[str, str]]]:
    final_test = [p for p in (ROOT / "dataset/final_test").rglob("*")
                  if p.is_file() and "annotation" not in p.parts]
    return {
        "code": aggregate(list((ROOT / "src/rubric_agent").rglob("*.py"))),
        "prompts": aggregate([p for p in (ROOT / "prompts").iterdir() if p.is_file()]),
        "final_test_inputs": aggregate(final_test),
        "dev_corpus": aggregate([
            ROOT / "dataset/labels.json", ROOT / "dataset/labels_v2.json",
            *(ROOT / "dataset/rubrics").glob("*"), *(ROOT / "dataset/submissions").glob("*"),
        ]),
    }


def check_against_campaign() -> list[str]:
    """Per-file comparison with the manifest the campaign runner actually wrote."""
    if not CAMPAIGN.is_file():
        print("No campaign manifest found; skipping the reproducibility check.")
        return []
    recorded = json.loads(CAMPAIGN.read_text(encoding="utf-8"))["frozen_inputs"]["files"]
    drifted = []
    for name, expected in sorted(recorded.items()):
        path = ROOT / name
        if not path.is_file():
            drifted.append(f"{name}: missing from the tree")
            continue
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != expected:
            drifted.append(f"{name}: {expected[:12]} -> {got[:12]}")
    print(f"Campaign manifest covers {len(recorded)} files "
          f"(src/, prompts/, run_campaign.py, labels and the documents they name).")
    if drifted:
        print(f"  {len(drifted)} file(s) differ from the executed campaign:")
        for line in drifted:
            print(f"    {line}")
    else:
        print("  every one is byte-identical, so this tree reproduces the committed results.")
    return drifted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    print("Freeze check\n")
    drifted = check_against_campaign()

    print(f"\nAggregate digests quoted in {FREEZE_DOC.relative_to(ROOT)}:")
    actual = current_scopes()
    doc_text = FREEZE_DOC.read_text(encoding="utf-8") if FREEZE_DOC.is_file() else ""
    mismatched_doc = []
    for label, expected in FREEZE_DOC_DIGESTS.items():
        scope = "code" if label == "code_at_tag" else label
        got, files = actual[scope]
        ok = got == expected
        note = ""
        if label == "code_at_tag" and not ok:
            note = "  (expected: tag predates the __version__ bump)"
        print(f"  {'OK   ' if ok else 'differs'}  {label:18s} {len(files):3d} files  {got[:16]}…{note}")
        if not ok and label != "code_at_tag":
            mismatched_doc.append(label)
        if expected not in doc_text:
            print(f"           note: this digest is no longer quoted in {FREEZE_DOC.name}")

    if drifted:
        print("\nFAIL: the tree differs from the executed campaign. Its results cannot be "
              "reported from this tree, and a new campaign needs a new output directory.")
        return 1
    if mismatched_doc:
        print(f"\nFAIL: {', '.join(mismatched_doc)} no longer match docs/FREEZE.md.")
        return 1
    if not args.quiet:
        print("\nPASS: prompts, final-test inputs and the development corpus are unchanged, "
              "and every file the campaign hashed is byte-identical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
