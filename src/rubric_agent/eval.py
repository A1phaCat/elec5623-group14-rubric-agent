"""Evaluation harness for proposal §8 (metrics M1–M8, M12, M13, M16, M17).

Design rules:
* The gateway under test never sees gold labels.
* Baseline B2 (direct whole-document grading) runs through the same gateway
  class so agent vs B2 differences come from the *workflow*, not the model.
* Human-in-the-loop metrics (M9–M11, M14, M15-audit) cannot be computed here;
  the report lists them as "requires marker session".
"""

from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from . import PROMPT_VERSION
from .gateway import PROMPTS_DIR, FixtureGateway, ModelGateway
from .pipeline import run_direct_baseline, run_pipeline
from .review import EXPORT_FIELDS
from .rubric_parser import parse_rubric
from .schemas import EvidenceUnit, GoldLabel
from .store import RunLogger
from .textutil import citation_ids, positive_claims, unsupported_claims

TARGETS = {
    "M1_rubric_criteria": 0.95, "M2_locator_complete": 1.0, "M3_recall_at_k": 0.85,
    "M4_sufficiency_macro_f1": 0.75, "M5_citation_exists": 0.95, "M6_unsupported_rate": 0.05,
    "M6_relative_reduction_vs_B2": 0.30, "M7_score_range_validity": 1.0,
    "M12_repeatability": 0.90, "M13_median_latency_ms": 120_000, "M13_s5_latency_ms": 120_000,
    "M16_export_completeness": 1.0, "M17_feedback_grounding": 1.0,
}
HIGHER_IS_BETTER = {k: k not in {"M6_unsupported_rate", "M13_median_latency_ms", "M13_s5_latency_ms"} for k in TARGETS}


def load_labels(path: Path) -> list[GoldLabel]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    labels = [GoldLabel.model_validate(item) for item in raw]
    seen = set()
    submission_splits: dict[str, str] = {}
    for label in labels:
        key = (label.rubric_id, label.submission_id, label.criterion_id)
        if key in seen:
            raise ValueError(f"Duplicate gold label: {key}")
        seen.add(key)
        previous = submission_splits.setdefault(label.submission_id, label.split)
        if previous != label.split:
            raise ValueError(f"Submission leaks across dev/heldout: {label.submission_id}")
    return labels


def _ratio(numerator: float, denominator: int) -> float | None:
    """An empty denominator is unmeasured, never a successful zero-error result."""
    return numerator / denominator if denominator else None


def _manifest(root: Path, paths: list[Path]) -> dict:
    files = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(set(paths))}
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {"sha256": digest, "files": files}


def _provenance(dataset_dir: Path, labels: list[GoldLabel], gateway: ModelGateway) -> dict:
    package = Path(__file__).resolve().parent
    root = package.parents[1]
    data_files = [dataset_dir / "labels.json"]
    for lab in labels:
        data_files.extend([dataset_dir / "rubrics" / f"{lab.rubric_id}.md",
                           dataset_dir / "submissions" / f"{lab.submission_id}.txt"])
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True,
                                    text=True, check=True).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    # Explicit allow-list: never serialize the gateway object, headers, endpoint or environment.
    model_config = {key: getattr(gateway, key) for key in ("model", "temperature", "max_tokens", "timeout", "max_retries")
                    if hasattr(gateway, key)}
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "evidence_kind": "fixture_regression" if isinstance(gateway, FixtureGateway) else "model_gateway_run",
        "gateway_class": type(gateway).__name__, "model_config": model_config,
        "git_commit": commit, "git_dirty": dirty,
        "code": _manifest(root, list(package.rglob("*.py"))),
        "prompts": _manifest(PROMPTS_DIR, [p for p in PROMPTS_DIR.iterdir() if p.is_file()]),
        "dataset": _manifest(dataset_dir, data_files),
        "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                    "pydantic": version("pydantic"), "pypdf": version("pypdf")},
        "label_validation": "Independent annotation is not verified by this harness; see EVALUATION_PROTOCOL.md.",
        "latency_scope": "first agent run per rubric/submission; wall-clock including parsing, retrieval, calls and validation",
        "workers": "pipeline default (one worker per criterion)", "corrective_rounds_max": 1,
    }


