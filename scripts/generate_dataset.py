#!/usr/bin/env python3
"""Write the synthetic evaluation corpus (no student data)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUBRICS = ROOT / "dataset" / "rubrics"
SUBS = ROOT / "dataset" / "submissions"

ENG = """# Engineering report rubric

CRITERION: Problem definition
ID: C1
MAX: 4
GRANULARITY: 1
0: Problem is missing or unrecognisable
2: Problem is stated but not scoped
4: Problem is scoped with affected users and a testable gap

CRITERION: Methodology
ID: C2
MAX: 4
GRANULARITY: 1
0: No method
2: Method named without a sequence
4: Method is incremental, testable and provider-independent

CRITERION: Evaluation plan
ID: C3
MAX: 4
GRANULARITY: 1
0: No evaluation
2: Metrics listed without a procedure
4: Metrics, baselines, scenarios and labelled data are specified

CRITERION: Results and discussion
ID: C4
MAX: 4
GRANULARITY: 1
0: No results
2: Results without interpretation
4: Results are interpreted against the method and limitations

CRITERION: Communication
ID: C5
MAX: 2
GRANULARITY: 1
0: Unreadable structure
1: Headings exist but terminology drifts
2: Consistent headings, captions and terminology
"""

HALF = """# Half-mark unusual rubric

| ID | Criterion | Max | 0 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- | --- |
| H1 | Scope | 1.0 | Missing | Partial boundary | Clear in-scope and out-of-scope |
| H2 | Evidence use | 1.0 | None | Some citations | Traceable citations |
| H3 | Feasibility | 1.0 | Implausible | Partial plan | Semester-feasible plan |
| H4 | Presentation | 1.0 | Broken layout | Readable | Consistent tables |
"""

PROPOSAL = """# Proposal rubric (numbered list format)

1. Problem and motivation (5 marks)
- 0: No problem stated
- 2.5: Problem stated without stakeholders or evidence of need
- 5: Problem, stakeholders and evidence of need are all explicit

2. Requirements (5 marks)
- 0: No requirements
- 2.5: Requirements listed without priority or acceptance criteria
- 5: Prioritised requirements with measurable acceptance criteria

3. Methodology (5 marks)
- 0: No method
- 2.5: Method described without iterations or tests
- 5: Incremental iterations with automated tests and a fixture model

