"""The campaign runner must describe and guard the corpus it actually ran on.

A report that cannot name its corpus, label file and prompt is not reproducible
evidence, and a runner that silently continues an output directory belonging to
different inputs would mix sources. Both are asserted here. Model calls are out
of scope: these run on the offline fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.run_campaign import Campaign, manifest

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"


def _run(output: Path, **kwargs):
    defaults = {"corpus": DATASET, "labels": "labels.json", "split": "dev"}
    campaign = Campaign(output, True, **{**defaults, **kwargs})
    campaign.run()
    return campaign


def test_campaign_records_corpus_labels_and_prompt(tmp_path):
    _run(tmp_path / "run")
    identity = json.loads((tmp_path / "run" / "manifest.json").read_text())
    settings = identity["settings"]
    assert settings["corpus"] == "dataset" and settings["labels_file"] == "labels.json"
    assert settings["split"] == "dev" and settings["prompt_version"]
    assert identity["status"] == "complete"

    comparison = json.loads((tmp_path / "run" / "comparison.json").read_text())
    assert comparison["corpus"] == "dataset" and comparison["labels_file"] == "labels.json"
    assert comparison["split"] == "dev"
    assert set(comparison["systems"]) == {"A", "B2", "B3"}
    # dev holds 43 labelled pairs; the heldout split must not leak in.
    assert comparison["pairs_per_system"] == 43


def test_a_different_label_file_is_a_different_campaign(tmp_path):
    output = tmp_path / "run"
    _run(output, labels="labels.json")
    with pytest.raises(RuntimeError, match="use a new output directory"):
        Campaign(output, True, corpus=DATASET, labels="labels_v2.json", split="dev")


def test_a_different_split_is_a_different_campaign(tmp_path):
    output = tmp_path / "run"
    _run(output, split="dev")
    with pytest.raises(RuntimeError, match="use a new output directory"):
        Campaign(output, True, corpus=DATASET, labels="labels.json", split="heldout")


def test_missing_labels_name_the_annotation_procedure(tmp_path):
    with pytest.raises(SystemExit, match="EVALUATION_PROTOCOL"):
        Campaign(tmp_path / "run", True, corpus=DATASET / "final_test", labels="labels.json", split="all")


def test_manifest_covers_the_label_file_and_the_documents_it_names():
    files = manifest(DATASET, DATASET / "labels_v2.json")["files"]
    assert "dataset/labels_v2.json" in files
    assert "dataset/rubrics/engineering_report.md" in files
    assert "dataset/submissions/s1_standard.txt" in files
    assert any(name.startswith("prompts/") for name in files)
    # A corpus swap must change the digest, otherwise assert_frozen is useless.
    assert manifest(DATASET, DATASET / "labels.json")["sha256"] != manifest(DATASET, DATASET / "labels_v2.json")["sha256"]


def test_resume_reuses_checkpoints_instead_of_recalling_the_model(tmp_path):
    output = tmp_path / "run"
    _run(output)
    checkpoints = sorted(path.name for path in (output / "checkpoints").glob("*.json"))
    stamps = {path: path.stat().st_mtime_ns for path in (output / "checkpoints").glob("*.json")}
    _run(output)
    assert sorted(path.name for path in (output / "checkpoints").glob("*.json")) == checkpoints
    assert all(path.stat().st_mtime_ns == stamp for path, stamp in stamps.items())
