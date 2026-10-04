"""The marker checklist ignores keywords that only appear inside a denial."""

from pathlib import Path

from rubric_agent.coverage import top_band_coverage
from rubric_agent.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / "dataset" / "rubrics" / "engineering_report.md"


def test_decoy_evaluation_does_not_count_as_having_metrics():
    result = run_pipeline(ENG, ROOT / "dataset/submissions/s4_decoy_eval.txt", rubric_id="engineering_report", workers=1)
    crit = next(c for c in result.rubric.criteria if c.id == "C3")
    coverage = top_band_coverage(crit, result.retrieved["C3"])
    assert coverage is not None
    assert "metric" not in coverage.present
    assert "baseline" not in coverage.present
    assert coverage.missing


def test_method_sentence_counts_incremental():
    result = run_pipeline(ENG, ROOT / "dataset/submissions/s3_missing_eval.txt", rubric_id="engineering_report", workers=1)
    crit = next(c for c in result.rubric.criteria if c.id == "C2")
    coverage = top_band_coverage(crit, result.retrieved["C2"])
    assert coverage is not None
    assert "incremental" in coverage.present
