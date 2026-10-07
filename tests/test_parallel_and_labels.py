"""Concurrency of criterion calls, and the blank second-pass sheet."""

from __future__ import annotations

import csv
import time
from pathlib import Path

from scripts.export_second_pass import export_second_pass

from rubric_agent.gateway import FixtureGateway
from rubric_agent.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / "dataset" / "rubrics" / "engineering_report.md"
S1 = ROOT / "dataset" / "submissions" / "s1_standard.txt"


class SlowGateway(FixtureGateway):
    def assess(self, criterion, evidence):
        time.sleep(0.25)
        return super().assess(criterion, evidence)


def test_criteria_overlap_and_keep_rubric_order():
    started = time.perf_counter()
    result = run_pipeline(ENG, S1, gateway=SlowGateway(), rubric_id="engineering_report")
    elapsed = time.perf_counter() - started
    ids = [item.draft.criterion_id for item in result.assessments]
    assert ids == [c.id for c in result.rubric.criteria]
    assert [entry.criterion_id for entry in result.logs] == ids
    # Five serial sleeps would be about 1.25s. Overlap should finish well under that.
    assert elapsed < 0.9


def test_second_pass_sheet_is_blank(tmp_path):
    path = tmp_path / "to_label.csv"
    n = export_second_pass(path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert n == 62 and len(rows) == 62
    assert all(row["sufficiency"] == "" and row["score"] == "" for row in rows)
    decoy = next(row for row in rows if row["submission_id"] == "s4_decoy_eval" and row["criterion_id"] == "C3")
    assert "keyword without specifying" in decoy["submission_text"]
    assert decoy["criterion_name"] == "Evaluation plan"
