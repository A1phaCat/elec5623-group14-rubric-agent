"""B3 changes context selection while preserving the assessment contract."""

from pathlib import Path

import pytest

from rubric_agent.gateway import FixtureGateway
from rubric_agent.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "dataset/rubrics/engineering_report.md"
SUBMISSION = ROOT / "dataset/submissions/s5_long.txt"


class RecordingGateway(FixtureGateway):
    def __init__(self):
        super().__init__()
        self.inputs = []

    def assess(self, criterion, evidence):
        self.inputs.append((criterion.id, [u.id for u in evidence]))
        return super().assess(criterion, evidence)


def test_full_context_has_all_units_in_document_order_and_logs_configuration():
    gateway = RecordingGateway()
    full = run_pipeline(RUBRIC, SUBMISSION, gateway=gateway, evidence_mode="full_context", workers=1)
    expected = [u.id for u in full.units]
    assert len(expected) > 1
    assert all(ids == expected for _, ids in gateway.inputs)
    assert all(log.retrieval_method == "full-context-v1" and log.retrieval_k == len(expected)
               for log in full.logs)
    assert len(full.assessments) == len(full.rubric.criteria)
    assert all(log.evidence_ids == expected for log in full.logs)
    top1 = run_pipeline(RUBRIC, SUBMISSION, k=1, workers=1)
    assert all(len(units) <= 1 for units in top1.retrieved.values())
    assert all(log.prompt_version == full.logs[0].prompt_version for log in top1.logs)
    assert all(log.retrieval_method != "full-context-v1" for log in top1.logs)


@pytest.mark.parametrize("kwargs", [{"evidence_mode": "unrecognised"}, {"k": 0}])
def test_bad_retrieval_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        run_pipeline(RUBRIC, SUBMISSION, **kwargs)
