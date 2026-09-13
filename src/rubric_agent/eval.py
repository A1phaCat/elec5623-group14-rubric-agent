"""Evaluation harness for proposal §8 (metrics M1–M8, M12, M13, M16, M17).

Design rules:
* The gateway under test never sees gold labels.
* Baseline B2 (direct whole-document grading) runs through the same gateway
  class so agent vs B2 differences come from the *workflow*, not the model.
* Human-in-the-loop metrics (M9–M11, M14, M15-audit) cannot be computed here;
  the report lists them as "requires marker session".
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from . import PROMPT_VERSION
from .gateway import FixtureGateway, ModelGateway
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
    return [GoldLabel.model_validate(item) for item in raw]


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
    if not pred or n_levels < 2:
        return None
    n = n_levels
    obs = [[0] * n for _ in range(n)]
    for p, g in zip(pred, gold):
        obs[min(p, n - 1)][min(g, n - 1)] += 1
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
        return 1.0 if num == 0 else 0.0
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
    pred_levels: list[int] = field(default_factory=list)
    gold_levels: list[int] = field(default_factory=list)
    abs_err: list[float] = field(default_factory=list)
    max_levels: int = 2
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

    def add_score(self, pred: float | None, gold: float | None, granularity: float, max_mark: float) -> None:
        if gold is None:
            return
        self.gold_scored += 1
        if pred is None:
            return
        self.scored_pairs += 1
        self.pred_levels.append(_level(pred, granularity))
        self.gold_levels.append(_level(gold, granularity))
        self.max_levels = max(self.max_levels, _level(max_mark, granularity) + 1)
        self.abs_err.append(abs(pred - gold))

    def macro_f1(self) -> float:
        f1s = []
        for lab in ("sufficient", "partial", "insufficient"):
            prec = self.suff_tp[lab] / max(self.suff_tp[lab] + self.suff_fp[lab], 1)
            rec = self.suff_tp[lab] / max(self.suff_tp[lab] + self.suff_fn[lab], 1)
            f1s.append(0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec))
        return sum(f1s) / len(f1s)

    def summary(self) -> dict:
        return {
            "sufficiency_accuracy": self.suff_correct / max(self.suff_total, 1),
            "sufficiency_macro_f1": self.macro_f1(),
            "claims": self.claims,
            "unsupported_claims": self.unsupported,
            "unsupported_rate": self.unsupported / max(self.claims, 1),
            "score_qwk": quadratic_weighted_kappa(self.pred_levels, self.gold_levels, self.max_levels),
            "score_mae": statistics.mean(self.abs_err) if self.abs_err else None,
            "score_coverage": self.scored_pairs / max(self.gold_scored, 1),
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
) -> dict:
    gateway = gateway or FixtureGateway()
    labels = [l for l in load_labels(dataset_dir / "labels.json") if split == "all" or l.split == split]
    by_pair: dict[tuple[str, str], list[GoldLabel]] = defaultdict(list)
    for label in labels:
        by_pair[(label.rubric_id, label.submission_id)].append(label)

    logger = RunLogger(log_path) if log_path else None
    agent, base = _Acc(), _Acc()
    per_scenario: dict[str, _Acc] = defaultdict(_Acc)
    rubric_hits = rubric_total = 0
    locator_ok = locator_total = 0
    recall_sum = precision_sum = 0.0
    retrieval_n = 0
    cite_exists_ok = cite_support_ok = cite_total = 0
    range_ok = range_total = 0
    export_ok = export_total = 0
    feedback_ok = feedback_total = 0
    warnings_seen: dict[str, int] = defaultdict(int)
    latencies: list[float] = []
    s5_latencies: list[float] = []
    repeat_ok = repeat_total = 0

    for (rubric_id, submission_id), golds in sorted(by_pair.items()):
        rubric_path = dataset_dir / "rubrics" / f"{rubric_id}.md"
        sub_path = dataset_dir / "submissions" / f"{submission_id}.txt"
        parsed = parse_rubric(rubric_path, rubric_id=rubric_id)
        crit_by_id = {c.id: c for c in parsed.criteria}
        gold_ids = {g.criterion_id for g in golds}
        rubric_total += len(gold_ids)
        rubric_hits += len(crit_by_id.keys() & gold_ids)
        gold_map = {g.criterion_id: g for g in golds}

        runs = []
        for run_i in range(repeats):
            runs.append(run_pipeline(
                rubric_path, sub_path, gateway=gateway, k=k,
                test_case_id=f"{submission_id}:{run_i}",
                logger=logger if run_i == 0 else None, rubric_id=rubric_id,
            ))
        result = runs[0]
        latencies.append(result.latency_ms)
        if any(g.scenario == "S5" for g in golds):
            s5_latencies.append(result.latency_ms)
        locator_total += len(result.units)
        locator_ok += sum(1 for u in result.units if u.page >= 1 and u.section)

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
            retrieval_n += 1
            if rel:
                recall_sum += len(set(top) & rel) / len(rel)
                precision_sum += (len(set(top) & rel) / len(top)) if top else 0.0
            else:
                recall_sum += 1.0
                precision_sum += 1.0 if not top else 0.0
            # M5
            for eid in draft.evidence_ids:
                cite_total += 1
                cite_exists_ok += int(eid in allowed)
                cite_support_ok += int(eid in allowed and eid in rel)
            # M4, M8
            agent.add_sufficiency(draft.sufficiency, gold.sufficiency)
            agent.add_score(draft.provisional_score, gold.score, crit.granularity, crit.max_mark)
            sc = per_scenario[gold.scenario]
            sc.add_sufficiency(draft.sufficiency, gold.sufficiency)
            sc.add_claims(draft.explanation, draft.sufficiency)
            sc.add_score(draft.provisional_score, gold.score, crit.granularity, crit.max_mark)

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
            session.decide(a.draft.criterion_id, "accepted" if a.draft.provisional_score is not None else "rejected")
        for row in session.export_record():
            export_total += 1
            export_ok += int(all(f in row for f in EXPORT_FIELDS) and row["decided_at"] and row["marker_state"] != "pending")

        # Baseline B2
        if with_baseline:
            _, drafts = run_direct_baseline(rubric_path, sub_path, gateway=gateway, rubric_id=rubric_id)
            for d in drafts:
                gold = gold_map.get(d.criterion_id)
                crit = crit_by_id[d.criterion_id]
                base.add_claims(d.explanation, d.sufficiency)
                if gold is not None:
                    base.add_sufficiency(d.sufficiency, gold.sufficiency)
                    base.add_score(d.provisional_score, gold.score, crit.granularity, crit.max_mark)

    agent_s, base_s = agent.summary(), base.summary()
    m6_agent = agent_s["unsupported_rate"]
    m6_base = base_s["unsupported_rate"]
    reduction = (m6_base - m6_agent) / m6_base if with_baseline and m6_base > 0 else None
    metrics = {
        "M1_rubric_criteria": rubric_hits / max(rubric_total, 1),
        "M2_locator_complete": locator_ok / max(locator_total, 1),
        "M3_recall_at_k": recall_sum / max(retrieval_n, 1),
        "M3_precision_at_k": precision_sum / max(retrieval_n, 1),
        "M4_sufficiency_macro_f1": agent_s["sufficiency_macro_f1"],
        "M4_sufficiency_accuracy": agent_s["sufficiency_accuracy"],
        "M5_citation_exists": cite_exists_ok / max(cite_total, 1),
        "M5_citation_supports_proxy": cite_support_ok / max(cite_total, 1),
        "M6_unsupported_rate": m6_agent,
        "M6_unsupported_rate_B2": m6_base if with_baseline else None,
        "M6_relative_reduction_vs_B2": reduction,
        "M7_score_range_validity": range_ok / max(range_total, 1),
        "M8_agent_qwk": agent_s["score_qwk"],
        "M8_agent_mae": agent_s["score_mae"],
        "M8_agent_score_coverage": agent_s["score_coverage"],
        "M8_B2_qwk": base_s["score_qwk"] if with_baseline else None,
        "M8_B2_mae": base_s["score_mae"] if with_baseline else None,
        "M12_repeatability": repeat_ok / max(repeat_total, 1),
        "M13_median_latency_ms": statistics.median(latencies) if latencies else 0.0,
        "M13_s5_latency_ms": statistics.median(s5_latencies) if s5_latencies else None,
        "M16_export_completeness": export_ok / max(export_total, 1),
        "M17_feedback_grounding": feedback_ok / max(feedback_total, 1) if feedback_total else None,
    }
    passes = {}
    for key, target in TARGETS.items():
        val = metrics.get(key)
        if val is None:
            passes[key] = None
        else:
            passes[key] = val >= target if HIGHER_IS_BETTER[key] else val <= target
    return {
        "generated_with": {"gateway": gateway.name, "prompt_version": PROMPT_VERSION, "k": k, "repeats": repeats, "split": split},
        "pairs": len(labels),
        "submissions": len(by_pair),
        "rubrics": len({r for r, _ in by_pair}),
        "metrics": metrics,
        "targets": TARGETS,
        "pass": passes,
        "per_scenario": {
            s: {"pairs": acc.suff_total, **{k2: v for k2, v in acc.summary().items() if k2 in {"sufficiency_accuracy", "unsupported_rate", "score_mae"}}}
            for s, acc in sorted(per_scenario.items())
        },
        "validator_warnings": dict(sorted(warnings_seen.items())),
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
        f"Generated by `rma eval`. Gateway **{g['gateway']}**, prompt `{g['prompt_version']}`, k={g['k']}, repeats={g['repeats']}, split={g['split']}.",
        "",
        f"Corpus: {report['rubrics']} rubrics, {report['submissions']} submissions, {report['pairs']} labelled criterion–submission pairs (synthetic, no student data).",
        "",
    ]
    if g["gateway"].startswith("fixture"):
        lines += [
            "> **Read this first.** The fixture is a deterministic descriptor-matching heuristic, not a language model. "
            "These numbers prove the harness, validator and metric code run end-to-end; they say nothing about how a real model would score. "
            "Re-run with `RMA_GATEWAY=live` once model access is approved.",
            "",
        ]
    lines += ["| Metric | Value | Target | Pass |", "|---|---|---|---|"]
    for key, val in m.items():
        target = report["targets"].get(key)
        status = p.get(key)
        mark = "—" if status is None else ("✅" if status else "❌")
        lines.append(f"| {key} | {_fmt(val)} | {_fmt(target) if target is not None else '—'} | {mark} |")
    lines += ["", "## Per scenario", "", "| Scenario | Pairs | Sufficiency acc. | Unsupported rate | Score MAE |", "|---|---|---|---|---|"]
    for s, row in report["per_scenario"].items():
        lines.append(f"| {s} | {row['pairs']} | {_fmt(row['sufficiency_accuracy'])} | {_fmt(row['unsupported_rate'])} | {_fmt(row['score_mae'])} |")
    if report.get("baseline_B2"):
        b = report["baseline_B2"]
        lines += ["", "## Baseline B2 (direct whole-document grading, same gateway)", "",
                  f"Sufficiency accuracy {_fmt(b['sufficiency_accuracy'])}, unsupported-claim rate {_fmt(b['unsupported_rate'])} "
                  f"({b['unsupported_claims']}/{b['claims']} claims), QWK {_fmt(b['score_qwk'])}, MAE {_fmt(b['score_mae'])}."]
    lines += ["", "## Validator warnings raised", ""]
    lines += [f"- `{k}`: {v}" for k, v in report["validator_warnings"].items()] or ["- none"]
    lines += ["", "## Not measurable offline", "", "Requires a marker session (proposal S8): " + ", ".join(report["requires_marker_session"]) + ".", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.3f}" if abs(v) < 1000 else f"{v:,.0f}"
    return str(v)