def relevant_ids(units: list[EvidenceUnit], gold: GoldLabel) -> set[str]:
    hits = set()
    for unit in units:
        text = unit.text.lower()
        if any(phrase.lower() in text for phrase in gold.must_contain):
            hits.add(unit.id)
    return hits


def _level(score: float, granularity: float) -> int:
    return int(round(score / granularity))


def quadratic_weighted_kappa(pred: list[int], gold: list[int], n_levels: int) -> float | None:
    if len(pred) != len(gold):
        raise ValueError("QWK requires paired predictions and labels")
    if not pred or n_levels < 2:
        return None
    n = n_levels
    obs = [[0] * n for _ in range(n)]
    for p, g in zip(pred, gold):
        if not 0 <= p < n or not 0 <= g < n:
            return None
        obs[p][g] += 1
    total = len(pred)
    row = [sum(r) for r in obs]
    col = [sum(obs[i][j] for i in range(n)) for j in range(n)]
    num = den = 0.0
    for i in range(n):
        for j in range(n):
            w = ((i - j) ** 2) / ((n - 1) ** 2)
            num += w * obs[i][j]
            den += w * row[i] * col[j] / total
    if den == 0:
        return None  # Constant labels and predictions give no chance-agreement denominator.
    return 1.0 - num / den


@dataclass
class _Acc:
    """Running counters for one system (agent or B2)."""

    suff_tp: dict = field(default_factory=lambda: defaultdict(int))
    suff_fp: dict = field(default_factory=lambda: defaultdict(int))
    suff_fn: dict = field(default_factory=lambda: defaultdict(int))
    suff_correct: int = 0
    suff_total: int = 0
    claims: int = 0
    unsupported: int = 0
    abs_err: list[float] = field(default_factory=list)
    normalised_abs_err: list[float] = field(default_factory=list)
    score_groups: dict = field(default_factory=lambda: defaultdict(list))
    scored_pairs: int = 0
    gold_scored: int = 0

    def add_sufficiency(self, pred: str, gold: str) -> None:
        self.suff_total += 1
        if pred == gold:
            self.suff_tp[pred] += 1
            self.suff_correct += 1
        else:
            self.suff_fp[pred] += 1
            self.suff_fn[gold] += 1

    def add_claims(self, explanation: str, sufficiency: str) -> None:
        if sufficiency == "insufficient":
            return
        self.claims += len(positive_claims(explanation))
        self.unsupported += len(unsupported_claims(explanation))

    def add_score(self, pred: float | None, gold: float | None, granularity: float, max_mark: float,
                  group: str = "default") -> None:
        if gold is None:
            return
        self.gold_scored += 1
        if pred is None:
            return
        self.scored_pairs += 1
        self.abs_err.append(abs(pred - gold))
        self.normalised_abs_err.append(abs(pred - gold) / max_mark)
        self.score_groups[(group, granularity, max_mark)].append((_level(pred, granularity), _level(gold, granularity)))

    def macro_f1(self) -> float | None:
        if not self.suff_total:
            return None
        f1s = []
        for lab in ("sufficient", "partial", "insufficient"):
            prec = self.suff_tp[lab] / max(self.suff_tp[lab] + self.suff_fp[lab], 1)
            rec = self.suff_tp[lab] / max(self.suff_tp[lab] + self.suff_fn[lab], 1)
            f1s.append(0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec))
        return sum(f1s) / len(f1s)

    def summary(self) -> dict:
        kappas = []
        for (_, step, maximum), pairs in self.score_groups.items():
            qwk = quadratic_weighted_kappa([p for p, _ in pairs], [g for _, g in pairs], _level(maximum, step) + 1)
            if qwk is not None:
                kappas.append((qwk, len(pairs)))
        return {
            "sufficiency_accuracy": _ratio(self.suff_correct, self.suff_total),
            "sufficiency_macro_f1": self.macro_f1(),
            "sufficiency_pairs": self.suff_total,
            "claims": self.claims,
            "unsupported_claims": self.unsupported,
            "unsupported_rate": _ratio(self.unsupported, self.claims),
            "score_qwk": _ratio(sum(q * n for q, n in kappas), sum(n for _, n in kappas)),
            "qwk_defined_groups": len(kappas),
            "qwk_scored_pairs": sum(n for _, n in kappas),
            "score_mae": statistics.mean(self.abs_err) if self.abs_err else None,
            "score_normalised_mae": statistics.mean(self.normalised_abs_err) if self.normalised_abs_err else None,
            "score_coverage": _ratio(self.scored_pairs, self.gold_scored),
            "scored_pairs": self.scored_pairs, "gold_scored_pairs": self.gold_scored,
            "abstained_on_gold_scored": self.gold_scored - self.scored_pairs,
        }


