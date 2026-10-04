"""Acceptance tests mapped to the proposal's FR/NFR IDs and scenarios S1–S7.

Everything runs offline with the fixture gateway. Live-gateway behaviour is
tested through a stub transport so no network or key is needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rubric_agent.chunker import chunk_pages
from rubric_agent.errors import ExportBlocked, RubricParseError
from rubric_agent.eval import evaluate_corpus
from rubric_agent.gateway import FixtureGateway, OpenAICompatibleGateway, build_gateway
from rubric_agent.pipeline import run_pipeline
from rubric_agent.review import EXPORT_FIELDS
from rubric_agent.rubric_parser import parse_rubric
from rubric_agent.text_parser import parse_submission

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"
ENG = DATASET / "rubrics" / "engineering_report.md"
S1 = DATASET / "submissions" / "s1_standard.txt"


def _run(sub: str = "s1_standard", rubric: Path = ENG, **kw):
    return run_pipeline(rubric, DATASET / "submissions" / f"{sub}.txt", rubric_id=rubric.stem, **kw)


# --- FR1–FR3: rubric ingest ------------------------------------------------------------


def test_fr1_fr3_block_rubric():
    rubric = parse_rubric(ENG, rubric_id="engineering_report")
    assert rubric.source_format == "block"
    assert [c.id for c in rubric.criteria] == ["C1", "C2", "C3", "C4", "C5"]
    assert [c.name for c in rubric.criteria] == [
        "Problem definition", "Methodology", "Evaluation plan", "Results and discussion", "Communication",
    ]
    assert [c.max_mark for c in rubric.criteria] == [4, 4, 4, 4, 2]
    assert all(len(c.descriptors) == 3 for c in rubric.criteria)


def test_fr2_fr3_s7_table_rubric_half_marks():
    half = parse_rubric(DATASET / "rubrics" / "half_mark.md", rubric_id="half_mark")
    assert half.source_format == "table"
    assert [c.id for c in half.criteria] == ["H1", "H2", "H3", "H4"]
    assert half.criteria[0].granularity == 0.5
    assert half.criteria[0].max_mark == 1.0
    assert [d.score for d in half.criteria[0].descriptors] == [0, 0.5, 1.0]


def test_fr1_numbered_rubric_format():
    rubric = parse_rubric(DATASET / "rubrics" / "proposal_rubric.md")
    assert rubric.source_format == "numbered"
    assert [c.id for c in rubric.criteria] == ["C1", "C2", "C3", "C4"]
    assert rubric.criteria[0].name == "Problem and motivation"
    assert rubric.criteria[0].max_mark == 5 and rubric.criteria[0].granularity == 2.5


def test_fr1_pasted_text_and_pdf_rubric():
    pasted = parse_rubric("1. Scope (2 marks)\n- 0: none\n- 2: clear\n2. Depth (3 marks)\n- 3: deep\n")
    assert [c.max_mark for c in pasted.criteria] == [2, 3]
    pdf = parse_rubric(DATASET / "rubrics" / "proposal_rubric_mini.pdf")
    assert [c.name for c in pdf.criteria] == ["Scope", "Evidence"]
    assert [c.max_mark for c in pdf.criteria] == [2, 2]


def test_fr3_rejects_descriptor_above_max_and_duplicate_ids():
    with pytest.raises(RubricParseError):
        parse_rubric("CRITERION: X\nID: C1\nMAX: 2\n0: a\n5: too high\n")
    with pytest.raises(RubricParseError):
        parse_rubric("CRITERION: X\nID: C1\nMAX: 2\n\nCRITERION: Y\nID: C1\nMAX: 2\n")


# --- FR4–FR5: submission ingest ----------------------------------------------------------


def test_fr4_fr5_txt_and_pdf_with_locators():
    pages = parse_submission(S1)
    assert pages[0].page == 1 and pages[0].section
    units = chunk_pages(pages)
    assert units and all(u.page >= 1 and u.section and u.id.startswith("E-") for u in units)
    assert "p.1" in units[0].locator

    pdf_pages = parse_submission(DATASET / "submissions" / "mini.pdf")
    assert pdf_pages[0].page == 1
    assert "Fixture adapter" in pdf_pages[0].text


# --- FR6: retrieval -----------------------------------------------------------------------


def test_fr6_topk_or_explicit_empty():
    result = _run()
    for hits in result.retrieved.values():
        assert hits == [] or all(u.id.startswith("E-") for u in hits)
    missing = _run("s3_missing_eval")
    c3 = next(a for a in missing.assessments if a.draft.criterion_id == "C3")
    assert c3.draft.sufficiency == "insufficient" and c3.draft.provisional_score is None


def test_s2_dispersed_evidence_reaches_topk():
    result = _run("s2_dispersed")
    sections = {u.section for u in result.retrieved["C2"]}
    assert len(sections) >= 2, "method evidence spread over pages should be retrieved from several sections"


# --- FR9–FR11: constrained scoring and validator (S6) ------------------------------------


def test_fr9_fr10_scores_in_range_and_cited():
    result = _run()
    for item in result.assessments:
        d = item.draft
        if d.sufficiency != "insufficient":
            assert d.provisional_score is not None and 0 <= d.provisional_score <= d.score_max
            assert d.evidence_ids and all(f"[{e}]" in d.explanation for e in d.evidence_ids[:1])
            assert item.unsupported_claims == 0


@pytest.mark.parametrize("mode,code", [
    ("unknown_id", "unknown_evidence_ids"),
    ("out_of_range", "score_out_of_range"),
    ("uncited_claim", "uncited_claim"),
    ("invalid_json", "invalid_model_output"),
])
def test_fr11_s6_validator_fails_closed(mode, code):
    broken = _run(gateway=FixtureGateway(fail_mode=mode))
    for item in broken.assessments:
        assert any(w.startswith(code) for w in item.warnings), item.warnings
        assert not item.accepted
        assert item.draft.sufficiency == "insufficient"
        assert item.draft.provisional_score is None
        assert "validation_failed" in item.draft.flags


def test_s4_decoy_never_positive():
    result = _run("s4_decoy_eval")
    c3 = next(a for a in result.assessments if a.draft.criterion_id == "C3")
    assert c3.draft.sufficiency in {"insufficient", "partial"}
    assert c3.draft.sufficiency != "sufficient"


# --- Live gateway contract (no network) -----------------------------------------------------


def _stub(reply: str):
    calls = []

    def transport(url, headers, body, timeout):
        calls.append((url, headers, body))
        return '{"choices":[{"message":{"content":' + __import__("json").dumps(reply) + '}}]}'

    return transport, calls


def test_live_gateway_valid_json_passes_through():
    rubric = parse_rubric(ENG)
    crit = rubric.criteria[0]
    units = chunk_pages(parse_submission(S1))
    reply = ('{"criterion_id":"C1","evidence_ids":["E-001"],"sufficiency":"partial","provisional_score":2,'
             '"score_max":4,"explanation":"Scoped problem stated [E-001].","draft_feedback":null,"flags":[]}')
    transport, calls = _stub(reply)
    gw = OpenAICompatibleGateway(endpoint="https://example.test/v1", model="m", api_key="secret", transport=transport)
    draft = gw.assess(crit, units[:3])
    assert draft.provisional_score == 2 and draft.evidence_ids == ["E-001"]
    url, headers, body = calls[0]
    assert url.endswith("/chat/completions")
    assert headers["Authorization"] == "Bearer secret"
    assert b'"response_format"' in body and b"E-001" in body
    assert "secret" not in gw.name


@pytest.mark.parametrize("reply", ["not json at all", '{"criterion_id":"C1","sufficiency":"great"}', "[]", '```json\n{"bad":1}\n```'])
def test_live_gateway_malformed_output_is_rejected(reply):
    rubric = parse_rubric(ENG)
    transport, _ = _stub(reply)
    gw = OpenAICompatibleGateway(endpoint="https://example.test/v1", model="m", api_key=None, transport=transport)
    draft = gw.assess(rubric.criteria[0], [])
    assert draft.sufficiency == "insufficient" and draft.provisional_score is None
    assert "invalid_model_output" in draft.flags


def test_fr1_s7_banded_table_rubric_without_max_column():
    text = (
        "# Banded rubric\n\n"
        "| Criterion | Excellent (8-10) | Good (5–7) | Limited (1-4) | Not shown (0) |\n"
        "|---|---|---|---|---|\n"
        "| Analysis | Rigorous, quantified analysis | Mostly sound analysis | Superficial | Absent |\n"
        "| Report quality | Clear and concise | Readable | Hard to follow | Absent |\n"
    )
    r = parse_rubric(text, rubric_id="banded")
    assert r.source_format == "table" and [c.max_mark for c in r.criteria] == [10.0, 10.0]
    assert [d.score for d in r.criteria[0].descriptors] == [0.0, 4.0, 7.0, 10.0]
    assert r.criteria[0].granularity == 1.0 and r.criteria[1].name == "Report quality"

    from rubric_agent.rubric_parser import level_from_header
    assert level_from_header("HD 4") == 4.0 and level_from_header("Weight") is None and level_from_header("1.5") == 1.5


def test_real_canvas_rubric_and_real_pdf_parse():
    """The official ELEC5623 proposal rubric and our own proposal PDF (a 16-page real document, cover removed)."""
    r = parse_rubric(ROOT / "dataset/real/elec5623_business_proposal_rubric.md")
    assert [c.max_mark for c in r.criteria] == [1.5, 1.5, 2, 2, 1.5, 1.5] and all(c.granularity == 0.5 for c in r.criteria)
    pages = parse_submission(ROOT / "dataset/real/group14_proposal_v2.pdf")
    units = chunk_pages(pages)
    assert len(pages) >= 15 and len(units) >= 40
    sections = {u.section for u in units}
    assert {"Executive Summary", "Functional Requirements", "Evaluation Plan"} <= sections, sections
    words = [len(u.text.split()) for u in units]
    assert max(words) <= 260 and sorted(words)[len(words) // 2] >= 40  # PDF paragraphs were split, not one unit per page


def test_live_gateway_corrective_round_after_validator_rejection():
    """First answer has an uncited claim → validator rejects → one revision → accepted."""
    import json as _json

    bad = _json.dumps({"criterion_id": "C1", "evidence_ids": ["E-001"], "sufficiency": "partial", "provisional_score": 2,
                       "score_max": 4, "explanation": "The problem is scoped. It names users [E-001].", "draft_feedback": None, "flags": []})
    good = _json.dumps({"criterion_id": "C1", "evidence_ids": ["E-001"], "sufficiency": "partial", "provisional_score": 2,
                        "score_max": 4, "explanation": "The problem is scoped [E-001]. It names users [E-001].", "draft_feedback": None, "flags": []})
    calls = []

    def transport(url, headers, body, timeout):
        calls.append(_json.loads(body))
        reply = good if len(calls) % 2 == 0 else bad  # first answer bad, corrected answer good
        return '{"choices":[{"message":{"content":' + _json.dumps(reply) + '}}]}'

    gw = OpenAICompatibleGateway(endpoint="https://example.test/v1", model="m", api_key=None, transport=transport)
    result = run_pipeline(ENG, S1, gateway=gw, rubric_id="engineering_report", workers=1)
    c1 = result.assessments[0]
    assert c1.accepted and "revised_once" in c1.draft.flags
    log = result.logs[0]
    assert log.attempts == 2 and any(w.startswith("uncited_claim") for w in log.first_attempt_warnings)
    # The revision request carried the validator's finding back to the model.
    assert any("uncited_claim" in m["content"] for m in calls[1]["messages"] if m["role"] == "user")

    # With revise disabled the rejection stands.
    calls.clear()
    result2 = run_pipeline(ENG, S1, gateway=gw, rubric_id="engineering_report", revise=False, workers=1)
    assert not result2.assessments[0].accepted and result2.logs[0].attempts == 1


def test_citation_variants_are_recognised_but_still_checked():
    from rubric_agent.textutil import citation_ids, unsupported_claims

    assert citation_ids("Scoped problem [E-001]. Users named [E-002, E-003]. Quote [E-004: 'x y'].") == ["E-001", "E-002", "E-003", "E-004"]
    assert unsupported_claims("Scoped problem [E-001: 'gap']. Users are named.") == ["Users are named."]
    rubric = parse_rubric(ENG)
    units = chunk_pages(parse_submission(S1))
    from rubric_agent.schemas import AssessmentDraft
    from rubric_agent.validator import validate_assessment

    draft = AssessmentDraft(criterion_id="C1", evidence_ids=["E-001"], sufficiency="partial", provisional_score=2, score_max=4,
                            explanation="Scoped [E-001]. Users named [E-999: 'tutors'].")
    v = validate_assessment(draft, rubric.criteria[0], units[:2])
    assert any(w.startswith("unknown_citation_ids") for w in v.warnings) and v.draft.provisional_score is None


def test_positive_claim_detection_rules():
    """M6 counts sentences that assert content is present; absences and rubric judgements are not claims."""
    from rubric_agent.textutil import positive_claims, unsupported_claims

    text = ("The report scopes the problem for tutors [E-001]. "
            "However, it does not explicitly state who is affected. "
            "This aligns with the descriptor for 2.0. "
            "No baseline is given. "
            "The method section lists three metrics.")
    assert unsupported_claims(text) == ["The method section lists three metrics."]
    assert len(positive_claims(text)) == 2
    # A cited sentence is always a claim even if it contains a negation.
    assert positive_claims("The plan does not name a baseline but lists two metrics [E-004].") == [
        "The plan does not name a baseline but lists two metrics [E-004]."]


def test_direct_baseline_accepts_common_output_shapes():
    from rubric_agent.gateway import _direct_items

    item = {"criterion_id": "C1", "sufficiency": "partial", "provisional_score": 2, "score_max": 4, "explanation": "x"}
    assert _direct_items({"criteria": [item]}) == [item]
    assert _direct_items([item]) == [item]
    assert _direct_items(item) == [item]
    assert _direct_items({"C1": {"sufficiency": "partial"}})[0]["criterion_id"] == "C1"
    assert _direct_items("nonsense") == []


def test_live_gateway_transport_error_is_fail_closed():
    def boom(url, headers, body, timeout):
        raise OSError("connection refused")

    gw = OpenAICompatibleGateway(endpoint="http://localhost:1/v1", model="m", api_key=None, transport=boom)
    result = run_pipeline(ENG, S1, gateway=gw, rubric_id="engineering_report")
    assert all(a.draft.sufficiency == "insufficient" and "provider_error" in a.warnings for a in result.assessments)


def test_build_gateway_from_env_and_azure_header():
    env = {"RMA_MODEL_ENDPOINT": "https://x.openai.azure.com/openai/deployments/d", "RMA_MODEL": "gpt",
           "RMA_MODEL_API_KEY": "k", "RMA_API_KEY_HEADER": "api-key", "RMA_API_VERSION": "2024-10-21"}
    gw = build_gateway("live", env=env)
    assert isinstance(gw, OpenAICompatibleGateway) and gw.key_header == "api-key" and gw.api_version == "2024-10-21"
    assert isinstance(build_gateway(None, env={}), FixtureGateway)
    with pytest.raises(RuntimeError):
        build_gateway("live", env={})


# --- FR12, FR13, FR15, NFR5: review and export --------------------------------------------


def test_fr12_fr13_fr15_nfr5_export_block_and_override():
    result = _run()
    session = result.review_session()
    with pytest.raises(ExportBlocked):
        session.export_record()
    first = result.assessments[0].draft.criterion_id
    session.decide(first, "accepted")
    with pytest.raises(ExportBlocked):
        session.export_record()
    for item in result.assessments[1:]:
        session.decide(item.draft.criterion_id, "edited", score=1, comment="override")
    record = session.export_record()
    assert {row["criterion_id"] for row in record} == {a.draft.criterion_id for a in result.assessments}
    for row in record:
        assert set(EXPORT_FIELDS) <= set(row)
        assert row["decided_at"] and row["marker_state"] in {"accepted", "edited"}
    edited = next(row for row in record if row["marker_state"] == "edited")
    assert edited["marker_final_score"] == 1
    assert "ai_suggested_score" in edited  # original suggestion retained (FR13)
    assert record[0]["model_id"] and record[0]["prompt_version"] == "assessment_v2"
    csv_text = session.export_csv()
    assert csv_text.splitlines()[0].startswith("criterion_id,criterion_name")
    assert len(csv_text.splitlines()) == len(record) + 1


def test_fr13_edited_score_must_be_in_range():
    result = _run()
    session = result.review_session()
    cid = result.assessments[0].draft.criterion_id
    with pytest.raises(ValueError):
        session.decide(cid, "edited", score=99)
    with pytest.raises(ValueError):
        session.decide(cid, "edited")


# --- FR16, NFR7, NFR2: logging and replay -----------------------------------------------------


def test_fr16_nfr7_run_log_and_replay(tmp_path):
    from rubric_agent.store import RunLogger, replay_entry

    logger = RunLogger(tmp_path / "runs.jsonl")
    result = run_pipeline(ENG, S1, test_case_id="s1_standard", logger=logger, rubric_id="engineering_report")
    entries = logger.read()
    assert len(entries) == len(result.assessments)
    for e in entries:
        assert e.model_id and e.prompt_version == "assessment_v2" and e.test_case_id == "s1_standard"
        assert e.retrieval_method == "bm25" and e.retrieval_k == 5 and e.rubric_ref and e.submission_ref
    outcomes = [replay_entry(e) for e in entries]
    assert all(o.same_top1 and o.same_cited and o.within_tolerance for o in outcomes)


# --- Corpus-level harness (M-metrics that do not need a real model) ---------------------------


def test_corpus_harness_targets():
    report = evaluate_corpus(DATASET, repeats=3)
    m = report["metrics"]
    assert report["pairs"] == 62
    assert m["M1_rubric_criteria"] == 1.0
    assert m["M2_locator_complete"] == 1.0
    assert m["M3_recall_at_k"] >= 0.85
    assert m["M5_citation_exists"] >= 0.95
    assert m["M6_unsupported_rate"] <= 0.05
    assert m["M6_unsupported_rate_B2"] > m["M6_unsupported_rate"]
    assert m["M7_score_range_validity"] == 1.0
    assert m["M12_repeatability"] >= 0.90
    assert m["M13_median_latency_ms"] <= 120_000
    assert m["M16_export_completeness"] == 1.0
    assert m["M17_feedback_grounding"] == 1.0
    # M4/M8 are reported honestly; the fixture is not expected to pass them.
    assert 0.0 <= m["M4_sufficiency_macro_f1"] <= 1.0
    assert report["pass"]["M4_sufficiency_macro_f1"] in {True, False}
    assert set(report["per_scenario"]) >= {"S1", "S2", "S3", "S4", "S5"}


def test_corpus_split_filter():
    dev = evaluate_corpus(DATASET, repeats=1, split="dev", with_baseline=False)
    held = evaluate_corpus(DATASET, repeats=1, split="heldout", with_baseline=False)
    assert dev["pairs"] + held["pairs"] == 62 and held["pairs"] == 19
