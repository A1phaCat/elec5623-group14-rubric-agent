"""Print a readable trace for one rubric-submission-criterion across A, B2 and B3.

`docs/EVALUATION_PROTOCOL.md` requires the final analysis to show, for at least
one ordinary, one dispersed/missing and one decoy case, the actual retrieved
span, the model output, the validation and revision, and the human reference.
Reading that out of the campaign JSON by hand is error-prone, so this does it.

    scripts/extract_traces.py --campaign docs/evaluation_dev_frozen \
        --submission s4_decoy_eval --criterion C3

Omit --criterion to print every criterion for that submission. Pass --markdown
to emit a block ready to paste into the report. Evidence text is read back from
the corpus named in the campaign manifest, so a trace cannot drift from the
inputs the run actually used.
"""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(campaign: Path) -> tuple[dict, dict, dict, dict]:
    manifest = json.loads((campaign / "manifest.json").read_text(encoding="utf-8"))
    comparison = json.loads((campaign / "comparison.json").read_text(encoding="utf-8"))
    reports = {}
    for name in ("A", "B3"):
        path = campaign / f"{name}.json"
        if path.is_file():
            reports[name] = json.loads(path.read_text(encoding="utf-8"))
    return manifest, comparison, reports, {}


def evidence_text(corpus: Path, rubric_id: str, submission_id: str, wanted: list[str]) -> dict[str, dict]:
    """Re-chunk the submission to recover the text behind each evidence id."""
    from rubric_agent.chunker import chunk_pages
    from rubric_agent.text_parser import parse_submission

    units = chunk_pages(parse_submission(corpus / "submissions" / f"{submission_id}.txt"))
    return {u.id: {"page": u.page, "section": u.section, "text": u.text}
            for u in units if not wanted or u.id in wanted}


def trace(campaign: Path, submission: str, criterion: str | None, markdown: bool) -> str:
    manifest, comparison, reports, _ = load(campaign)
    corpus = ROOT / manifest["settings"]["corpus"]
    rows = [d for d in comparison["reference_disagreements"] if d["submission_id"] == submission]
    golds = {(d["criterion_id"]): d for d in rows}

    out: list[str] = []
    criteria = [criterion] if criterion else sorted(golds)
    if not criteria:
        return f"No recorded reference disagreement for {submission}; it agreed on every criterion."

    for cid in criteria:
        record = golds.get(cid)
        if record is None:
            out.append(f"{submission}/{cid}: agreed with the reference on every system.")
            continue
        ref = record["preliminary_reference"]
        head = f"{submission} / {cid} — scenario {record['scenario']}, split {record['split']}"
        out.append(f"\n{'## ' if markdown else ''}{head}")
        out.append(f"Reference: sufficiency **{ref['sufficiency']}**, score {ref['score']}"
                   if markdown else
                   f"Reference: sufficiency {ref['sufficiency']}, score {ref['score']}")
        out.append(f"Systems differing from the reference: {', '.join(record['systems_differing_from_reference'])}")

        for system, output in record["outputs"].items():
            out.append("")
            out.append(f"{'### ' if markdown else ''}{system}")
            out.append(f"sufficiency {output['sufficiency']}, score {output['provisional_score']}, "
                       f"cited {output['evidence_ids']}")
            if output.get("flags"):
                out.append(f"flags: {output['flags']}")
            explanation = " ".join((output.get("explanation") or "").split())
            out.append("explanation: " + ("\n  " + "\n  ".join(textwrap.wrap(explanation, 96))
                                          if explanation else "(none)"))
            if output.get("draft_feedback"):
                feedback = " ".join(output["draft_feedback"].split())
                out.append("feedback: " + "\n  ".join(textwrap.wrap(feedback, 96)))

        # Retrieved evidence for system A, with the text behind each id.
        retrieved = None
        for case in reports.get("A", {}).get("run_outputs", []):
            if case["submission_id"] == submission:
                retrieved = case["agent_runs"][0]["retrieved_ids"].get(cid)
        if retrieved:
            out.append("")
            out.append(f"{'### ' if markdown else ''}Evidence A retrieved for {cid} (BM25 top-5, in rank order)")
            units = evidence_text(corpus, record["rubric_id"], submission, retrieved)
            for eid in retrieved:
                unit = units.get(eid)
                if not unit:
                    continue
                body = " ".join(unit["text"].split())
                marker = " <- cited" if eid in record["outputs"].get("A", {}).get("evidence_ids", []) else ""
                out.append(f"- {eid} p.{unit['page']} - {unit['section']}{marker}")
                out.append("    " + "\n    ".join(textwrap.wrap(body, 92)))
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, default=ROOT / "docs/evaluation_dev_frozen")
    parser.add_argument("--submission", required=True)
    parser.add_argument("--criterion", default=None)
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    print(trace(args.campaign.resolve(), args.submission, args.criterion, args.markdown))


if __name__ == "__main__":
    main()