4. Feasibility and risks (5 marks)
- 0: No plan
- 2.5: Timeline given without risks
- 5: Weekly timeline with a risk register and mitigations
"""

HELDOUT = {"s5_long", "s9_strong_eval_weak_comm", "s10_all_partial", "p3_decoy"}

FILLER = (
    "Background filler paragraph used only to lengthen the document. "
    "It discusses campus weather, timetable logistics and unrelated library hours "
    "and must not be treated as evidence for any rubric criterion. "
)


def page(n: int, section: str, body: str) -> str:
    return f"===PAGE {n}===\n# {section}\n\n{body.strip()}\n"


def standard() -> str:
    return "\n".join([
        page(1, "Introduction", "The scoped marking-workload gap for long analytic rubrics is that tutors repeatedly search the same report for criterion-specific evidence."),
        page(2, "Users", "Affected users are university markers and unit coordinators who need a testable link from each criterion to a source span."),
        page(3, "Methodology", "Development is incremental: rubric parsing, then BM25 retrieval, then a fixture adapter for tests, then a validator that rejects unknown IDs."),
        page(4, "Architecture", "The assessment model is provider-independent and never receives the full submission."),
        page(5, "Evaluation plan", "The labelled evaluation set uses Recall@5, citation accuracy and two baselines: manual marking and direct whole-document LLM grading. Test scenarios include missing-criterion and keyword-decoy cases."),
        page(6, "Results", "On the synthetic corpus the method recovered criterion evidence and the discussion notes that scores remain provisional until a marker confirms them."),
        page(7, "Limitations", "Limitations include the small labelled set and the restriction to text-only submissions."),
        page(8, "Communication", "Each figure caption uses consistent terminology and numbered headings without drifting labels."),
    ])


def dispersed() -> str:
    return "\n".join([
        page(1, "Opening", "The scoped marking-workload gap is repeated evidence search across a 15-page report."),
        page(2, "Method start", "The incremental BM25 retrieval path is the first implemented stage."),
        page(3, "Unrelated", FILLER * 3),
        page(4, "Still unrelated", FILLER * 3),
        page(5, "Method middle", "A fixture adapter for tests lets the pipeline run without live model calls."),
        page(6, "Padding", FILLER * 4),
        page(7, "Users", "Affected users remain human markers who confirm every score."),
        page(8, "Method end", "The validator rejects unknown IDs before anything reaches the review UI."),
        page(9, "Evaluation plan", "Metrics include Recall@5 and citation accuracy against a labelled evaluation set with a manual baseline and a direct-LLM baseline."),
        page(10, "Results", "Results show retrieved spans from three non-adjacent method sections and the discussion treats this as a recall check."),
        page(11, "Limits", "Limitations: synthetic data only."),
        page(12, "Communication", "Numbered headings and a single figure caption keep consistent terminology."),
    ])


def missing_eval() -> str:
    return "\n".join([
        page(1, "Problem", "The scoped marking-workload gap is unverifiable AI scores on long reports."),
        page(2, "Users", "Affected users are markers who must still make the final decision."),
        page(3, "Methodology", "The incremental method uses BM25 retrieval and a fixture adapter for tests plus a validator that rejects unknown IDs."),
        page(4, "Results", "Narrative results describe a working parser; the discussion admits there is no measurement section."),
        page(5, "Communication", "Headings are consistent and the only figure caption names the parser."),
    ])


def decoy_eval() -> str:
    return "\n".join([
        page(1, "Problem", "The scoped marking-workload gap is opaque chatbot grading."),
        page(2, "Users", "Affected users include tutors marking proposals."),
        page(3, "Methodology", "An incremental BM25 retrieval path and fixture adapter for tests feed a validator that rejects unknown IDs."),
        page(4, "Evaluation mention", "We mention evaluation only as a keyword without specifying metrics or a baseline. This sentence is a decoy and does not include Recall@5, labelled data, or test scenarios."),
        page(5, "Results", "Results are anecdotal. The discussion says the demo 'felt fine'."),
        page(6, "Communication", "Consistent terminology appears in headings and one figure caption."),
    ])


def long_doc() -> str:
    pages = [
        page(1, "Problem", "The scoped marking-workload gap grows with report length, which this 12-page file represents."),
        page(2, "Users", "Affected users still need a testable gap statement and visible evidence."),
        page(3, "Methodology", "Incremental BM25 retrieval, a fixture adapter for tests, and a validator that rejects unknown IDs stay in scope."),
        page(4, "Evaluation plan", "The labelled evaluation set records Recall@5, citation accuracy, a manual baseline and a direct-LLM baseline."),
        page(5, "Results", "Latency results on this long file are logged; the discussion compares them with the 120-second target."),
        page(6, "Communication", "Consistent terminology and figure captions continue through the filler pages."),
    ]
    for i in range(7, 13):
        pages.append(page(i, f"Appendix filler {i}", FILLER * 8))
    return "\n".join(pages)


def variant(seed: str, problem: str, method: str, ev: str, results: str, comm: str) -> str:
    return "\n".join([
        page(1, "Problem", problem),
        page(2, "Methodology", method),
        page(3, "Evaluation plan", ev),
        page(4, "Results", results),
        page(5, "Communication", comm),
        page(6, "Notes", f"Variant {seed}. {FILLER}"),
    ])


VARIANTS = {
    "s6_weak_problem": (
        "Students write reports. No scoped marking-workload gap is given.",
        "Incremental BM25 retrieval and a fixture adapter for tests sit behind a validator that rejects unknown IDs.",
        "The labelled evaluation set uses Recall@5, citation accuracy, a manual baseline and a direct-LLM baseline.",
        "Results include a small table; the discussion links them to retrieval quality.",
        "Headings, one figure caption and consistent terminology are present.",
    ),
    "s7_partial_results": (
        "The scoped marking-workload gap is missing page locators on AI comments.",
        "The incremental method keeps BM25 retrieval, a fixture adapter for tests and a validator that rejects unknown IDs.",
        "Metrics on the labelled evaluation set are Recall@5 and citation accuracy versus a manual baseline and a direct-LLM baseline.",
        "A single number is stated with no discussion of limitations.",
        "Consistent terminology is used in headings.",
    ),
    "s8_missing_method": (
        "The scoped marking-workload gap is unverifiable provisional scores.",
        "We will use AI somehow.",
        "The labelled evaluation set still lists Recall@5, citation accuracy, a manual baseline and a direct-LLM baseline.",
        "Results are described as pending; the discussion is empty.",
        "A figure caption exists and headings stay consistent.",
    ),
    "s9_strong_eval_weak_comm": (
        "The scoped marking-workload gap is criterion-level evidence search.",
        "Incremental BM25 retrieval, a fixture adapter for tests and a validator that rejects unknown IDs are specified.",
        "The labelled evaluation set defines Recall@5, citation accuracy, unsupported-judgement rate, a manual baseline and a direct-LLM baseline, plus decoy and missing-criterion scenarios.",
        "Results beat the direct-LLM baseline on unsupported judgements; the discussion notes remaining parse errors.",
        "Text wall with no headings figure caption or consistent terminology.",
    ),
    "s10_all_partial": (
        "A marking-workload gap is hinted but not scoped.",
        "BM25 is named without an incremental sequence or a fixture adapter for tests.",
        "Recall@5 is named but the labelled evaluation set and baselines are omitted.",
        "Results appear as raw numbers without discussion.",
        "Headings exist but terminology drifts between 'score', 'mark' and 'grade' without a figure caption.",
    ),
}


def proposal_doc(problem: str, reqs: str, method: str, feas: str, extra: str = "") -> str:
    return "\n".join([
        page(1, "Problem and motivation", problem),
        page(2, "Requirements", reqs),
        page(3, "Methodology", method),
        page(4, "Feasibility and risks", feas),
        page(5, "Appendix", extra or FILLER * 2),
    ])


PROPOSALS = {
    "p1_strong": proposal_doc(
        "The problem is repeated evidence search by markers; stakeholders are tutors and coordinators, and evidence of need comes from marker interviews and a workload survey.",
        "Requirements are prioritised as Must, Should and Could, and each has a measurable acceptance criteria row such as Recall@5 at or above 0.85.",
        "Development runs in incremental iterations; each iteration ends with automated tests and a fixture model adapter so the pipeline runs offline.",
        "A weekly timeline covers Weeks 7 to 13 and a risk register lists mitigations for model access, extraction errors and annotation delay.",
    ),
    "p2_gaps": proposal_doc(
        "The problem is that marking is slow. Stakeholders are not named and no evidence of need is offered.",
        "Requirements are listed as a flat set without priority and without acceptance criteria.",
        "The method is described once; there are no iterations and no tests are planned.",
        "A timeline is given by week but risks are not discussed.",
    ),
    "p3_decoy": proposal_doc(
        "The problem is evidence search by markers. Stakeholders are tutors; the evidence of need is a survey of twelve tutors.",
        "This section uses the words priority and acceptance criteria but does not attach either to any requirement.",
        "We say incremental iterations and automated tests here without describing a single iteration or test, and no fixture model exists.",
        "A weekly timeline is provided and a risk register lists mitigations for each risk.",
    ),
}


LABELS = []


def add(sub, cid, phrases, sufficiency, score, scenario="S1", rubric="engineering_report"):
    LABELS.append({
        "rubric_id": rubric,
        "submission_id": sub,
        "criterion_id": cid,
        "must_contain": phrases,
        "sufficiency": sufficiency,
        "score": score,
        "scenario": scenario,
        "split": "heldout" if sub in HELDOUT else "dev",
    })


def addp(sub, cid, phrases, sufficiency, score, scenario="S1"):
    add(sub, cid, phrases, sufficiency, score, scenario, rubric="proposal_rubric")


def main() -> None:
    RUBRICS.mkdir(parents=True, exist_ok=True)
    SUBS.mkdir(parents=True, exist_ok=True)
    (RUBRICS / "engineering_report.md").write_text(ENG, encoding="utf-8")
    (RUBRICS / "half_mark.md").write_text(HALF, encoding="utf-8")
    (RUBRICS / "proposal_rubric.md").write_text(PROPOSAL, encoding="utf-8")
    _write_mini_pdf(RUBRICS / "proposal_rubric_mini.pdf", [
        "1. Scope (2 marks)", "- 0: Missing", "- 1: Partial", "- 2: Clear scope",
        "2. Evidence (2 marks)", "- 0: None", "- 2: Traceable",
    ])
    files = {
        "s1_standard": standard(),
        "s2_dispersed": dispersed(),
        "s3_missing_eval": missing_eval(),
        "s4_decoy_eval": decoy_eval(),
        "s5_long": long_doc(),
    }
    for name, parts in VARIANTS.items():
        files[name] = variant(name, *parts)
    files.update(PROPOSALS)
    for name, text in files.items():
        (SUBS / f"{name}.txt").write_text(text, encoding="utf-8")

    add("s1_standard", "C1", ["scoped marking-workload gap"], "sufficient", 4)
    add("s1_standard", "C2", ["fixture adapter for tests", "validator that rejects unknown IDs"], "sufficient", 4)
    add("s1_standard", "C3", ["labelled evaluation set", "Recall@5"], "sufficient", 4)
    add("s1_standard", "C4", ["discussion notes that scores remain provisional"], "sufficient", 4)
    add("s1_standard", "C5", ["figure caption", "consistent terminology"], "sufficient", 2)

    add("s2_dispersed", "C1", ["scoped marking-workload gap"], "sufficient", 4, "S2")
    add("s2_dispersed", "C2", ["incremental BM25 retrieval path", "fixture adapter for tests", "validator rejects unknown IDs"], "sufficient", 4, "S2")
    add("s2_dispersed", "C3", ["labelled evaluation set"], "sufficient", 4, "S2")
    add("s2_dispersed", "C4", ["three non-adjacent method sections"], "sufficient", 4, "S2")
    add("s2_dispersed", "C5", ["figure caption"], "sufficient", 2, "S2")

    add("s3_missing_eval", "C1", ["scoped marking-workload gap"], "sufficient", 4, "S3")
    add("s3_missing_eval", "C2", ["fixture adapter for tests"], "sufficient", 4, "S3")
    add("s3_missing_eval", "C3", ["labelled evaluation set"], "insufficient", None, "S3")
    add("s3_missing_eval", "C4", ["no measurement section"], "partial", 2, "S3")
    add("s3_missing_eval", "C5", ["figure caption"], "sufficient", 2, "S3")

    add("s4_decoy_eval", "C1", ["scoped marking-workload gap"], "sufficient", 4, "S4")
    add("s4_decoy_eval", "C2", ["fixture adapter for tests"], "sufficient", 4, "S4")
    add("s4_decoy_eval", "C3", ["keyword without specifying"], "insufficient", None, "S4")
    add("s4_decoy_eval", "C4", ["anecdotal"], "partial", 2, "S4")
    add("s4_decoy_eval", "C5", ["figure caption"], "sufficient", 2, "S4")

    add("s5_long", "C1", ["scoped marking-workload gap"], "sufficient", 4, "S5")
    add("s5_long", "C2", ["fixture adapter for tests"], "sufficient", 4, "S5")
    add("s5_long", "C3", ["labelled evaluation set"], "sufficient", 4, "S5")
    add("s5_long", "C4", ["120-second target"], "sufficient", 4, "S5")
    add("s5_long", "C5", ["figure captions"], "sufficient", 2, "S5")

    add("s6_weak_problem", "C1", ["No scoped marking-workload gap"], "insufficient", None)
    add("s6_weak_problem", "C2", ["fixture adapter for tests"], "sufficient", 4)
    add("s6_weak_problem", "C3", ["labelled evaluation set"], "sufficient", 4)
    add("s6_weak_problem", "C4", ["discussion links them"], "sufficient", 4)
    add("s6_weak_problem", "C5", ["figure caption"], "sufficient", 2)

    add("s7_partial_results", "C1", ["scoped marking-workload gap"], "sufficient", 4)
    add("s7_partial_results", "C2", ["fixture adapter for tests"], "sufficient", 4)
    add("s7_partial_results", "C3", ["labelled evaluation set"], "sufficient", 4)
    add("s7_partial_results", "C4", ["no discussion of limitations"], "partial", 2)
    add("s7_partial_results", "C5", ["consistent terminology"], "partial", 1)

    add("s8_missing_method", "C1", ["scoped marking-workload gap"], "sufficient", 4)
    add("s8_missing_method", "C2", ["use AI somehow"], "insufficient", None)
    add("s8_missing_method", "C3", ["labelled evaluation set"], "sufficient", 4)
    add("s8_missing_method", "C4", ["discussion is empty"], "insufficient", None)
    add("s8_missing_method", "C5", ["figure caption"], "sufficient", 2)

    add("s9_strong_eval_weak_comm", "C1", ["scoped marking-workload gap"], "sufficient", 4)
    add("s9_strong_eval_weak_comm", "C2", ["fixture adapter for tests"], "sufficient", 4)
    add("s9_strong_eval_weak_comm", "C3", ["unsupported-judgement rate"], "sufficient", 4)
    add("s9_strong_eval_weak_comm", "C4", ["direct-LLM baseline"], "sufficient", 4)
    add("s9_strong_eval_weak_comm", "C5", ["no headings figure caption"], "insufficient", None)

    add("s10_all_partial", "C1", ["not scoped"], "partial", 2)
    add("s10_all_partial", "C2", ["without an incremental sequence"], "partial", 2)
    add("s10_all_partial", "C3", ["baselines are omitted"], "partial", 2)
    add("s10_all_partial", "C4", ["without discussion"], "partial", 2)
    add("s10_all_partial", "C5", ["terminology drifts"], "partial", 1)

    addp("p1_strong", "C1", ["stakeholders are tutors", "evidence of need"], "sufficient", 5)
    addp("p1_strong", "C2", ["prioritised as Must", "acceptance criteria"], "sufficient", 5)
    addp("p1_strong", "C3", ["incremental iterations", "fixture model adapter"], "sufficient", 5)
    addp("p1_strong", "C4", ["weekly timeline", "risk register"], "sufficient", 5)

    addp("p2_gaps", "C1", ["Stakeholders are not named"], "partial", 2.5, "S3")
    addp("p2_gaps", "C2", ["without priority"], "partial", 2.5, "S3")
    addp("p2_gaps", "C3", ["no iterations"], "partial", 2.5, "S3")
    addp("p2_gaps", "C4", ["risks are not discussed"], "partial", 2.5, "S3")

    addp("p3_decoy", "C1", ["survey of twelve tutors"], "sufficient", 5, "S4")
    addp("p3_decoy", "C2", ["does not attach either"], "insufficient", None, "S4")
    addp("p3_decoy", "C3", ["without describing a single iteration"], "insufficient", None, "S4")
    addp("p3_decoy", "C4", ["risk register lists mitigations"], "sufficient", 5, "S4")

    (ROOT / "dataset" / "labels.json").write_text(json.dumps(LABELS, indent=2), encoding="utf-8")
    _write_mini_pdf(SUBS / "mini.pdf", ["SECTION: Methods Fixture adapter for tests"])
    print(f"wrote {len(files)} submissions and {len(LABELS)} labels "
          f"({sum(1 for lab in LABELS if lab['split'] == 'heldout')} held-out)")


def _pdf_escape(text: str) -> bytes:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("latin-1")


def _write_mini_pdf(path: Path, lines: list[str]) -> None:
    """Minimal text-extractable PDF (one page) without any PDF library."""
    parts = [b"BT /F1 12 Tf 72 740 Td 14 TL"]
    for line in lines:
        parts.append(b"(" + _pdf_escape(line) + b") Tj T*")
    parts.append(b"ET")
    stream = b"\n".join(parts)
    objects = [
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n",
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n",
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n",
        b"4 0 obj<</Length %d>>stream\n" % len(stream) + stream + b"\nendstream\nendobj\n",
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n",
    ]
    header = b"%PDF-1.4\n"
    offsets = [0]
    cursor = len(header)
    body = b""
    for obj in objects:
        offsets.append(cursor)
        body += obj
        cursor += len(obj)
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n" + str(len(header) + len(body)).encode() + b"\n%%EOF\n"
    path.write_bytes(header + body + xref + trailer)


if __name__ == "__main__":
    main()