def evaluate_corpus(
    dataset_dir: Path,
    *,
    gateway: ModelGateway | None = None,
    k: int = 5,
    repeats: int = 3,
    split: str = "all",
    log_path: Path | None = None,
    with_baseline: bool = True,
    evidence_mode: str = "bm25",
) -> dict:
    if repeats < 1 or k < 1:
        raise ValueError("repeats and k must both be positive integers")
    if split not in {"all", "dev", "heldout"}:
        raise ValueError("split must be all, dev or heldout")
    if evidence_mode not in {"bm25", "full_context"}:
        raise ValueError("evidence_mode must be bm25 or full_context")
    gateway = gateway or FixtureGateway()
    labels = [lab for lab in load_labels(dataset_dir / "labels.json") if split == "all" or lab.split == split]
    if not labels:
        raise ValueError(f"No labels in selected split: {split}")
    by_pair: dict[tuple[str, str], list[GoldLabel]] = defaultdict(list)
    for label in labels:
        by_pair[(label.rubric_id, label.submission_id)].append(label)

    logger = RunLogger(log_path) if log_path else None
    agent, base = _Acc(), _Acc()
    per_scenario: dict[str, _Acc] = defaultdict(_Acc)
    rubric_hits = rubric_total = 0
    locator_ok = locator_total = 0
    recall_sum = precision_sum = 0.0
    retrieval_n = retrieval_empty_gold = 0
    cite_exists_ok = cite_support_ok = cite_total = 0
    range_ok = range_total = 0
    export_ok = export_total = 0
    feedback_ok = feedback_total = 0
    warnings_seen: dict[str, int] = defaultdict(int)
    first_attempt_warnings: dict[str, int] = defaultdict(int)
    revised = calls = 0
    latencies: list[float] = []
    s5_latencies: list[float] = []
    repeat_ok = repeat_total = 0
    agent_scores: dict[tuple[str, str, str], tuple[float, float, float]] = {}
    baseline_scores: dict[tuple[str, str, str], tuple[float, float, float]] = {}
    run_outputs: list[dict] = []
    provenance = _provenance(dataset_dir, labels, gateway)

    for (rubric_id, submission_id), golds in sorted(by_pair.items()):
        rubric_path = dataset_dir / "rubrics" / f"{rubric_id}.md"
        sub_path = dataset_dir / "submissions" / f"{submission_id}.txt"
        parsed = parse_rubric(rubric_path, rubric_id=rubric_id)
        crit_by_id = {c.id: c for c in parsed.criteria}
        gold_ids = {g.criterion_id for g in golds}
        rubric_total += len(gold_ids)
        rubric_hits += len(crit_by_id.keys() & gold_ids)
        gold_map = {g.criterion_id: g for g in golds}
        if not gold_ids <= crit_by_id.keys():
            raise ValueError(f"Unknown labelled criteria for {rubric_id}: {sorted(gold_ids - crit_by_id.keys())}")
        for gold in golds:
            crit = crit_by_id[gold.criterion_id]
            if gold.score is not None and (not 0 <= gold.score <= crit.max_mark or
                    abs(round(gold.score / crit.granularity) * crit.granularity - gold.score) > 1e-6):
                raise ValueError(f"Gold score outside rubric range/grid: {rubric_id}/{submission_id}/{crit.id}")

        runs = []
        for run_i in range(repeats):
            runs.append(run_pipeline(
                rubric_path, sub_path, gateway=gateway, k=k,
                test_case_id=f"{submission_id}:{run_i}",
                logger=logger if run_i == 0 else None, rubric_id=rubric_id,
                evidence_mode=evidence_mode,
            ))
        result = runs[0]
        case_output = {
            "rubric_id": rubric_id, "submission_id": submission_id,
            "agent_runs": [
                {"run_index": index, "latency_ms": run.latency_ms,
                 "retrieved_ids": {cid: [unit.id for unit in units] for cid, units in run.retrieved.items()},
                 "assessments": [item.model_dump(mode="json") for item in run.assessments]}
                for index, run in enumerate(runs)
            ],
            "baseline_B2": None,
        }
        run_outputs.append(case_output)
        latencies.append(result.latency_ms)
        if any(g.scenario == "S5" for g in golds):
            s5_latencies.append(result.latency_ms)
        locator_total += len(result.units)
        locator_ok += sum(1 for u in result.units if u.page >= 1 and u.section)
        for entry in result.logs:
            calls += 1
            revised += int(entry.attempts > 1)
            for w in entry.first_attempt_warnings:
                first_attempt_warnings[w.split(":", 1)[0]] += 1

        for validated in result.assessments:
            draft = validated.draft
            crit = crit_by_id[draft.criterion_id]
            gold = gold_map.get(draft.criterion_id)
            retrieved = result.retrieved.get(draft.criterion_id, [])
            allowed = {u.id for u in retrieved}
            for w in validated.warnings:
                warnings_seen[w.split(":", 1)[0]] += 1

            # M7
            range_total += 1
            if draft.sufficiency == "insufficient":
                range_ok += int(draft.provisional_score is None)
            elif draft.provisional_score is not None:
                step = crit.granularity
                range_ok += int(0 <= draft.provisional_score <= crit.max_mark
                                and abs(round(draft.provisional_score / step) * step - draft.provisional_score) < 1e-6)
            # M17
            if draft.draft_feedback:
                feedback_total += 1
                feedback_ok += int(set(citation_ids(draft.draft_feedback)) <= allowed)
            # M6 (agent)
            agent.add_claims(draft.explanation, draft.sufficiency)

            if gold is None:
                continue
            # M3
            rel = relevant_ids(result.units, gold)
            top = [u.id for u in retrieved]
            if rel:
                retrieval_n += 1
                recall_sum += len(set(top) & rel) / len(rel)
                precision_sum += (len(set(top) & rel) / len(top)) if top else 0.0
            else:
                retrieval_empty_gold += 1
            # M5
            for eid in draft.evidence_ids:
                cite_total += 1
                cite_exists_ok += int(eid in allowed)
                cite_support_ok += int(eid in allowed and eid in rel)
            # M4, M8
            agent.add_sufficiency(draft.sufficiency, gold.sufficiency)
            group = f"{rubric_id}/{crit.id}"
            agent.add_score(draft.provisional_score, gold.score, crit.granularity, crit.max_mark, group)
            if draft.provisional_score is not None and gold.score is not None:
                agent_scores[(rubric_id, submission_id, crit.id)] = (draft.provisional_score, gold.score, crit.max_mark)
            sc = per_scenario[gold.scenario]
            sc.add_sufficiency(draft.sufficiency, gold.sufficiency)
            sc.add_claims(draft.explanation, draft.sufficiency)
            sc.add_score(draft.provisional_score, gold.score, crit.granularity, crit.max_mark, group)

        # M12 across repeats
        for c in parsed.criteria:
            repeat_total += 1
            top1 = {(r.retrieved.get(c.id) or [None])[0].id if r.retrieved.get(c.id) else "NONE" for r in runs}
            scores = [next(a.draft.provisional_score for a in r.assessments if a.draft.criterion_id == c.id) for r in runs]
            present = [s for s in scores if s is not None]
            drift_ok = (len(present) in (0, len(scores))) and (not present or (max(present) - min(present)) <= 0.10 * c.max_mark)
            repeat_ok += int(len(top1) == 1 and drift_ok)

        # M16: auto-confirm and export
        session = result.review_session()
        for a in result.assessments:
            can_accept = a.accepted and a.draft.provisional_score is not None and a.draft.sufficiency != "insufficient"
            session.decide(a.draft.criterion_id, "accepted" if can_accept else "rejected")
        for row in session.export_record():
            export_total += 1
            export_ok += int(all(f in row for f in EXPORT_FIELDS) and row["decided_at"] and row["marker_state"] != "pending")

        # Baseline B2
        if with_baseline:
            _, drafts = run_direct_baseline(rubric_path, sub_path, gateway=gateway, rubric_id=rubric_id)
            case_output["baseline_B2"] = [draft.model_dump(mode="json") for draft in drafts]
            for d in drafts:
                gold = gold_map.get(d.criterion_id)
                crit = crit_by_id[d.criterion_id]
                base.add_claims(d.explanation, d.sufficiency)
                if gold is not None:
                    base.add_sufficiency(d.sufficiency, gold.sufficiency)
                    base.add_score(d.provisional_score, gold.score, crit.granularity, crit.max_mark, f"{rubric_id}/{crit.id}")
                    if d.provisional_score is not None and gold.score is not None:
                        baseline_scores[(rubric_id, submission_id, crit.id)] = (d.provisional_score, gold.score, crit.max_mark)

    agent_s, base_s = agent.summary(), base.summary()
    m6_agent = agent_s["unsupported_rate"]
    m6_base = base_s["unsupported_rate"]
    reduction = (m6_base - m6_agent) / m6_base if with_baseline and m6_base and m6_agent is not None else None
    common = agent_scores.keys() & baseline_scores.keys()
    paired_scores = {
        "pairs": len(common),
        "agent_conditional_normalised_mae": statistics.mean(abs(agent_scores[key][0] - agent_scores[key][1]) / agent_scores[key][2]
                                                            for key in common) if common else None,
        "B2_conditional_normalised_mae": statistics.mean(abs(baseline_scores[key][0] - baseline_scores[key][1]) / baseline_scores[key][2]
                                                         for key in common) if common else None,
    } if with_baseline else None
    metrics = {
        "M1_rubric_criteria": rubric_hits / max(rubric_total, 1),
        "M2_locator_complete": _ratio(locator_ok, locator_total),
        "M3_recall_at_k": _ratio(recall_sum, retrieval_n),
        "M3_precision_at_k": _ratio(precision_sum, retrieval_n),
        "M4_sufficiency_macro_f1": agent_s["sufficiency_macro_f1"],
        "M4_sufficiency_accuracy": agent_s["sufficiency_accuracy"],
        "M4_B2_sufficiency_macro_f1": base_s["sufficiency_macro_f1"] if with_baseline else None,
        "M4_B2_sufficiency_accuracy": base_s["sufficiency_accuracy"] if with_baseline else None,
        "M5_citation_exists": _ratio(cite_exists_ok, cite_total),
        "M5_citation_supports_proxy": _ratio(cite_support_ok, cite_total),
        "M6_unsupported_rate": m6_agent,
        "M6_unsupported_rate_B2": m6_base if with_baseline else None,
        "M6_relative_reduction_vs_B2": reduction,
        "M7_score_range_validity": range_ok / max(range_total, 1),
        "M8_agent_qwk": agent_s["score_qwk"],
        "M8_agent_mae": agent_s["score_mae"],
        "M8_agent_normalised_mae": agent_s["score_normalised_mae"],
        "M8_agent_score_coverage": agent_s["score_coverage"],
        "M8_B2_qwk": base_s["score_qwk"] if with_baseline else None,
        "M8_B2_mae": base_s["score_mae"] if with_baseline else None,
        "M8_B2_normalised_mae": base_s["score_normalised_mae"] if with_baseline else None,
        "M8_B2_score_coverage": base_s["score_coverage"] if with_baseline else None,
        "M12_repeatability": _ratio(repeat_ok, repeat_total) if repeats >= 2 else None,
        "M13_median_latency_ms": statistics.median(latencies) if latencies else None,
        "M13_s5_latency_ms": statistics.median(s5_latencies) if s5_latencies else None,
        "M16_export_completeness": _ratio(export_ok, export_total),
        "M17_feedback_grounding": _ratio(feedback_ok, feedback_total),
    }
    passes = {}
    for key, target in TARGETS.items():
        val = metrics.get(key)
        if val is None:
            passes[key] = None
        else:
            passes[key] = val >= target if HIGHER_IS_BETTER[key] else val <= target
    return {
        "schema_version": 2,
        "generated_with": {"gateway": gateway.name, "prompt_version": PROMPT_VERSION, "k": k, "repeats": repeats,
                           "split": split, "evidence_mode": evidence_mode, **provenance},
        "pairs": len(labels),
        "submissions": len(by_pair),
        "rubrics": len({r for r, _ in by_pair}),
        "metrics": metrics,
        "targets": TARGETS,
        "pass": passes,
        "agent": agent_s,
        "paired_scoring": paired_scores,
        "run_outputs": run_outputs,
        "denominators": {
            "labelled_pairs": len(labels), "gold_numeric_scores": agent.gold_scored,
            "agent_scored_pairs": agent.scored_pairs, "B2_scored_pairs": base.scored_pairs if with_baseline else None,
            "retrieval_pairs_with_relevant_units": retrieval_n, "retrieval_pairs_without_relevant_units": retrieval_empty_gold,
            "evidence_units": locator_total, "citations": cite_total,
            "agent_positive_claims": agent.claims, "B2_positive_claims": base.claims if with_baseline else None,
            "range_checked_outputs": range_total, "repeatability_criteria": repeat_total if repeats >= 2 else 0,
            "latency_submissions": len(latencies), "s5_latency_submissions": len(s5_latencies),
            "export_rows": export_total, "feedback_outputs": feedback_total,
        },
        "metric_notes": {
            "M3": "Macro average over pairs with at least one phrase-matched relevant unit; empty gold sets excluded and counted.",
            "M6": "Legacy unsupported keys count uncited positive sentences only, not semantic hallucinations. B2 is not asked for evidence IDs.",
            "M8": "MAE/QWK are conditional on emitted scores with numeric gold. QWK is pair-weighted across defined rubric/criterion groups; no mixed-scale pooling.",
            "M12": "Requires at least two runs; one run is unmeasured. Stable abstention counts as repeatability, not quality.",
            "M17": "Checks only that feedback citation IDs are allowed; does not establish semantic grounding.",
        },
        "per_scenario": {
            s: {"pairs": acc.suff_total, **acc.summary()}
            for s, acc in sorted(per_scenario.items())
        },
        "validator_warnings": dict(sorted(warnings_seen.items())),
        "first_attempt_warnings": dict(sorted(first_attempt_warnings.items())),
        "revision_rate": revised / max(calls, 1),
        "baseline_B2": base_s if with_baseline else None,
        "requires_marker_session": ["M9", "M10", "M11", "M14", "M15 (data audit)", "M5 human support judgement"],
    }


