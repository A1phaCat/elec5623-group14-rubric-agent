"""Measure inter-annotator agreement, then build the adjudicated final-test labels.

Two commands, deliberately separate so the agreement numbers are computed and
saved from the untouched originals *before* anyone discusses a disagreement
(`docs/EVALUATION_PROTOCOL.md`, annotation procedure step 4):

    scripts/adjudicate_annotations.py agreement
    scripts/adjudicate_annotations.py build --adjudicated <file.csv>

`agreement` reads the per-annotator sheets, hashes them, and reports Cohen's
kappa, raw agreement and the three-class confusion matrix for sufficiency,
plus score MAE and exact agreement on the pairs where both annotators gave a
number. It refuses to run on an incomplete sheet rather than silently scoring
a subset.

`build` turns an adjudicated sheet into `dataset/final_test/labels.json` in the
GoldLabel shape the evaluator reads. It records the hashes of both originals
and the adjudicated file so a later report can prove which labels it used.

Neither command invents a label. Both fail if the cells are empty.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "dataset/final_test"
WORKSPACE = CORPUS / "annotation"
CLASSES = ("sufficient", "partial", "insufficient")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def _key(row: dict) -> tuple[str, str, str]:
    return row["rubric_id"], row["submission_id"], row["criterion_id"]


def read_sheet(path: Path) -> dict[tuple[str, str, str], dict]:
    if not path.is_file():
        raise SystemExit(f"Missing annotation sheet: {path}")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    parsed: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        sufficiency = (row.get("sufficiency") or "").strip().lower()
        raw_score = (row.get("score") or "").strip()
        if sufficiency not in CLASSES:
            raise SystemExit(
                f"{path.name} pair {row['pair']}: sufficiency is {row.get('sufficiency')!r}; "
                f"expected one of {CLASSES}. Complete the sheet before computing agreement."
            )
        if sufficiency == "insufficient":
            if raw_score:
                raise SystemExit(f"{path.name} pair {row['pair']}: insufficient must have an empty score")
            score = None
        else:
            if not raw_score:
                raise SystemExit(
                    f"{path.name} pair {row['pair']}: {sufficiency} needs a numeric score "
                    "(leave it empty only for insufficient)"
                )
            score = float(raw_score)
            maximum, step = float(row["max_mark"]), float(row["granularity"])
            if not 0 <= score <= maximum or abs(round(score / step) * step - score) > 1e-6:
                raise SystemExit(
                    f"{path.name} pair {row['pair']}: score {score} is outside the 0..{maximum} grid of {step}"
                )
        parsed[_key(row)] = {
            **{field: row[field] for field in ("pair", "rubric_id", "submission_id", "criterion_id", "scenario")},
            "sufficiency": sufficiency,
            "score": score,
            "rationale": (row.get("rationale") or "").strip(),
        }
    return parsed


def cohens_kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Unweighted kappa over the three sufficiency classes.

    Returns None when chance agreement is 1.0, which happens if both annotators
    used a single class throughout. That is undefined, not perfect agreement.
    """
    total = len(pairs)
    if not total:
        return None
    observed = sum(1 for left, right in pairs if left == right) / total
    left_counts, right_counts = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum((left_counts[c] / total) * (right_counts[c] / total) for c in CLASSES)
    if abs(1 - expected) < 1e-12:
        return None
    return (observed - expected) / (1 - expected)


