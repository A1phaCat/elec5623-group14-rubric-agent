"""Small current-source local-model check; not a labelled evaluation campaign.

Run from the source checkout with the local Ollama server already running:
    python scripts/validate_local_model.py --output docs/validation/local_smoke.json
No credentials, hosted endpoints, new models or human decisions are involved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from rubric_agent.gateway import OpenAICompatibleGateway
from rubric_agent.pipeline import run_direct_baseline, run_pipeline

ROOT = Path(__file__).resolve().parents[1]
OLLAMA = "http://127.0.0.1:11434"
MODEL = "qwen2.5:7b-instruct"


def metadata(path: str):
    with urllib.request.urlopen(f"{OLLAMA}{path}", timeout=5) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; choose a new path to preserve the previous run")
    models = metadata("/api/tags")["models"]
    model = next((row for row in models if row["name"] == MODEL), None)
    if model is None:
        parser.error(f"{MODEL} is not installed locally")
    gateway = OpenAICompatibleGateway(endpoint=f"{OLLAMA}/v1", model=MODEL, api_key=None)
    cases = [
        ("synthetic_decoy", "dataset/rubrics/engineering_report.md", "dataset/submissions/s4_decoy_eval.txt", "bm25"),
        ("synthetic_decoy_B3", "dataset/rubrics/engineering_report.md", "dataset/submissions/s4_decoy_eval.txt", "full_context"),
        ("own_proposal", "dataset/real/elec5623_business_proposal_rubric.md", "dataset/real/group14_proposal_v2.pdf", "bm25"),
    ]
    paths = [*ROOT.glob("src/rubric_agent/*.py"), *ROOT.glob("prompts/*.md"), Path(__file__).resolve()]
    paths.extend(ROOT / source for _, rubric, submission, _ in cases for source in (rubric, submission))
    report = {
        "kind": "local_model_smoke_not_quality_benchmark",
        "started_at_utc": datetime.now(UTC).isoformat(),
        "model": MODEL, "model_digest": model["digest"], "ollama": metadata("/api/version"),
        "python": platform.python_version(), "temperature": gateway.temperature,
        "max_tokens": gateway.max_tokens, "context_length_server": 16384,
        "context_length_note": "Server configured by operator with OLLAMA_CONTEXT_LENGTH=16384; verify for reruns.",
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))},
        "limitations": ["One run per condition; no repeatability or population-quality claim.",
                        "No independently labelled score or semantic support on the real PDF.",
                        "Validator and review code differ from the historical 13 September run.",
                        "Local server queueing and warm-up affect wall-clock latency."],
        "runs": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for name, rubric, submission, mode in cases:
        print(f"Running {name}: {mode}", flush=True)
        result = run_pipeline(ROOT / rubric, ROOT / submission, gateway=gateway,
                              evidence_mode=mode, rubric_id=Path(rubric).stem, test_case_id=name)
        report["runs"].append({
            "case": name, "evidence_mode": mode, "pages": len(result.pages), "units": len(result.units),
            "latency_ms": result.latency_ms,
            "criteria": [a.model_dump() for a in result.assessments],
            "logs": [entry.model_dump() for entry in result.logs],
        })
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved {name}: {result.latency_ms / 1000:.1f}s; "
              f"{sum(a.accepted for a in result.assessments)}/{len(result.assessments)} valid records", flush=True)
    _, baseline = run_direct_baseline(ROOT / cases[0][1], ROOT / cases[0][2], gateway=gateway)
    report["B2_decoy"] = [draft.model_dump() for draft in baseline]
    report["completed_at_utc"] = datetime.now(UTC).isoformat()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Completed; saved {args.output}", flush=True)


if __name__ == "__main__":
    main()