def write_markdown_report(report: dict, path: Path) -> None:
    g = report["generated_with"]
    m = report["metrics"]
    p = report["pass"]
    lines = [
        "# Evaluation report",
        "",
        f"Generated by `rma eval`. Gateway **{g['gateway']}**, prompt `{g['prompt_version']}`, "
        f"evidence mode={g.get('evidence_mode', 'bm25')}, k={g['k']}, repeats={g['repeats']}, split={g['split']}.",
        "",
        f"Corpus: {report['rubrics']} rubrics, {report['submissions']} rubric–submission combinations, "
        f"{report['pairs']} labelled criterion–submission pairs. The bundled corpus is synthetic; independent labels remain pending.",
        "",
    ]
    if g.get("evidence_kind") == "fixture_regression" or g["gateway"].startswith("fixture"):
        lines += [
            "> **Read this first.** The fixture is a deterministic descriptor-matching heuristic, not a language model. "
            "These numbers prove the harness, validator and metric code run end-to-end; they say nothing about how a real model would score. "
            "Re-run with `RMA_GATEWAY=live` once model access is approved.",
            "",
        ]
    lines += [
        "> **Metric limits.** M6 measures uncited positive sentences, not semantic hallucination. B2 does not receive a citation "
        "requirement, so its M6 rate does not demonstrate worse factual accuracy. M8 MAE and QWK exclude abstentions and must "
        "be read with score coverage. QWK uses separate rubric/criterion scales; values are not comparable with older pooled QWK reports. "
        "M5/M17 citation checks are structural proxies. A single run cannot measure repeatability. See [protocol](EVALUATION_PROTOCOL.md).",
        "",
    ]
    lines += ["| Metric | Value | Target | Pass |", "|---|---|---|---|"]
    for key, val in m.items():
        target = report["targets"].get(key)
        status = p.get(key)
        mark = "—" if status is None else ("✅" if status else "❌")
        label = key.replace("unsupported_rate", "uncited_positive_claim_rate")
        if key.startswith("M8_") and "coverage" not in key:
            label += " (conditional)"
        lines.append(f"| {label} | {_fmt(val)} | {_fmt(target) if target is not None else '—'} | {mark} |")
    if report.get("agent"):
        a = report["agent"]
        lines += ["", f"Agent scored **{a['scored_pairs']}/{a['gold_scored_pairs']}** numeric-gold pairs; "
                  f"abstained on **{a['abstained_on_gold_scored']}**. Conditional normalised MAE: {_fmt(a['score_normalised_mae'])}."]
    lines += ["", "## Per scenario", "", "| Scenario | Pairs | Sufficiency acc. | Uncited positive claim rate | Conditional MAE | Score coverage |",
              "|---|---|---|---|---|---|"]
    for s, row in report["per_scenario"].items():
        lines.append(f"| {s} | {row['pairs']} | {_fmt(row['sufficiency_accuracy'])} | {_fmt(row['unsupported_rate'])} "
                     f"| {_fmt(row['score_mae'])} | {_fmt(row.get('score_coverage'))} |")
    if report.get("baseline_B2"):
        b = report["baseline_B2"]
        lines += ["", "## Baseline B2 (direct whole-document grading, same gateway)", "",
                  f"Sufficiency macro-F1 {_fmt(b['sufficiency_macro_f1'])}, accuracy {_fmt(b['sufficiency_accuracy'])}, "
                  f"uncited positive claim rate {_fmt(b['unsupported_rate'])} ({b['unsupported_claims']}/{b['claims']} claims), "
                  f"conditional QWK {_fmt(b['score_qwk'])}, conditional MAE {_fmt(b['score_mae'])}, "
                  f"score coverage {_fmt(b['score_coverage'])} ({b.get('scored_pairs', 'n/a')}/{b.get('gold_scored_pairs', 'n/a')})."]
    if report.get("paired_scoring"):
        paired = report["paired_scoring"]
        lines += ["", f"On the **same {paired['pairs']} jointly scored pairs**, conditional normalised MAE is "
                  f"agent {_fmt(paired['agent_conditional_normalised_mae'])}, B2 {_fmt(paired['B2_conditional_normalised_mae'])}. "
                  "This subset comparison does not measure accuracy on abstained cases."]
    lines += ["", "## Validator", "",
              "Final records with warnings: " + (", ".join(f"`{k}` ×{v}" for k, v in report["validator_warnings"].items()) or "none") + ".",
              "",
              f"Corrective round used on {report['revision_rate']:.1%} of calls. First-attempt rejections: "
              + (", ".join(f"`{k}` ×{v}" for k, v in report["first_attempt_warnings"].items()) or "none") + "."]
    lines += ["", "## Not measurable offline", "", "Requires a marker session (proposal S8): " + ", ".join(report["requires_marker_session"]) + ".", ""]
    if report.get("denominators"):
        lines += ["## Sample counts", "", "| Denominator | Count |", "|---|---|"]
        lines.extend(f"| {key} | {_fmt(value)} |" for key, value in report["denominators"].items())
        lines += ["", "## Reproducibility", "", f"Generated (UTC): `{g['created_at_utc']}`. "
                  f"Git commit: `{g['git_commit']}`; working tree modified: `{g['git_dirty']}`.",
                  "Full per-file SHA-256 manifests and model/runtime configuration are in the companion JSON.", ""]
        lines.extend(f"- {kind} SHA-256: `{g[kind]['sha256']}`" for kind in ("code", "prompts", "dataset"))
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.3f}" if abs(v) < 1000 else f"{v:,.0f}"
    return str(v)
