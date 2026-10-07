"""Rebuild dataset/labels_v2.json from labels.json by applying reviewed dev-split corrections.

Why this exists: `dataset/LABELLING_GUIDE.md` rule 4 requires sufficiency and
score to be labelled independently. Sufficiency asks whether the retrieved text
lets a marker score the criterion without hunting further. The score asks how
good the work is. `docs/EVALUATION_NOTES.md` §2 explanation 2 records that the
first pass instead assigned sufficiency by quality band, so a clearly
documented weak section was labelled `partial`.

Tuning a prompt against that confusion would optimise toward a broken target,
so the dev labels are corrected first and the corrections are declared here
rather than hand-edited into the JSON.

Scope limits enforced below:
  * Only the dev split may change. The 19 heldout pairs stay byte-identical so
    they remain a usable regression split.
  * Only `sufficiency` may change. Scores and `must_contain` phrases are
    untouched, so M3 retrieval relevance is unaffected.
  * Every change is keyed by (rubric, submission, criterion) with a written
    reason, and the script fails if a declared key is missing or already holds
    the target value.

`dataset/labels.json` is never written. Run:
    .venv/bin/python scripts/build_labels_v2.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (rubric_id, submission_id, criterion_id): (from, to, reason)
#
# Reviewed 7 October 2026 against the rubric descriptors and the submission
# text. Each entry below is a case where the document states its own gap
# plainly enough that a marker can land on the lower descriptor immediately.
# That is sufficient evidence for a low score, not partial evidence.
CORRECTIONS: dict[tuple[str, str, str], tuple[str, str, str]] = {
    ("engineering_report", "s3_missing_eval", "C4"): (
        "partial", "sufficient",
        "The Results page states narrative results and admits there is no measurement section. "
        "That is a direct read on 'Results without interpretation' (2/4); nothing further to hunt for.",
    ),
    ("engineering_report", "s4_decoy_eval", "C4"): (
        "partial", "sufficient",
        "The Results page says results are anecdotal and the discussion said the demo 'felt fine'. "
        "A marker can score 'Results without interpretation' (2/4) from that page alone.",
    ),
    ("engineering_report", "s7_partial_results", "C4"): (
        "partial", "sufficient",
        "'A single number is stated with no discussion of limitations' is the worked example in "
        "LABELLING_GUIDE rule 4: numbers present, interpretation absent, so sufficient evidence for 2/4.",
    ),
    ("proposal_rubric", "p2_gaps", "C1"): (
        "partial", "sufficient",
        "The page states the problem and explicitly records that stakeholders are not named and no "
        "evidence of need is offered, which is verbatim the 2.5/5 descriptor.",
    ),
    ("proposal_rubric", "p2_gaps", "C2"): (
        "partial", "sufficient",
        "'Requirements are listed as a flat set without priority and without acceptance criteria' "
        "matches the 2.5/5 descriptor verbatim; the evidence is complete, the work is weak.",
    ),
    ("proposal_rubric", "p2_gaps", "C3"): (
        "partial", "sufficient",
        "'The method is described once; there are no iterations and no tests are planned' matches the "
        "2.5/5 descriptor verbatim.",
    ),
    ("proposal_rubric", "p2_gaps", "C4"): (
        "partial", "sufficient",
        "'A timeline is given by week but risks are not discussed' matches the 2.5/5 descriptor verbatim.",
    ),
}

# Reviewed and deliberately left unchanged, so the review is not a one-way flip.
RETAINED: dict[tuple[str, str, str], str] = {
    ("engineering_report", "s7_partial_results", "C5"): (
        "Kept partial. The Communication page reports consistent terminology in headings but never "
        "mentions captions, and the 2/2 descriptor requires consistent headings, captions and "
        "terminology. Choosing between 1 and 2 needs a caption the document does not supply, so a "
        "marker would still have to hunt. Compare s3_missing_eval and s4_decoy_eval, whose "
        "Communication pages do name a figure caption."
    ),
}


def _display(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def build(labels_path: Path, output_path: Path) -> dict:
    rows = json.loads(labels_path.read_text(encoding="utf-8"))
    applied: list[dict] = []
    for row in rows:
        key = (row["rubric_id"], row["submission_id"], row["criterion_id"])
        if key not in CORRECTIONS:
            continue
        if row["split"] != "dev":
            raise SystemExit(f"Refusing to change a non-dev label: {key} is in {row['split']}")
        source, target, reason = CORRECTIONS[key]
        if row["sufficiency"] != source:
            raise SystemExit(f"{key} holds {row['sufficiency']!r}, declared source was {source!r}")
        row["sufficiency"] = target
        applied.append({"key": list(key), "from": source, "to": target, "score": row["score"], "reason": reason})

    missing = set(CORRECTIONS) - {tuple(item["key"]) for item in applied}
    if missing:
        raise SystemExit(f"Declared corrections not found in {labels_path.name}: {sorted(missing)}")
    for key in RETAINED:
        if not any((r["rubric_id"], r["submission_id"], r["criterion_id"]) == key for r in rows):
            raise SystemExit(f"Declared retained label not found: {key}")

    output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    original = json.loads(labels_path.read_text(encoding="utf-8"))
    heldout_before = [r for r in original if r["split"] == "heldout"]
    heldout_after = [r for r in rows if r["split"] == "heldout"]
    if heldout_before != heldout_after:
        raise SystemExit("Heldout labels changed; aborting")
    return {
        "labels_path": _display(labels_path),
        "output_path": _display(output_path),
        "source_sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "pairs": len(rows),
        "changed": applied,
        "retained": [{"key": list(key), "reason": reason} for key, reason in RETAINED.items()],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=ROOT / "dataset/labels.json")
    parser.add_argument("--output", type=Path, default=ROOT / "dataset/labels_v2.json")
    args = parser.parse_args()
    summary = build(args.labels.resolve(), args.output.resolve())
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
