"""Write a blank sheet for the second labelling pass.

The sheet lists each pair and the submission text. It does not copy the first
annotator's sufficiency or score. Filling those columns is a person's job.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"
RUBRICS = {
    "engineering_report": DATASET / "rubrics" / "engineering_report.md",
    "proposal_rubric": DATASET / "rubrics" / "proposal_rubric.md",
    "half_mark": DATASET / "rubrics" / "half_mark.md",
}


def export_second_pass(path: Path) -> int:
    from rubric_agent.rubric_parser import parse_rubric

    labels = json.loads((DATASET / "labels.json").read_text(encoding="utf-8"))
    rubrics = {}
    texts: dict[str, str] = {}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "pair",
                "rubric_id",
                "submission_id",
                "criterion_id",
                "criterion_name",
                "max_mark",
                "submission_text",
                "sufficiency",
                "score",
                "notes",
            ],
        )
        writer.writeheader()
        for index, row in enumerate(labels, start=1):
            rubric_id = row["rubric_id"]
            if rubric_id not in rubrics:
                rubrics[rubric_id] = parse_rubric(RUBRICS[rubric_id], rubric_id=rubric_id)
            criterion = next(c for c in rubrics[rubric_id].criteria if c.id == row["criterion_id"])
            submission_id = row["submission_id"]
            if submission_id not in texts:
                texts[submission_id] = (DATASET / "submissions" / f"{submission_id}.txt").read_text(encoding="utf-8")
            writer.writerow({
                "pair": index,
                "rubric_id": rubric_id,
                "submission_id": submission_id,
                "criterion_id": criterion.id,
                "criterion_name": criterion.name,
                "max_mark": criterion.max_mark,
                "submission_text": texts[submission_id].replace("\n", " ").strip(),
                "sufficiency": "",
                "score": "",
                "notes": "",
            })
    return len(labels)


if __name__ == "__main__":
    out = DATASET / "second_pass" / "to_label.csv"
    n = export_second_pass(out)
    print(f"wrote {n} blank rows to {out}")
