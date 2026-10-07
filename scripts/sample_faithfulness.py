"""Draw a blank manual faithfulness sample from existing frozen-config outputs.

Addendum A.6 of docs/EVALUATION_PROTOCOL.md, answering the Week 9 lab §5 ask
for a manual check of which factual claims are supported by the retrieved
context. M5 (citation id exists) and M6 (uncited positive sentence rate) are
declared structural proxies throughout the protocol; this is the instrument
that replaces the largest of those disclaimers with a human number.

    .venv/bin/python scripts/sample_faithfulness.py

Writes a blank sheet. It must be scored by a named person: an AI judging
whether its own citation supports its own claim is not human evidence, and the
protocol forbids using it that way. Until someone scores it the result is
**not measured**.

Sampling is reproducible — fixed seed, recorded in the sheet and in the
companion JSON — so the same 30 claims can be redrawn and a second judge can
score the identical sample.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rubric_agent.chunker import chunk_pages  # noqa: E402
from rubric_agent.text_parser import parse_submission  # noqa: E402

CAMPAIGN = ROOT / "docs/evaluation_dev_frozen"
CORPUS = ROOT / "dataset"
SEED = 20261007
SAMPLE_SIZE = 30

CITATION = re.compile(r"\[(E-\d{3})(?::[^\]]*)?\]")

FIELDS = [
    "item", "rubric_id", "submission_id", "criterion_id",
    "claim_sentence", "cited_unit_id", "cited_unit_page", "cited_unit_section", "cited_unit_text",
    # The judge fills only these three.
    "supported", "note", "judge",
]

INSTRUCTIONS = """Manual faithfulness check — instructions

What you are judging
--------------------
For each row you see one sentence the system wrote (claim_sentence) and the
full text of the evidence unit it cited (cited_unit_text). Answer one question:

    Does the cited passage support this claim?

Fill `supported` with exactly one of:

  yes     - the cited passage states or directly entails the claim
  partial - the passage is about the right thing but does not establish what
            the claim asserts (e.g. the claim adds a judgement, a quantity or a
            property the passage does not contain)
  no      - the passage does not support the claim, or is about something else

Put anything worth remembering in `note`, and your name in `judge`.

Rules that matter
-----------------
1. Judge support, not quality. A claim can be well written and unsupported.
2. Judge ONLY against the passage shown. Do not use the rest of the document,
   your own knowledge, or whether the claim seems true. Faithfulness asks
   whether the evidence supports the claim; it does not ask whether the
   evidence is correct.
