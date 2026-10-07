"""Derive token and call usage from already-captured provider responses.

Addendum A.5 of docs/EVALUATION_PROTOCOL.md. Pure post-processing: no model is
called and nothing is re-run. `scripts/run_campaign.py` and
`scripts/run_robustness.py` both write every local request and reply to
`provider_responses.jsonl`, and Ollama's OpenAI-compatible endpoint returns a
`usage` object, so the figures were already on disk.

    .venv/bin/python scripts/extract_usage.py

Counts include JSON re-asks and validator corrective rounds, because the Week 9
lab asks for retries to be included: a criterion is allowed up to three HTTP
calls, so calls-per-criterion is part of the cost picture.

Tokens are **not** a monetary cost. These runs were local; cost would depend on
a model and a service that were not used. If a response carries no `usage`
object its tokens are reported as unmeasured rather than estimated.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def show(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


DEFAULT_SOURCES = [
    ROOT / "docs/evaluation_dev_frozen/provider_responses.jsonl",
    ROOT / "docs/robustness/provider_responses.jsonl",
]


def criterion_of(request: dict) -> str | None:
    """Recover which rubric criterion a captured request was about.

    The prompt embeds the criterion as `"id": "C3"` in its JSON block, which is
    the only place the captured body identifies it.
    """
    for message in request.get("messages", []):
        content = message.get("content") or ""
        marker = '"id":'
        if marker in content:
            fragment = content.split(marker, 1)[1].lstrip()
            if fragment.startswith('"'):
                return fragment[1:].split('"', 1)[0]
    return None


def load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        response = record.get("response")
        usage = None
        if response:
            try:
                usage = json.loads(response).get("usage")
            except (json.JSONDecodeError, AttributeError):
                usage = None
        records.append({
            "source": show(path),
            # run_campaign records condition/checkpoint; run_robustness records context.
            "group": record.get("checkpoint") or record.get("context") or "unknown",
            "condition": record.get("condition"),
            "criterion_id": criterion_of(record.get("request") or {}),
            "latency_ms": record.get("latency_ms"),
            "error_type": record.get("error_type"),
            "usage": usage,
        })
    return records


def summarise(records: list[dict]) -> dict:
    if not records:
        return {"status": "no captured responses found", "calls": 0}

    with_usage = [r for r in records if r["usage"]]
    prompt = [r["usage"]["prompt_tokens"] for r in with_usage if "prompt_tokens" in r["usage"]]
    completion = [r["usage"]["completion_tokens"] for r in with_usage if "completion_tokens" in r["usage"]]
    cached = [r["usage"].get("prompt_tokens_details", {}).get("cached_tokens", 0) for r in with_usage]

    # Calls per (group, criterion): the retry budget is per criterion call.
    per_unit: dict[tuple[str, str | None], int] = defaultdict(int)
    for record in records:
        per_unit[(record["group"], record["criterion_id"])] += 1
    calls = list(per_unit.values())

    # Per-submission totals. A campaign checkpoint looks like
    # "bm25__engineering_report__s1_standard__r0"; take the submission segment.
    def submission_of(group: str) -> str:
        parts = group.split("__")
        if len(parts) >= 3:
            return parts[2]
        return group.split(":", 2)[1] if ":" in group else group

    per_submission: dict[str, dict] = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0,
                                                           "completion_tokens": 0, "criteria": set()})
    for record in records:
        row = per_submission[submission_of(record["group"])]
        row["calls"] += 1
        if record["criterion_id"]:
            row["criteria"].add(record["criterion_id"])
        if record["usage"]:
            row["prompt_tokens"] += record["usage"].get("prompt_tokens", 0)
            row["completion_tokens"] += record["usage"].get("completion_tokens", 0)

    submissions = {
        name: {**{k: v for k, v in row.items() if k != "criteria"},
               "criteria": len(row["criteria"]),
               "total_tokens": row["prompt_tokens"] + row["completion_tokens"]}
        for name, row in sorted(per_submission.items())
    }

    by_condition: dict[str, dict] = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0,
                                                         "completion_tokens": 0})
    for record in records:
        key = record["condition"] or record["source"].rsplit("/", 2)[-2]
        by_condition[key]["calls"] += 1
        if record["usage"]:
            by_condition[key]["prompt_tokens"] += record["usage"].get("prompt_tokens", 0)
            by_condition[key]["completion_tokens"] += record["usage"].get("completion_tokens", 0)

    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "protocol": "docs/EVALUATION_PROTOCOL.md Addendum A.5",
        "derivation": "post-processing of captured provider_responses.jsonl; no model was called",
        "sources": sorted({r["source"] for r in records}),
        "calls": len(records),
        "failed_calls": sum(1 for r in records if r["error_type"]),
        "usage_capture_rate": len(with_usage) / len(records),
        "calls_without_usage": len(records) - len(with_usage),
        "tokens": {
            "prompt_total": sum(prompt) or None,
            "completion_total": sum(completion) or None,
            "total": (sum(prompt) + sum(completion)) if prompt or completion else None,
            "prompt_median_per_call": statistics.median(prompt) if prompt else None,
            "completion_median_per_call": statistics.median(completion) if completion else None,
            "prompt_max_per_call": max(prompt) if prompt else None,
            "completion_max_per_call": max(completion) if completion else None,
            "cached_prompt_tokens_total": sum(cached) or None,
            "cached_note": (
                "cached_tokens is the local server's prompt-cache hit count. It reduces local "
                "compute, not the prompt the model was given."),
        },
        "calls_per_criterion": {
            "mean": statistics.mean(calls) if calls else None,
            "median": statistics.median(calls) if calls else None,
            "max": max(calls) if calls else None,
            "distribution": {str(n): calls.count(n) for n in sorted(set(calls))},
            "units_counted": len(calls),
            "budget": "1 assessment call + up to 1 JSON re-ask + up to 1 validator corrective round = 3",
        },
        "per_condition": dict(by_condition),
        "per_submission": submissions,
        "limits": [
            "Token counts are not monetary cost. These runs were local; no provider was billed.",
            "Counts include JSON re-asks and validator corrective rounds, so they exceed one call per criterion.",
            "A prompt-cache hit lowers local compute only; it does not change what the model was shown.",
            "Derived from captured responses; a response without a usage object is reported as unmeasured.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, nargs="*", default=DEFAULT_SOURCES)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/robustness/usage.json")
    args = parser.parse_args()

    records: list[dict] = []
    for source in args.sources:
        found = load(source.resolve())
        print(f"{show(source.resolve())}: {len(found)} captured calls")
        records.extend(found)

    report = summarise(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not records:
        print("No captured responses; token usage is unmeasured.")
        return
    tokens = report["tokens"]
    print(f"\ncalls {report['calls']}  usage captured {report['usage_capture_rate']:.3f}")
    print(f"prompt tokens {tokens['prompt_total']:,} (median {tokens['prompt_median_per_call']}/call, "
          f"max {tokens['prompt_max_per_call']})")
    print(f"completion tokens {tokens['completion_total']:,} (median "
          f"{tokens['completion_median_per_call']}/call, max {tokens['completion_max_per_call']})")
    cpc = report["calls_per_criterion"]
    print(f"calls per criterion: median {cpc['median']}, max {cpc['max']}, "
          f"distribution {cpc['distribution']} over {cpc['units_counted']} units")
    print(f"wrote {show(args.output.resolve())}")


if __name__ == "__main__":
    main()
