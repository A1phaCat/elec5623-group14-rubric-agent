"""Guards on the reviewed dev-split label correction and the labels_path plumbing.

The correction is only defensible if it stayed inside its declared scope, so the
scope is asserted here rather than described in prose alone. See
`dataset/LABELS_V2_CHANGES.md`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.build_labels_v2 import CORRECTIONS, RETAINED, build

from rubric_agent.eval import evaluate_corpus, load_labels
from rubric_agent.gateway import FixtureGateway

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"
V1 = DATASET / "labels.json"
V2 = DATASET / "labels_v2.json"


def _key(row: dict) -> tuple[str, str, str]:
    return row["rubric_id"], row["submission_id"], row["criterion_id"]


def test_correction_touches_only_dev_sufficiency():
    before = {_key(r): r for r in json.loads(V1.read_text(encoding="utf-8"))}
    after = {_key(r): r for r in json.loads(V2.read_text(encoding="utf-8"))}
    assert before.keys() == after.keys()

    for key, old in before.items():
        new = after[key]
        # Scores drive M8 and must_contain drives M3; neither may move.
        assert new["score"] == old["score"], key
        assert new["must_contain"] == old["must_contain"], key
        assert new["split"] == old["split"] and new["scenario"] == old["scenario"], key
        if new["sufficiency"] != old["sufficiency"]:
            assert old["split"] == "dev", f"{key} changed outside the dev split"
            assert key in CORRECTIONS, f"{key} changed without a declared reason"


def test_heldout_split_is_byte_identical():
    before = [r for r in json.loads(V1.read_text(encoding="utf-8")) if r["split"] == "heldout"]
    after = [r for r in json.loads(V2.read_text(encoding="utf-8")) if r["split"] == "heldout"]
    assert before == after and len(after) == 19


def test_every_declared_correction_is_applied_and_retained_pairs_are_not():
    after = {_key(r): r for r in json.loads(V2.read_text(encoding="utf-8"))}
    for key, (source, target, reason) in CORRECTIONS.items():
        assert after[key]["sufficiency"] == target, key
        assert source != target and reason.strip()
    for key in RETAINED:
        before = {_key(r): r for r in json.loads(V1.read_text(encoding="utf-8"))}
        assert after[key]["sufficiency"] == before[key]["sufficiency"], key


def test_build_is_idempotent_and_never_writes_the_original(tmp_path):
    original = V1.read_bytes()
    out = tmp_path / "labels_v2.json"
    build(V1, out)
    assert V1.read_bytes() == original
    assert json.loads(out.read_text(encoding="utf-8")) == json.loads(V2.read_text(encoding="utf-8"))


def test_build_refuses_a_source_that_no_longer_matches(tmp_path):
    rows = json.loads(V1.read_text(encoding="utf-8"))
    for row in rows:
        if _key(row) in CORRECTIONS:
            row["sufficiency"] = "insufficient"  # not the declared source value
            break
    tampered = tmp_path / "labels.json"
    tampered.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(SystemExit, match="declared source"):
        build(tampered, tmp_path / "out.json")


def test_both_label_files_load_and_keep_submissions_inside_one_split():
    for path in (V1, V2):
        labels = load_labels(path)
        assert len(labels) == 62


def test_evaluate_corpus_honours_labels_path_and_reports_per_class():
    report = evaluate_corpus(DATASET, gateway=FixtureGateway(), repeats=1, split="dev", labels_path=V2)
    assert report["generated_with"]["labels_file"] == "labels_v2.json"

    per_class = report["agent"]["sufficiency_per_class"]
    assert set(per_class) == {"sufficient", "partial", "insufficient"}
    assert sum(row["gold_support"] for row in per_class.values()) == report["pairs"]
    # The correction leaves a single partial gold in dev; macro-F1 therefore
    # rests one third on one pair, which the report must make visible.
    assert per_class["partial"]["gold_support"] == 1
    assert sum(report["agent"]["sufficiency_confusion"].values()) == report["pairs"]


def test_labels_path_must_live_inside_the_corpus_directory(tmp_path):
    outside = tmp_path / "labels.json"
    outside.write_text(V2.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="inside dataset_dir"):
        evaluate_corpus(DATASET, gateway=FixtureGateway(), repeats=1, labels_path=outside)