def agreement(sheets: dict[str, Path]) -> dict:
    if len(sheets) != 2:
        raise SystemExit("Agreement needs exactly two annotator sheets")
    (left_name, left_path), (right_name, right_path) = sorted(sheets.items())
    left, right = read_sheet(left_path), read_sheet(right_path)
    if left.keys() != right.keys():
        raise SystemExit("The two sheets cover different pairs")

    keys = sorted(left)
    suff_pairs = [(left[k]["sufficiency"], right[k]["sufficiency"]) for k in keys]
    confusion = {f"{a}|{b}": 0 for a in CLASSES for b in CLASSES}
    for a, b in suff_pairs:
        confusion[f"{a}|{b}"] += 1

    both_scored = [k for k in keys if left[k]["score"] is not None and right[k]["score"] is not None]
    abs_errors = [abs(left[k]["score"] - right[k]["score"]) for k in both_scored]
    disagreements = [
        {
            "pair": left[k]["pair"], "rubric_id": k[0], "submission_id": k[1], "criterion_id": k[2],
            "scenario": left[k]["scenario"],
            left_name: {"sufficiency": left[k]["sufficiency"], "score": left[k]["score"],
                        "rationale": left[k]["rationale"]},
            right_name: {"sufficiency": right[k]["sufficiency"], "score": right[k]["score"],
                         "rationale": right[k]["rationale"]},
        }
        for k in keys
        if left[k]["sufficiency"] != right[k]["sufficiency"] or left[k]["score"] != right[k]["score"]
    ]

    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "independent originals, before adjudication",
        "annotators": [left_name, right_name],
        "source_files": {left_name: {"path": _display(left_path), "sha256": _digest(left_path)},
                         right_name: {"path": _display(right_path), "sha256": _digest(right_path)}},
        "pairs": len(keys),
        "sufficiency": {
            "raw_agreement": sum(1 for a, b in suff_pairs if a == b) / len(keys),
            "cohens_kappa": cohens_kappa(suff_pairs),
            "kappa_note": "null means both annotators used one class throughout, which is undefined, not perfect.",
            "confusion_rows_are_" + left_name + "_columns_are_" + right_name: confusion,
            "class_counts": {name: {c: sum(1 for k in keys if sheet[k]["sufficiency"] == c) for c in CLASSES}
                             for name, sheet in ((left_name, left), (right_name, right))},
        },
        "score": {
            "jointly_scored_pairs": len(both_scored),
            "pairs_where_only_one_scored": sum(
                1 for k in keys if (left[k]["score"] is None) != (right[k]["score"] is None)),
            "mae": sum(abs_errors) / len(abs_errors) if abs_errors else None,
            "exact_agreement": (sum(1 for e in abs_errors if e == 0) / len(abs_errors)) if abs_errors else None,
            "note": "MAE is conditional on both annotators emitting a number; it ignores the abstained pairs.",
        },
        "disagreements": disagreements,
        "limits": [
            "Two annotators on 27 synthetic pairs from six documents.",
            "The documents were authored with AI assistance inside this project; see corpus.json.",
            "Agreement on synthetic text is not agreement on real student submissions.",
        ],
    }


def build(adjudicated: Path, sheets: dict[str, Path]) -> dict:
    rows = read_sheet(adjudicated)
    manifest = json.loads((CORPUS / "corpus.json").read_text(encoding="utf-8"))
    splits = {entry["submission_id"]: entry["split"] for entry in manifest["submissions"]}
    scenarios = {entry["submission_id"]: entry["scenario"] for entry in manifest["submissions"]}

    labels = []
    for key in sorted(rows):
        row = rows[key]
        labels.append({
            "rubric_id": row["rubric_id"],
            "submission_id": row["submission_id"],
            "criterion_id": row["criterion_id"],
            # must_contain drives M3 relevance and is a retrieval annotation, not
            # a sufficiency judgement; the rationale text is not reused for it.
            "must_contain": [],
            "sufficiency": row["sufficiency"],
            "score": row["score"],
            "scenario": scenarios[row["submission_id"]],
            "split": splits[row["submission_id"]],
        })

    out = CORPUS / "labels.json"
    out.write_text(json.dumps(labels, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    provenance = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "labels": _display(out),
        "labels_sha256": _digest(out),
        "adjudicated_source": {"path": _display(adjudicated), "sha256": _digest(adjudicated)},
        "independent_originals": {name: {"path": _display(path), "sha256": _digest(path)}
                                  for name, path in sorted(sheets.items()) if path.is_file()},
        "pairs": len(labels),
        "class_counts": dict(Counter(row["sufficiency"] for row in labels)),
        "numeric_scores": sum(1 for row in labels if row["score"] is not None),
        "must_contain_status": "empty; M3 retrieval relevance is not annotated for this corpus and is reported as unmeasured",
    }
    (WORKSPACE / "labels_provenance.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return provenance


def _sheets(names: list[str]) -> dict[str, Path]:
    return {name: WORKSPACE / f"annotator_{name}.csv" for name in names}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    ag = sub.add_parser("agreement", help="compute agreement from the untouched originals")
    ag.add_argument("--annotators", nargs=2, default=["A", "B"])
    ag.add_argument("--output", type=Path, default=WORKSPACE / "agreement.json")
    bl = sub.add_parser("build", help="write dataset/final_test/labels.json from an adjudicated sheet")
    bl.add_argument("--adjudicated", type=Path, default=WORKSPACE / "adjudicated.csv")
    bl.add_argument("--annotators", nargs="+", default=["A", "B"])
    args = parser.parse_args()

    if args.cmd == "agreement":
        report = agreement(_sheets(args.annotators))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        suff, score = report["sufficiency"], report["score"]
        print(f"pairs {report['pairs']}  raw agreement {suff['raw_agreement']:.3f}  kappa {suff['cohens_kappa']}")
        print(f"jointly scored {score['jointly_scored_pairs']}  MAE {score['mae']}  exact {score['exact_agreement']}")
        print(f"{len(report['disagreements'])} disagreements -> {_display(args.output)}")
    else:
        if not args.adjudicated.is_file():
            raise SystemExit(
                f"No adjudicated sheet at {args.adjudicated}. Run `agreement` first, save it, and only then "
                "resolve disagreements into an adjudicated copy."
            )
        provenance = build(args.adjudicated, _sheets(args.annotators))
        print(json.dumps(provenance, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
