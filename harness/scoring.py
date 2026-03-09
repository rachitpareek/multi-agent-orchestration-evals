"""
Scoring engines for all six MAO-Bench metric dimensions.

Each scorer takes a list of TaskRun objects and produces a normalized
score in [0, 1] for its dimension, plus the raw metric values.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Sequence

from harness.models import TaskRun


@dataclass
class DimensionScore:
    """Normalized score for one metric dimension."""

    dimension: str
    score: float  # [0, 1]
    raw_metrics: dict[str, float] = field(default_factory=dict)
    task_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class MAOScore:
    """Full composite MAO-Bench score for a benchmark run."""

    robustness: DimensionScore
    persistence: DimensionScore
    token_efficiency: DimensionScore
    speed: DimensionScore
    topology: DimensionScore
    quality: DimensionScore

    @property
    def composite(self) -> float:
        """Geometric mean of all six dimension scores."""
        scores = [
            self.robustness.score,
            self.persistence.score,
            self.token_efficiency.score,
            self.speed.score,
            self.topology.score,
            self.quality.score,
        ]
        if any(s <= 0 for s in scores):
            return 0.0
        return math.exp(statistics.mean(math.log(s) for s in scores))

    def as_dict(self) -> dict[str, float]:
        return {
            "mao_score": self.composite,
            "robustness": self.robustness.score,
            "persistence": self.persistence.score,
            "token_efficiency": self.token_efficiency.score,
            "speed": self.speed.score,
            "topology": self.topology.score,
            "quality": self.quality.score,
        }


# ─── Individual Scorers ───────────────────────────────────────────────────────


def score_quality(runs: Sequence[TaskRun]) -> DimensionScore:
    """
    Quality dimension: correctness and completeness of agent outputs.
    Q = 0.45 * csr + 0.30 * tpr + 0.10 * sas + 0.15 * (1 - rr)
    """
    csr_values: list[float] = []
    tpr_values: list[float] = []
    sas_values: list[float] = []
    rr_values: list[float] = []

    task_scores: dict[str, float] = {}

    for run in runs:
        if run.oracle_result is None:
            csr = 0.0
        else:
            csr = run.oracle_result.claims_satisfaction_rate
        csr_values.append(csr)

        tpr = run.oracle_result.test_pass_rate if run.oracle_result else 0.0
        tpr_values.append(tpr if tpr is not None else 0.0)

        sas = run.oracle_result.static_analysis_score if run.oracle_result else 0.0
        sas_values.append(sas if sas is not None else 0.5)  # neutral default

        rr = run.oracle_result.regression_rate if run.oracle_result else 0.0
        rr_values.append(rr if rr is not None else 0.0)

        task_q = 0.45 * csr + 0.30 * (tpr or 0.0) + 0.10 * (sas or 0.5) + 0.15 * (1 - (rr or 0.0))
        task_scores[run.task_id] = task_q

    csr = statistics.mean(csr_values) if csr_values else 0.0
    tpr = statistics.mean(v for v in tpr_values if v is not None) if tpr_values else 0.0
    sas = statistics.mean(v for v in sas_values if v is not None) if sas_values else 0.5
    rr = statistics.mean(v for v in rr_values if v is not None) if rr_values else 0.0

    score = 0.45 * csr + 0.30 * tpr + 0.10 * sas + 0.15 * (1.0 - rr)

    return DimensionScore(
        dimension="quality",
        score=max(0.0, min(1.0, score)),
        raw_metrics={"csr": csr, "tpr": tpr, "sas": sas, "rr": rr},
        task_scores=task_scores,
    )


def score_robustness(runs: Sequence[TaskRun]) -> DimensionScore:
    """
    Robustness dimension.
    R = 0.4 * tcr_1 + 0.2 * gds + 0.2 * err + 0.2 * mcrr
    """
    adversarial_runs = [r for r in runs if r.failure_injections_triggered > 0]

    if not adversarial_runs:
        # No adversarial tasks run — return neutral score with note
        return DimensionScore(
            dimension="robustness",
            score=0.5,
            raw_metrics={"note": 0.0, "adversarial_tasks": 0.0},
        )

    # tcr_1: fraction completed despite at least 1 failure injection
    tcr_1 = sum(
        1 for r in adversarial_runs
        if r.oracle_result is not None and r.oracle_result.claims_satisfaction_rate > 0.9
    ) / len(adversarial_runs)

    # gds: partial credit for tasks that failed but made progress
    failed_runs = [
        r for r in adversarial_runs
        if r.oracle_result is None or r.oracle_result.claims_satisfaction_rate <= 0.9
    ]
    gds = statistics.mean(
        r.oracle_result.claims_satisfaction_rate if r.oracle_result else 0.0
        for r in failed_runs
    ) if failed_runs else 1.0

    # mcrr: merge conflict resolution rate
    total_conflicts = sum(r.merge_conflicts for r in runs)
    resolved_conflicts = sum(r.merge_conflicts_resolved for r in runs)
    mcrr = resolved_conflicts / total_conflicts if total_conflicts > 0 else 1.0

    # err: tool error recovery (placeholder — requires telemetry data)
    # TODO: wire from telemetry pipeline once implemented
    err = 0.5  # neutral until telemetry is wired

    score = 0.4 * tcr_1 + 0.2 * gds + 0.2 * err + 0.2 * mcrr

    return DimensionScore(
        dimension="robustness",
        score=max(0.0, min(1.0, score)),
        raw_metrics={"tcr_1": tcr_1, "gds": gds, "err": err, "mcrr": mcrr},
    )


def score_token_efficiency(runs: Sequence[TaskRun]) -> DimensionScore:
    """
    Token efficiency dimension.
    T = normalize(1/tpt)*0.35 + (1-cof)*0.30 + (1-rrc)*0.20 + normalize(cr)*0.15
    """
    completed_runs = [r for r in runs if r.oracle_result is not None]
    if not completed_runs:
        return DimensionScore(dimension="token_efficiency", score=0.0)

    tpt_values = []
    cof_values = []

    for run in completed_runs:
        usage = run.total_token_usage
        tpt_values.append(usage.total_tokens)
        cof_values.append(usage.coordination_overhead_fraction)

    tpt = statistics.mean(tpt_values) if tpt_values else 0.0
    cof = statistics.mean(cof_values) if cof_values else 0.0

    # rrc and cr require telemetry data — placeholder neutral values
    rrc = 0.2  # TODO: wire from telemetry
    cr = 2.0   # TODO: wire from compaction events

    # Normalize tpt: 50k tokens = 1.0 score baseline (adjust empirically)
    tpt_score = min(1.0, 50_000 / max(tpt, 1))
    cr_score = min(1.0, (cr - 1.0) / 4.0)  # 5x compaction = perfect score

    score = 0.35 * tpt_score + 0.30 * (1 - cof) + 0.20 * (1 - rrc) + 0.15 * cr_score

    return DimensionScore(
        dimension="token_efficiency",
        score=max(0.0, min(1.0, score)),
        raw_metrics={"tpt": tpt, "cof": cof, "rrc": rrc, "cr": cr},
    )


def score_speed(runs: Sequence[TaskRun]) -> DimensionScore:
    """
    Speed dimension.
    S = normalize(1/wctc)*0.40 + normalize(1/ahc)*0.25 + pe*0.20 + normalize(1/ttfd)*0.15
    """
    completed = [r for r in runs if r.end_time is not None]
    if not completed:
        return DimensionScore(dimension="speed", score=0.0)

    wctc_values = [r.wall_clock_seconds for r in completed]
    ahc_values = [r.agent_hours for r in completed]

    wctc = statistics.mean(wctc_values)
    ahc = statistics.mean(ahc_values)

    # Normalize: 1800s (30 min) = 0.5 score for wctc
    wctc_score = min(1.0, 900 / max(wctc, 1))
    ahc_score = min(1.0, 0.5 / max(ahc, 0.001))

    # pe and ttfd require additional instrumentation — placeholder
    pe = 0.7     # TODO: wire from agent topology data
    ttfd_score = 0.5  # TODO: wire from first-deliverable tracking

    score = 0.40 * wctc_score + 0.25 * ahc_score + 0.20 * pe + 0.15 * ttfd_score

    return DimensionScore(
        dimension="speed",
        score=max(0.0, min(1.0, score)),
        raw_metrics={"wctc": wctc, "ahc": ahc, "pe": pe},
    )


def score_persistence(runs: Sequence[TaskRun]) -> DimensionScore:
    """
    Persistence dimension — primarily measured on long_horizon tasks.
    P = 0.35*mstcr + 0.25*crf + 0.25*rdo_score + 0.15*dgp
    """
    long_horizon_runs = [r for r in runs]  # filter by tier requires Task objects

    # Until we have session boundary telemetry, approximate from run data
    # TODO: wire crf, rdo, dgp from session checkpoint instrumentation

    mstcr = sum(
        1 for r in long_horizon_runs
        if r.oracle_result and r.oracle_result.claims_satisfaction_rate > 0.9
    ) / max(len(long_horizon_runs), 1)

    crf = 0.5    # TODO: wire from session boundary checkpointing
    rdo = 0.3    # TODO: wire from telemetry (tokens before first new action)
    dgp = 0.5    # TODO: wire from beads dependency graph comparison

    rdo_score = max(0.0, 1.0 - rdo * 5)
    score = 0.35 * mstcr + 0.25 * crf + 0.25 * rdo_score + 0.15 * dgp

    return DimensionScore(
        dimension="persistence",
        score=max(0.0, min(1.0, score)),
        raw_metrics={"mstcr": mstcr, "crf": crf, "rdo": rdo, "dgp": dgp},
    )


def score_topology(runs: Sequence[TaskRun]) -> DimensionScore:
    """
    Topology / coordination quality dimension.
    O = bas*0.35 + normalize(oace)*0.35 + (1 - dwr*10)*0.30
    """
    # Duplicate work rate: tasks claimed by 2+ agents
    # TODO: wire from beads claim telemetry
    dwr = 0.0

    # Bottleneck agent score and oace require full agent topology data
    # TODO: wire from telemetry graph analysis
    bas = 0.7
    oace = 0.6

    dwr_score = max(0.0, 1.0 - dwr * 10)
    score = 0.35 * bas + 0.35 * oace + 0.30 * dwr_score

    return DimensionScore(
        dimension="topology",
        score=max(0.0, min(1.0, score)),
        raw_metrics={"bas": bas, "oace": oace, "dwr": dwr},
    )


# ─── Composite ────────────────────────────────────────────────────────────────


def compute_mao_score(runs: Sequence[TaskRun]) -> MAOScore:
    """Compute all six dimension scores and the composite MAO score."""
    return MAOScore(
        robustness=score_robustness(runs),
        persistence=score_persistence(runs),
        token_efficiency=score_token_efficiency(runs),
        speed=score_speed(runs),
        topology=score_topology(runs),
        quality=score_quality(runs),
    )
