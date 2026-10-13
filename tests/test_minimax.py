"""Provider contract tests use stub responses, never credentials or live calls."""

import json
import urllib.error
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rubric_agent.minimax import MiniMaxGateway
from rubric_agent.pipeline import run_pipeline
from rubric_agent.rubric_parser import parse_rubric

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "dataset/rubrics/engineering_report.md"
SUB = ROOT / "dataset/submissions/s1_standard.txt"


def response(text, finish="stop", **extra):
    return json.dumps({"choices": [{"finish_reason": finish, "message": {"content": text}}], **extra})


def test_minimax_contract_and_thinking_separation():
    calls = []

    def transport(url, headers, body, timeout):
        calls.append((url, headers, json.loads(body)))
        criterion = json.loads(json.loads(body)["messages"][1]["content"])["criterion"]
        return response('<think>{"provisional_score":999}</think>\n' + json.dumps({
            "criterion_id": criterion["id"], "evidence_ids": [], "sufficiency": "insufficient",
            "provisional_score": None, "score_max": criterion["max_mark"], "explanation": "Insufficient evidence.",
        }))

    gateway = MiniMaxGateway(api_key="test-secret", transport=transport)
    result = run_pipeline(RUBRIC, SUB, gateway=gateway, workers=1)
    assert all(a.draft.provisional_score is None for a in result.assessments)
    assert all("invalid_model_output" not in a.draft.flags for a in result.assessments)
    url, headers, body = calls[0]
    assert url == "https://api.minimax.io/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test-secret"
    assert body["max_completion_tokens"] == 8192
    assert body["reasoning_split"] is True and body["reasoning_effort"] == "low"
    assert "response_format" not in body and "temperature" not in body
    assert "test-secret" not in json.dumps([e.model_dump() for e in result.logs])


@pytest.mark.parametrize("reply", [response("{}", "length"), response(None), response("{}", base_resp={"status_code": 1008}), response("not JSON")])
def test_minimax_failures_never_produce_scores(reply):
    gateway = MiniMaxGateway(api_key="test", transport=lambda *args: reply)
    draft = gateway.assess(parse_rubric(RUBRIC).criteria[0], [])
    assert draft.provisional_score is None
    assert set(draft.flags) & {"provider_error", "invalid_model_output"}


def test_http_error_does_not_echo_secret():
    def transport(*args):
        raise urllib.error.HTTPError("https://api.minimax.io", 401, "test-secret", {}, None)

    draft = MiniMaxGateway(api_key="test-secret", transport=transport).assess(parse_rubric(RUBRIC).criteria[0], [])
    assert "provider_error" in draft.flags and "test-secret" not in draft.model_dump_json()
    assert "HTTP 401" in draft.explanation


def test_provider_error_message_is_not_echoed():
    gateway = MiniMaxGateway(api_key="test-secret", transport=lambda *args: response(
        "{}", base_resp={"status_code": 1008, "status_msg": "test-secret"}))
    draft = gateway.assess(parse_rubric(RUBRIC).criteria[0], [])
    assert "status 1008" in draft.explanation
    assert "test-secret" not in draft.model_dump_json()


def test_missing_key_blocks_configuration():
    with pytest.raises(ValueError, match="API key"):
        MiniMaxGateway.from_env({})


@pytest.mark.parametrize("endpoint", ["http://api.minimax.io/v1", "https://evil.test/v1", "https://api.minimax.io/v1?key=secret"])
def test_key_only_sent_to_official_https_endpoints(endpoint):
    with pytest.raises(ValueError, match="base URL"):
        MiniMaxGateway(api_key="test", endpoint=endpoint)


def test_ui_minimax_visible_and_missing_key_blocks_call(monkeypatch):
    monkeypatch.delenv("RMA_MINIMAX_API_KEY", raising=False)
    at = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=30).run()
    at.sidebar.radio[0].set_value("MiniMax API (hosted)").run()
    assert any(w.label == "MiniMax API key" for w in at.text_input)
    at.sidebar.selectbox[0].select("s1_standard (S1 baseline)")
    at.sidebar.button[0].click().run()
    assert not at.exception
    assert any("API key" in e.value for e in at.error)


def test_ui_region_switch_sets_endpoint():
    at = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=30).run()
    at.sidebar.radio[0].set_value("MiniMax API (hosted)").run()
    at.selectbox(key="minimax-region").select("China · platform.minimaxi.com").run()
    assert any("https://api.minimaxi.com/v1" in c.value for c in at.caption)
    at.selectbox(key="minimax-region").select("International · platform.minimax.io").run()
    assert any("https://api.minimax.io/v1" in c.value for c in at.caption)
    assert not at.exception


def test_ui_minimax_uses_real_adapter_contract_and_separate_log(monkeypatch, tmp_path):
    from rubric_agent.gateway import FixtureGateway
    from rubric_agent.schemas import Criterion, EvidenceUnit, ScoreDescriptor

    def transport(url, headers, body, timeout):
        payload = json.loads(json.loads(body)["messages"][1]["content"])
        c = payload["criterion"]
        criterion = Criterion(id=c["id"], name=c["name"], max_mark=c["max_mark"], granularity=c["granularity"],
                              descriptors=[ScoreDescriptor(**d) for d in c["levels"]])
        units = [EvidenceUnit(**u, paragraph=0) for u in payload["evidence"]]
        # Fixture supplies a well-formed stub response; this is not a live model test.
        return response(FixtureGateway().assess(criterion, units).model_dump_json())

    monkeypatch.setattr("rubric_agent.gateway._urllib_transport", transport)
    paths = []

    class CaptureLogger:
        def __init__(self, path):
            paths.append(path)

        def write(self, entry):
            assert "test-secret" not in entry.model_dump_json()

    monkeypatch.setattr("rubric_agent.store.RunLogger", CaptureLogger)
    at = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=30).run()
    at.sidebar.radio[0].set_value("MiniMax API (hosted)").run()
    at.text_input(key="minimax-key").set_value("test-secret")
    at.sidebar.selectbox[0].select("s1_standard (S1 baseline)")
    at.sidebar.button[0].click().run()
    assert not at.exception
    assert at.session_state["result"].model_id.startswith("MiniMax-")
    assert paths == [ROOT / "data/minimax_runs.jsonl"]
    assert at.session_state["session"].decisions
