"""Resumable, localhost-only A/B2/B3 campaign on the bundled preliminary labels.

Usage: .venv/bin/python scripts/run_campaign.py --output docs/evaluation_current
Use --fixture and a distinct output directory to verify the runner offline.
Every completed submission/repeat is checkpointed, including rejected results.
Resume never retries a completed failure or cherry-picks the best repeat.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import threading
import time
import urllib.request
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from rubric_agent import eval as evaluator
from rubric_agent.gateway import PROMPTS_DIR, FixtureGateway, OpenAICompatibleGateway, _urllib_transport
from rubric_agent.pipeline import PipelineResult, run_direct_baseline, run_pipeline
from rubric_agent.schemas import AssessmentDraft, EvidenceUnit, Rubric, RunLogEntry, ValidatedAssessment
from rubric_agent.text_parser import ParsedPage

ROOT = Path(__file__).resolve().parents[1]
SERVER = "http://127.0.0.1:11434"
MODEL = "qwen2.5:7b-instruct"


def now() -> str:
    return datetime.now(UTC).isoformat()


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".writing")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def api(path: str) -> dict:
    with urllib.request.urlopen(SERVER + path, timeout=5) as response:
        return json.load(response)


def manifest() -> dict:
    package = Path(evaluator.__file__).resolve().parent
    paths = [*package.rglob("*.py"), *PROMPTS_DIR.glob("*"), Path(__file__).resolve(), ROOT / "dataset/labels.json"]
    paths.extend(ROOT / "dataset/rubrics" / f"{label.rubric_id}.md" for label in evaluator.load_labels(ROOT / "dataset/labels.json"))
    paths.extend(ROOT / "dataset/submissions" / f"{label.submission_id}.txt" for label in evaluator.load_labels(ROOT / "dataset/labels.json"))
    files = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(set(paths)) if path.is_file()}
    return {"sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), "files": files}


def encode_result(result: PipelineResult) -> dict:
    return {
        "rubric": result.rubric.model_dump(mode="json"), "pages": [asdict(page) for page in result.pages],
        "assessments": [row.model_dump(mode="json") for row in result.assessments],
        "units": [row.model_dump(mode="json") for row in result.units],
        "retrieved": {key: [row.model_dump(mode="json") for row in rows] for key, rows in result.retrieved.items()},
        "logs": [row.model_dump(mode="json") for row in result.logs],
        "latency_ms": result.latency_ms, "model_id": result.model_id,
    }


def decode_result(value: dict) -> PipelineResult:
    return PipelineResult(
        rubric=Rubric.model_validate(value["rubric"]), pages=[ParsedPage(**page) for page in value["pages"]],
        assessments=[ValidatedAssessment.model_validate(row) for row in value["assessments"]],
        units=[EvidenceUnit.model_validate(row) for row in value["units"]],
        retrieved={key: [EvidenceUnit.model_validate(row) for row in rows] for key, rows in value["retrieved"].items()},
        logs=[RunLogEntry.model_validate(row) for row in value["logs"]],
        latency_ms=value["latency_ms"], model_id=value["model_id"],
    )


class Campaign:
    def __init__(self, output: Path, fixture: bool):
        self.output = output
        self.fixture = fixture
        self.lock = threading.Lock()
        self.condition = ""
        self.active = ""
        self.output.mkdir(parents=True, exist_ok=True)
        frozen = manifest()
        if fixture:
            model = {"name": "fixture-descriptor-v2", "digest": None}
            server = None
        else:
            installed = api("/api/tags")["models"]
            model = next((row for row in installed if row["name"] == MODEL), None)
            if not model:
                raise RuntimeError(f"Required local model {MODEL} is absent; this script never downloads models")
            server = api("/api/version")
        settings = {"model": model["name"], "model_digest": model.get("digest"), "temperature": 0,
                    "max_tokens": 700, "timeout_seconds": 180, "schema_retries_max": 1,
                    "validator_corrective_rounds_max": 1, "k": 5, "A_repeats": 3, "B3_repeats": 3,
                    "B2_repeats": 1, "split": "all", "workers": "one per criterion, pipeline default",
                    "local_server": server, "declared_server_context": 16384}
        identity = {"frozen_inputs": frozen, "settings": settings, "fixture": fixture}
        self.frozen = frozen
        self.identity_path = output / "manifest.json"
        if self.identity_path.exists():
            previous = json.loads(self.identity_path.read_text())
            if any(previous[key] != value for key, value in identity.items()):
                raise RuntimeError("Frozen code, prompts, corpus, model or settings differ; use a new output directory")
            self.identity = previous
        else:
            self.identity = {**identity, "started_at_utc": now(), "platform": platform.platform(),
                             "python": platform.python_version(), "status": "running",
                             "label_status": "preliminary first-pass synthetic labels; not independent human ground truth",
                             "execution_note": "A and B2 complete before B3; warm-up/order effects possible; same local server",
                             "raw_capture": "complete local request bodies and provider replies; no headers or credentials"}
            save(self.identity_path, self.identity)
        self.gateway = FixtureGateway() if fixture else OpenAICompatibleGateway(
            endpoint=SERVER + "/v1", model=MODEL, api_key=None, transport=self.transport)

    def assert_frozen(self):
        if manifest() != self.frozen:
            raise RuntimeError("Source/prompt/data changed during campaign; checkpoint preserved, refusing mixed-source run")

    def event(self, value: dict):
        with self.lock, (self.output / "progress.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"at_utc": now(), **value}, ensure_ascii=False) + "\n")

    def transport(self, url, headers, body, timeout):
        if url != SERVER + "/v1/chat/completions" or any(k.lower() != "content-type" for k in headers):
            raise RuntimeError("Campaign only permits unauthenticated fixed-localhost model calls")
        started = time.perf_counter()
        record = {"started_at_utc": now(), "condition": self.condition, "checkpoint": self.active,
                  "request": json.loads(body)}
        try:
            raw = _urllib_transport(url, headers, body, timeout)
            record["response"] = raw
            return raw
        except Exception as exc:
            record["error_type"] = type(exc).__name__
            raise
        finally:
            record["latency_ms"] = (time.perf_counter() - started) * 1000
            record["completed_at_utc"] = now()
            with self.lock, (self.output / "provider_responses.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def pipeline(self, rubric_path, sub_path, **kwargs):
        mode = kwargs["evidence_mode"]
        run_index = int(kwargs["test_case_id"].rsplit(":", 1)[1])
        key = f"{mode}__{rubric_path.stem}__{sub_path.stem}__r{run_index}"
        path = self.output / "checkpoints" / f"{key}.json"
        self.assert_frozen()
        if path.exists():
            return decode_result(json.loads(path.read_text())["result"])
        self.active = key
        self.event({"event": "start", "checkpoint": key})
        print(f"START {key}", flush=True)
        result = run_pipeline(rubric_path, sub_path, **kwargs)
        self.assert_frozen()
        save(path, {"completed_at_utc": now(), "result": encode_result(result)})
        self.event({"event": "complete", "checkpoint": key, "latency_ms": result.latency_ms})
        print(f"DONE {key} {result.latency_ms / 1000:.1f}s", flush=True)
        return result

    def baseline(self, rubric_path, sub_path, **kwargs):
        key = f"B2__{rubric_path.stem}__{sub_path.stem}"
        path = self.output / "checkpoints" / f"{key}.json"
        self.assert_frozen()
        if path.exists():
            data = json.loads(path.read_text())
            return Rubric.model_validate(data["rubric"]), [AssessmentDraft.model_validate(row) for row in data["drafts"]]
        self.active = key
        self.event({"event": "start", "checkpoint": key})
        print(f"START {key}", flush=True)
        started = time.perf_counter()
        rubric, drafts = run_direct_baseline(rubric_path, sub_path, **kwargs)
        latency = (time.perf_counter() - started) * 1000
        self.assert_frozen()
        save(path, {"completed_at_utc": now(), "rubric": rubric.model_dump(mode="json"),
                    "drafts": [row.model_dump(mode="json") for row in drafts], "latency_ms": latency})
        self.event({"event": "complete", "checkpoint": key, "latency_ms": latency})
        print(f"DONE {key} {latency / 1000:.1f}s", flush=True)
        return rubric, drafts

    def run(self):
        # Patching these call sites changes persistence only. All metrics are
        # recomputed by the unmodified harness across the complete corpus.
        original_pipeline, original_baseline = evaluator.run_pipeline, evaluator.run_direct_baseline
        evaluator.run_pipeline, evaluator.run_direct_baseline = self.pipeline, self.baseline
        try:
            reports = {}
            for condition, mode, baseline in (("A", "bm25", True), ("B3", "full_context", False)):
                self.condition = condition
                report = evaluator.evaluate_corpus(ROOT / "dataset", gateway=self.gateway, repeats=3, k=5,
                                                   split="all", with_baseline=baseline, evidence_mode=mode)
                report["campaign_manifest"] = "manifest.json"
                save(self.output / f"{condition}.json", report)
                evaluator.write_markdown_report(report, self.output / f"{condition}.md")
                reports[condition] = report
            save(self.output / "comparison.json", comparison(reports, self.output))
            self.identity["status"] = "complete"
            self.identity["completed_at_utc"] = now()
            save(self.identity_path, self.identity)
            self.event({"event": "campaign_complete", "pairs_per_system": reports["A"]["pairs"]})
        finally:
            evaluator.run_pipeline, evaluator.run_direct_baseline = original_pipeline, original_baseline


def comparison(reports: dict, output: Path) -> dict:
    labels = evaluator.load_labels(ROOT / "dataset/labels.json")
    golds = {(label.rubric_id, label.submission_id, label.criterion_id): label for label in labels}
    systems = {}
    predictions = {}
    for name in ("A", "B2", "B3"):
        report = reports["A" if name == "B2" else name]
        summary = report["baseline_B2" if name == "B2" else "agent"].copy()
        records = {}
        for case in report["run_outputs"]:
            drafts = case["baseline_B2"] if name == "B2" else [row["draft"] for row in case["agent_runs"][0]["assessments"]]
            for draft in drafts:
                records[(case["rubric_id"], case["submission_id"], draft["criterion_id"])] = draft
        predictions[name] = records
        summary["median_latency_ms"] = (statistics.median(json.loads(path.read_text())["latency_ms"]
                                                        for path in (output / "checkpoints").glob("B2__*.json"))
                                        if name == "B2" else report["metrics"]["M13_median_latency_ms"])
        summary["repeatability"] = None if name == "B2" else report["metrics"]["M12_repeatability"]
        summary["repeats"] = 1 if name == "B2" else 3
        summary["false_insufficient_pairs"] = sum(draft["sufficiency"] == "insufficient" and
                                                   golds[key].sufficiency != "insufficient" for key, draft in records.items())
        systems[name] = summary
    paired = {}
    for left, right in (("A", "B2"), ("A", "B3"), ("B2", "B3")):
        keys = [key for key, gold in golds.items() if gold.score is not None and
                predictions[left][key]["provisional_score"] is not None and predictions[right][key]["provisional_score"] is not None]
        paired[f"{left}_vs_{right}"] = {"jointly_scored_pairs": len(keys)}
        for name in (left, right):
            paired[f"{left}_vs_{right}"][f"{name}_normalised_mae"] = statistics.mean(
                abs(predictions[name][key]["provisional_score"] - golds[key].score) / predictions[name][key]["score_max"]
                for key in keys) if keys else None
    failures = []
    for key, gold in golds.items():
        differing = [name for name in systems if predictions[name][key]["sufficiency"] != gold.sufficiency or
                     predictions[name][key]["provisional_score"] != gold.score]
        if differing:
            failures.append({"rubric_id": key[0], "submission_id": key[1], "criterion_id": key[2],
                             "scenario": gold.scenario, "split": gold.split, "preliminary_reference": gold.model_dump(),
                             "systems_differing_from_reference": differing,
                             "outputs": {name: predictions[name][key] for name in systems}})
    per_submission = []
    for rubric_id, submission_id in sorted({key[:2] for key in golds}):
        row = {"rubric_id": rubric_id, "submission_id": submission_id, "systems": {}}
        for name in systems:
            accumulator = evaluator._Acc()
            rubric = evaluator.parse_rubric(ROOT / "dataset/rubrics" / f"{rubric_id}.md", rubric_id=rubric_id)
            criteria = {criterion.id: criterion for criterion in rubric.criteria}
            for key, gold in golds.items():
                if key[:2] != (rubric_id, submission_id):
                    continue
                draft = predictions[name][key]
                criterion = criteria[key[2]]
                accumulator.add_sufficiency(draft["sufficiency"], gold.sufficiency)
                accumulator.add_score(draft["provisional_score"], gold.score, criterion.granularity,
                                      criterion.max_mark, f"{rubric_id}/{key[2]}")
            row["systems"][name] = accumulator.summary()
        per_submission.append(row)
    return {"created_at_utc": now(), "label_status": "preliminary synthetic reference, not independent human evaluation",
            "pairs_per_system": len(golds), "systems": systems, "paired_scoring": paired,
            "per_submission": per_submission, "reference_disagreements": failures,
            "limitations": ["B2 has one run; its repeatability is not measured.",
                            "QWK/MAE are conditional on emitted scores; coverage must be reported.",
                            "QWK averages only defined within-rubric/criterion groups.",
                            "Repeated runs are not extra independent samples.",
                            "Sufficiency and scores are compared against first-pass synthetic labels.",
                            "A/B3 reuse identical original evidence IDs; B3 provides every chunk.",
                            "Order and local model warm-up can affect latency."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/evaluation_current")
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    campaign = Campaign(args.output.resolve(), args.fixture)
    try:
        campaign.run()
    except Exception as exc:
        campaign.event({"event": "campaign_interrupted", "error_type": type(exc).__name__, "message": str(exc)})
        raise
    print(f"Campaign complete: {campaign.output}", flush=True)


if __name__ == "__main__":
    main()