3. A claim that merely names the rubric descriptor ("this matches the 2-mark
   descriptor") is a judgement about the rubric, not a factual claim about the
   submission. Mark those `partial` and say so in the note.
4. Do not change any other column.
5. If you are unsure, use `partial` and write why. An honest `partial` is more
   useful than a guessed `yes`.

Do not let an AI fill this in. The entire point is that it is a human reading
the passage. An AI judging its own citation would be the system marking its own
homework.

When you are done
-----------------
Run:

    .venv/bin/python scripts/sample_faithfulness.py --score <your-sheet.csv>

It reports the supported rate with its denominator and refuses to score a
partially filled sheet.
"""


def unit_index(rubric_id: str, submission_id: str) -> dict[str, dict]:
    path = CORPUS / "submissions" / f"{submission_id}.txt"
    units = chunk_pages(parse_submission(path))
    return {u.id: {"page": u.page, "section": u.section, "text": " ".join(u.text.split())}
            for u in units}


def candidates() -> list[dict]:
    """Every cited claim sentence in the frozen campaign's first-run outputs."""
    report = json.loads((CAMPAIGN / "A.json").read_text(encoding="utf-8"))
    rows: list[dict] = []
    for case in report["run_outputs"]:
        rubric_id, submission_id = case["rubric_id"], case["submission_id"]
        units = unit_index(rubric_id, submission_id)
        for item in case["agent_runs"][0]["assessments"]:
            draft = item["draft"]
            if draft["sufficiency"] == "insufficient":
                continue
            for sentence in re.split(r"(?<=[.!?])\s+", draft["explanation"] or ""):
                sentence = " ".join(sentence.split())
                ids = CITATION.findall(sentence)
                if not sentence or not ids:
                    continue
                for unit_id in dict.fromkeys(ids):
                    unit = units.get(unit_id)
                    if not unit:
                        continue
                    rows.append({
                        "rubric_id": rubric_id, "submission_id": submission_id,
                        "criterion_id": draft["criterion_id"],
                        "claim_sentence": sentence,
                        "cited_unit_id": unit_id,
                        "cited_unit_page": unit["page"], "cited_unit_section": unit["section"],
                        "cited_unit_text": unit["text"],
                    })
    # Stable order before sampling so the seed fully determines the draw.
    rows.sort(key=lambda r: (r["submission_id"], r["criterion_id"], r["cited_unit_id"],
                             r["claim_sentence"]))
    return rows


def draw(size: int, seed: int) -> tuple[list[dict], int]:
    population = candidates()
    rng = random.Random(seed)
    chosen = rng.sample(population, min(size, len(population)))
    chosen.sort(key=lambda r: (r["submission_id"], r["criterion_id"]))
    return chosen, len(population)


def write_sheet(out: Path, rows: list[dict], population: int, seed: int) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            writer.writerow({"item": index, **row, "supported": "", "note": "", "judge": ""})
    (out.parent / "INSTRUCTIONS.txt").write_text(INSTRUCTIONS, encoding="utf-8")
    (out.parent / "sample_provenance.json").write_text(json.dumps({
        "created_at_utc": datetime.now(UTC).isoformat(),
        "protocol": "docs/EVALUATION_PROTOCOL.md Addendum A.6",
        "source": "docs/evaluation_dev_frozen/A.json, first run of each rubric/submission",
        "population_cited_claims": population,
        "sample_size": len(rows),
        "seed": seed,
        "status": "blank; not measured until a named person scores it",
        "sampling": ("candidates sorted by (submission, criterion, unit, sentence) then "
                     "random.Random(seed).sample, so the draw is reproducible"),
        "prohibition": "An AI must not fill this in; that would not be human evidence.",
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def score(path: Path) -> dict:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
    allowed = {"yes", "partial", "no"}
    judged = [r for r in rows if (r.get("supported") or "").strip().lower() in allowed]
    if not judged:
        raise SystemExit(f"{path.name} has no judgements yet; faithfulness is not measured.")
    if len(judged) != len(rows):
        raise SystemExit(
            f"{path.name}: {len(judged)} of {len(rows)} rows judged. Finish the sheet; a partial "
            "sample has no denominator."
        )
    bad = [r["item"] for r in rows if (r.get("supported") or "").strip().lower() not in allowed]
    if bad:
        raise SystemExit(f"Rows {bad} use a value outside yes/partial/no.")
    counts = {label: sum(1 for r in judged if r["supported"].strip().lower() == label)
              for label in ("yes", "partial", "no")}
    judges = sorted({(r.get("judge") or "").strip() for r in judged if (r.get("judge") or "").strip()})
    if not judges:
        raise SystemExit("No judge name recorded; an unattributed sheet is not human evidence.")
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "sheet": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "judges": judges,
        "claims_judged": len(judged),
        "counts": counts,
        "faithfulness_supported_rate": counts["yes"] / len(judged),
        "supported_or_partial_rate": (counts["yes"] + counts["partial"]) / len(judged),
        "limits": [
            f"{len(judged)} claims from one build, judged by {len(judges)} person(s).",
            "Faithfulness checks support from the supplied evidence; it does not establish that the "
            "evidence is true.",
            "Judged against the cited passage only, not the whole document.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/faithfulness/sample_blank.csv")
    parser.add_argument("--size", type=int, default=SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--score", type=Path, default=None, help="score a completed sheet instead")
    args = parser.parse_args()

    if args.score:
        result = score(args.score.resolve())
        out = args.score.resolve().parent / "faithfulness_result.json"
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    rows, population = draw(args.size, args.seed)
    write_sheet(args.output.resolve(), rows, population, args.seed)
    print(f"{len(rows)} of {population} cited claims drawn with seed {args.seed}")
    print(f"wrote {args.output.relative_to(ROOT)} (blank) plus INSTRUCTIONS.txt "
          f"and sample_provenance.json")
    print("Faithfulness is NOT measured until a named person scores this sheet.")


if __name__ == "__main__":
    main()
