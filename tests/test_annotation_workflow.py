"""The annotation tooling must never invent a label or hide an incomplete sheet.

Agreement statistics are the only independent evidence this project will have
about its reference labels, so the code that produces them is tested against
hand-built sheets. Every sheet here lives in tmp_path: these tests must not
write anything into dataset/final_test/annotation/.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from scripts.adjudicate_annotations import CLASSES, agreement, cohens_kappa, read_csv_rows, read_sheet
from scripts.export_annotation_sheets import FIELDS, export_sheets

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "dataset/final_test"


LOW = "low"
HIGH = "high"


def _grid_score(row: dict, band: str) -> str:
    """A score that is on this criterion's grid, so the fixture tests the logic under test."""
    step, maximum = float(row["granularity"]), float(row["max_mark"])
    return str(step if band == LOW else maximum)


def _sheet(path: Path, answers: list[tuple[str, str]]) -> Path:
    """Write a sheet whose 27 rows mirror the real corpus but carry given answers.

    A score of LOW or HIGH is resolved per row, because the two rubrics have
    different maxima and step sizes.
    """
    template = list(csv.DictReader((CORPUS / "annotation" / "annotator_A.csv").open(encoding="utf-8")))
    assert len(template) == len(answers)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row, (sufficiency, score) in zip(template, answers, strict=True):
            resolved = _grid_score(row, score) if score in (LOW, HIGH) else score
            writer.writerow({**row, "sufficiency": sufficiency, "score": resolved, "rationale": "test"})
    return path


def _answers(sufficiency: str, score: str) -> list[tuple[str, str]]:
    return [(sufficiency, score)] * 27


def test_exported_sheets_are_blank_and_cover_the_declared_corpus(tmp_path):
    written = export_sheets(["X"], corpus=CORPUS)
    try:
        rows = list(csv.DictReader(written["X"].open(encoding="utf-8")))
        manifest = json.loads((CORPUS / "corpus.json").read_text(encoding="utf-8"))
        assert len(rows) == 27
        assert {row["submission_id"] for row in rows} == {e["submission_id"] for e in manifest["submissions"]}
        assert all(not row["sufficiency"] and not row["score"] and not row["rationale"] for row in rows)
        # The annotator needs the descriptors to judge against.
        assert all(row["level_descriptors"] and row["submission_text"] for row in rows)
    finally:
        written["X"].unlink()


def test_export_refuses_to_discard_existing_annotations(tmp_path):
    written = export_sheets(["Y"], corpus=CORPUS)
    path = written["Y"]
    try:
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        rows[0]["sufficiency"] = "sufficient"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        with pytest.raises(SystemExit, match="refusing to overwrite"):
            export_sheets(["Y"], corpus=CORPUS)
    finally:
        path.unlink()


def test_blank_cells_are_an_error_not_a_skipped_pair(tmp_path):
    path = _sheet(tmp_path / "blank.csv", [("", "")] * 27)
    with pytest.raises(SystemExit, match="Complete the sheet"):
        read_sheet(path)


def test_insufficient_must_not_carry_a_score(tmp_path):
    path = _sheet(tmp_path / "bad.csv", _answers("insufficient", LOW))
    with pytest.raises(SystemExit, match="empty score"):
        read_sheet(path)


def test_scored_classes_must_carry_a_number(tmp_path):
    path = _sheet(tmp_path / "bad.csv", _answers("partial", ""))
    with pytest.raises(SystemExit, match="needs a numeric score"):
        read_sheet(path)


def test_score_must_respect_the_rubric_grid(tmp_path):
    path = _sheet(tmp_path / "bad.csv", _answers("sufficient", "2.3"))
    with pytest.raises(SystemExit, match="outside the"):
        read_sheet(path)


def test_identical_sheets_agree_completely_but_kappa_is_undefined(tmp_path):
    sheets = {
        "A": _sheet(tmp_path / "a.csv", _answers("sufficient", LOW)),
        "B": _sheet(tmp_path / "b.csv", _answers("sufficient", LOW)),
    }
    report = agreement(sheets)
    assert report["pairs"] == 27
    assert report["sufficiency"]["raw_agreement"] == 1.0
    # One class throughout: chance agreement is 1.0, so kappa is undefined.
    assert report["sufficiency"]["cohens_kappa"] is None
    assert report["score"]["mae"] == 0.0 and report["score"]["exact_agreement"] == 1.0
    assert report["disagreements"] == []
    assert report["status"].startswith("independent originals")


def test_disagreements_are_listed_with_both_rationales(tmp_path):
    a = _answers("sufficient", LOW)
    b = _answers("sufficient", LOW)
    b[0] = ("insufficient", "")
    b[1] = ("sufficient", HIGH)
    sheets = {"A": _sheet(tmp_path / "a.csv", a), "B": _sheet(tmp_path / "b.csv", b)}
    report = agreement(sheets)
    assert len(report["disagreements"]) == 2
    first = report["disagreements"][0]
    assert first["A"]["sufficiency"] == "sufficient" and first["B"]["sufficiency"] == "insufficient"
    assert report["sufficiency"]["raw_agreement"] == pytest.approx(26 / 27)
    assert report["sufficiency"]["cohens_kappa"] is not None
    # B abstained on one pair, so that pair leaves the score comparison.
    assert report["score"]["jointly_scored_pairs"] == 26
    assert report["score"]["pairs_where_only_one_scored"] == 1
    assert all(path_info["sha256"] for path_info in report["source_files"].values())


