"""Regression tests for misleading denominators, comparisons and provenance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rubric_agent.cli import main
from rubric_agent.eval import _Acc, evaluate_corpus, load_labels, quadratic_weighted_kappa, write_markdown_report
from rubric_agent.gateway import FixtureGateway

DATASET = Path(__file__).resolve().parents[1] / "dataset"


def test_abstention_is_coverage_loss_not_zero_error():
    acc = _Acc()
    acc.add_score(4, 4, 1, 4, "C1")
    acc.add_score(None, 0, 1, 4, "C1")
    result = acc.summary()
    assert result["score_mae"] == 0
    assert result["score_coverage"] == 0.5
    assert result["scored_pairs"] == 1 and result["gold_scored_pairs"] == 2
    assert result["abstained_on_gold_scored"] == 1
    assert result["score_qwk"] is None  # one constant pair has undefined chance agreement


def test_empty_denominators_are_unmeasured():
    result = _Acc().summary()
    for metric in ("unsupported_rate", "sufficiency_accuracy", "sufficiency_macro_f1", "score_coverage", "score_mae"):
        assert result[metric] is None
    assert quadratic_weighted_kappa([1, 1], [1, 1], 3) is None


def test_qwk_does_not_pool_distinct_criterion_scales():
    acc = _Acc()
    for pred, gold in [(0, 0), (4, 4)]:
        acc.add_score(pred, gold, 1, 4, "engineering/C1")
    for pred, gold in [(0, 2), (2, 0)]:
        acc.add_score(pred, gold, 1, 2, "proposal/C1")
    result = acc.summary()
    assert result["score_qwk"] == 0  # equal-weight perfect (+1) and reversed (-1) scales
    assert result["qwk_defined_groups"] == 2
    assert result["score_normalised_mae"] == 0.5


def test_single_run_not_repeatability_and_baseline_uses_same_metrics(tmp_path):
    report = evaluate_corpus(DATASET, repeats=1, split="heldout")
    assert report["metrics"]["M12_repeatability"] is None
    assert report["pass"]["M12_repeatability"] is None
    assert report["denominators"]["repeatability_criteria"] == 0
    assert report["metrics"]["M4_B2_sufficiency_macro_f1"] == report["baseline_B2"]["sufficiency_macro_f1"]
    assert report["metrics"]["M8_B2_score_coverage"] == report["baseline_B2"]["score_coverage"]
    assert report["agent"]["sufficiency_pairs"] == report["baseline_B2"]["sufficiency_pairs"] == report["pairs"] == 19
    assert report["paired_scoring"]["pairs"] <= report["agent"]["scored_pairs"]
    assert len(report["run_outputs"]) == report["submissions"] == 4
    for case in report["run_outputs"]:
        assert len(case["agent_runs"]) == 1
        assert case["agent_runs"][0]["assessments"] and case["agent_runs"][0]["retrieved_ids"]
        assert case["baseline_B2"]
    assert (report["denominators"]["retrieval_pairs_with_relevant_units"] +
            report["denominators"]["retrieval_pairs_without_relevant_units"]) == 19
    generated = report["generated_with"]
    assert generated["evidence_kind"] == "fixture_regression"
    for kind in ("code", "prompts", "dataset"):
        assert len(generated[kind]["sha256"]) == 64 and generated[kind]["files"]
    assert "labels.json" in generated["dataset"]["files"]
    path = tmp_path / "evaluation.md"
    write_markdown_report(report, path)
    markdown = path.read_text()
    assert "not semantic hallucination" in markdown
    assert "same " in markdown and "jointly scored pairs" in markdown
    assert "conditional" in markdown and "independent labels remain pending" in markdown


def test_recall_with_no_relevant_units_is_unmeasured(monkeypatch):
    monkeypatch.setattr("rubric_agent.eval.relevant_ids", lambda units, gold: set())
    report = evaluate_corpus(DATASET, repeats=1, split="heldout", with_baseline=False)
    assert report["metrics"]["M3_recall_at_k"] is None
    assert report["pass"]["M3_recall_at_k"] is None
    assert report["denominators"]["retrieval_pairs_without_relevant_units"] == 19


def test_rejected_fixture_cannot_claim_zero_uncited_rate():
    report = evaluate_corpus(DATASET, repeats=1, split="heldout", gateway=FixtureGateway(fail_mode="invalid_json"),
                             with_baseline=False)
    assert report["agent"]["claims"] == 0
    assert report["metrics"]["M6_unsupported_rate"] is None
    assert report["pass"]["M6_unsupported_rate"] is None
    assert report["metrics"]["M8_agent_score_coverage"] == 0
    assert report["metrics"]["M8_agent_mae"] is None


@pytest.mark.parametrize("kwargs", [{"repeats": 0}, {"k": 0}, {"split": "typo"}])
def test_invalid_experiment_settings_rejected(kwargs):
    with pytest.raises(ValueError):
        evaluate_corpus(DATASET, **kwargs)


def test_duplicate_labels_and_submission_split_leakage_rejected(tmp_path):
    label = json.loads((DATASET / "labels.json").read_text())[0]
    path = tmp_path / "labels.json"
    path.write_text(json.dumps([label, label]))
    with pytest.raises(ValueError, match="Duplicate"):
        load_labels(path)
    other = {**label, "criterion_id": "C2", "split": "heldout"}
    path.write_text(json.dumps([label, other]))
    with pytest.raises(ValueError, match="leaks"):
        load_labels(path)


def test_empty_selected_split_rejected(tmp_path):
    label = json.loads((DATASET / "labels.json").read_text())[0]
    (tmp_path / "labels.json").write_text(json.dumps([label]))
    with pytest.raises(ValueError, match="No labels"):
        evaluate_corpus(tmp_path, split="heldout")


def test_cli_rejects_zero_repeats_before_gateway_setup():
    with pytest.raises(SystemExit) as error:
        main(["eval", "--repeats", "0"])
    assert error.value.code == 2
