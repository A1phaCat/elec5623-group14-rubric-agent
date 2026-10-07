"""Write one blank annotation sheet per annotator for the frozen final test.

`docs/EVALUATION_PROTOCOL.md` requires two people to label the 27 final-test
pairs independently, without seeing model output or each other's decisions,
before any adjudication. This script produces their sheets and nothing else:
every `sufficiency`, `score` and `rationale` cell is empty, and no first-pass
or model value is copied in.

The sheets are ordered by rubric and criterion rather than shuffled, so an
annotator reads one document once and answers each criterion against it.

    .venv/bin/python scripts/export_annotation_sheets.py --annotators A B

Running it again refuses to clobber a sheet that already has content, so a
partially completed sheet cannot be reset by accident.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "dataset/final_test"

FIELDS = [
    "pair",
    "rubric_id",
    "submission_id",
    "scenario",
    "criterion_id",
    "criterion_name",
    "max_mark",
    "granularity",
    "level_descriptors",
    "submission_text",
    # The annotator fills only the three columns below.
    "sufficiency",
    "score",
    "rationale",
]

INSTRUCTIONS = """Annotation instructions (read once, then do not change them mid-sheet)

Fill only the sufficiency, score and rationale columns.

sufficiency is about the EVIDENCE, not the quality of the work:
  sufficient   - you can name the level descriptor this document matches for
                 this criterion without hunting further. This includes weak
                 work that the document itself documents plainly.
  partial      - the document points at content you cannot see (an appendix, a
                 "see Section 4"), a statement is cut off, or the descriptors
                 need a dimension the text never mentions and might cover
                 elsewhere. You would have to keep searching.
  insufficient - the criterion is absent, or only its keyword appears with no
                 substance.

score is about the QUALITY of the work, on the rubric scale:
  - a number that is a multiple of `granularity`, from 0 to max_mark;
  - leave it EMPTY only when sufficiency is insufficient;
  - clearly documented weak work gets sufficient evidence and a LOW score.

rationale: one short line naming the descriptor you chose and the words in the
document you relied on.

Do not look at any model output, any other annotator's sheet, or the
development corpus labels while filling this in.
"""


def _level_text(criterion) -> str:
    return " | ".join(f"{level.score}: {level.text}" for level in criterion.descriptors)


def export_sheets(annotators: list[str], corpus: Path = CORPUS, force: bool = False) -> dict[str, Path]:
    from rubric_agent.rubric_parser import parse_rubric

    manifest = json.loads((corpus / "corpus.json").read_text(encoding="utf-8"))
    rubrics: dict[str, object] = {}
    texts: dict[str, str] = {}
    rows: list[dict] = []

    for entry in manifest["submissions"]:
        rubric_id, submission_id = entry["rubric_id"], entry["submission_id"]
        if rubric_id not in rubrics:
            rubrics[rubric_id] = parse_rubric(corpus / "rubrics" / f"{rubric_id}.md", rubric_id=rubric_id)
        if submission_id not in texts:
            texts[submission_id] = (corpus / "submissions" / f"{submission_id}.txt").read_text(encoding="utf-8")
        for criterion in rubrics[rubric_id].criteria:  # type: ignore[attr-defined]
            rows.append({
                "pair": len(rows) + 1,
                "rubric_id": rubric_id,
                "submission_id": submission_id,
                "scenario": entry["scenario"],
                "criterion_id": criterion.id,
                "criterion_name": criterion.name,
                "max_mark": criterion.max_mark,
                "granularity": criterion.granularity,
                "level_descriptors": _level_text(criterion),
                "submission_text": texts[submission_id].replace("\n", " ").strip(),
                "sufficiency": "",
                "score": "",
                "rationale": "",
            })

    written = {}
    workspace = corpus / "annotation"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "INSTRUCTIONS.txt").write_text(INSTRUCTIONS, encoding="utf-8")
    for name in annotators:
        path = workspace / f"annotator_{name}.csv"
        if path.exists() and not force and any(
            row["sufficiency"] or row["score"] or row["rationale"]
            for row in csv.DictReader(path.open(encoding="utf-8"))
        ):
            raise SystemExit(f"{path} already has annotations; refusing to overwrite. Pass --force to discard them.")
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        written[name] = path
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotators", nargs="+", default=["A", "B"],
                        help="identifiers for the sheets; record who each one is in annotation/REGISTER.md")
    parser.add_argument("--force", action="store_true", help="discard existing annotations")
    args = parser.parse_args()
    written = export_sheets(args.annotators, force=args.force)
    for name, path in written.items():
        rows = sum(1 for _ in csv.DictReader(path.open(encoding="utf-8")))
        print(f"annotator {name}: {rows} blank pairs -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