def test_kappa_corrects_for_chance_and_reports_null_when_undefined():
    assert cohens_kappa([("sufficient", "sufficient"), ("partial", "partial")]) == pytest.approx(1.0)
    assert cohens_kappa([("sufficient", "partial"), ("partial", "sufficient")]) == pytest.approx(-1.0)
    assert cohens_kappa([("sufficient", "sufficient")] * 5) is None
    assert cohens_kappa([]) is None


def test_confusion_matrix_covers_every_class_pair_and_totals_the_pairs(tmp_path):
    a = _answers("sufficient", LOW)
    a[0] = ("partial", LOW)
    sheets = {"A": _sheet(tmp_path / "a.csv", a), "B": _sheet(tmp_path / "b.csv", _answers("sufficient", LOW))}
    report = agreement(sheets)
    confusion = next(v for k, v in report["sufficiency"].items() if k.startswith("confusion_rows"))
    assert len(confusion) == len(CLASSES) ** 2
    assert sum(confusion.values()) == 27
    assert confusion["partial|sufficient"] == 1


def test_excel_utf8_bom_is_tolerated(tmp_path):
    """Excel's "CSV UTF-8" writes a BOM; a teammate's upload must still parse.

    Under plain utf-8 the first column name becomes "\ufeffpair" and every
    lookup of "pair" raises KeyError, which would have failed at adjudication
    after the annotation work was already done.
    """
    path = _sheet(tmp_path / "bom.csv", _answers("sufficient", LOW))
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    rows = read_csv_rows(path)
    assert "pair" in rows[0] and "\ufeffpair" not in rows[0]
    assert len(read_sheet(path)) == 27


def test_non_utf8_sheet_explains_how_to_re_save(tmp_path):
    """Excel's plain "CSV" uses a regional encoding, which is not decodable here."""
    path = tmp_path / "latin1.csv"
    header = ",".join(FIELDS)
    row = ",".join(["1", "engineering_report", "f01", "ordinary", "C1", "caf\u00e9",
                    "4.0", "1.0", "d", "t", "sufficient", "1.0", "r"])
    path.write_bytes(f"{header}\n{row}\n".encode("latin-1"))
    with pytest.raises(SystemExit, match="CSV UTF-8"):
        read_csv_rows(path)


def test_renamed_or_dropped_columns_are_named_in_the_error(tmp_path):
    path = _sheet(tmp_path / "renamed.csv", _answers("sufficient", LOW))
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace("criterion_id", "criterion")
    path.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(SystemExit, match="criterion_id"):
        read_csv_rows(path)


def test_header_only_sheet_is_rejected(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text(",".join(FIELDS) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="no rows"):
        read_csv_rows(path)


def test_mismatched_sheets_are_rejected(tmp_path):
    full = _sheet(tmp_path / "a.csv", _answers("sufficient", LOW))
    rows = list(csv.DictReader(full.open(encoding="utf-8")))[:-1]
    short = tmp_path / "b.csv"
    with short.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(SystemExit, match="different pairs"):
        agreement({"A": full, "B": short})


def test_real_annotation_sheets_are_blank_or_valid():
    """A sheet must be either untouched or correctly filled in — never half-done.

    This runs in CI while real annotation is in progress, so it must not punish
    a teammate for doing the work. A blank sheet is the starting state; a
    completed sheet must parse under the same rules the adjudicator applies, so
    a sheet that was filled in wrongly (bad label, off-grid score, a score on an
    `insufficient` row, an Excel BOM) fails here rather than at adjudication.
    """
    for name in ("A", "B"):
        path = CORPUS / "annotation" / f"annotator_{name}.csv"
        rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
        assert len(rows) == 27, f"{path.name} should keep all 27 pairs"
        filled = [row for row in rows if row["sufficiency"] or row["score"]]
        if not filled:
            continue
        assert len(filled) == 27, (
            f"{path.name} is partially filled ({len(filled)}/27). Finish it or clear it; "
            "a partial sheet cannot support an agreement statistic."
        )
        # Raises SystemExit with a specific message if anything is inconsistent.
        parsed = read_sheet(path)
        assert len(parsed) == 27


def test_corpus_labels_only_exist_once_both_sheets_are_complete():
    """final_test/labels.json must be derived from completed sheets, not authored."""
    sheets = {}
    for name in ("A", "B"):
        path = CORPUS / "annotation" / f"annotator_{name}.csv"
        rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
        sheets[name] = any(row["sufficiency"] or row["score"] for row in rows)
    if (CORPUS / "labels.json").exists():
        assert all(sheets.values()), (
            "final_test/labels.json exists but an annotation sheet is still blank; "
            "labels must come from two completed independent sheets via "
            "scripts/adjudicate_annotations.py build"
        )
        assert (CORPUS / "annotation" / "agreement.json").exists(), (
            "labels.json exists without agreement.json; agreement must be computed from the "
            "untouched originals before adjudication"
        )
