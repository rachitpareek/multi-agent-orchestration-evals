"""
Unit tests for the MAO-Bench scoring engine.
"""

import math
from datetime import datetime, timezone

import pytest

from harness.models import (
    AgentRun,
    BenchmarkRun,
    Claim,
    ClaimResult,
    OracleResult,
    TaskRun,
    TokenUsage,
)
from harness.scoring import (
    MAOScore,
    compute_mao_score,
    score_quality,
    score_robustness,
    score_speed,
    score_token_efficiency,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────


def make_task_run(
    task_id: str = "sa_001",
    claims_passed: list[bool] | None = None,
    claims_weights: list[float] | None = None,
    wall_clock_seconds: float = 300.0,
    input_tokens: int = 10_000,
    output_tokens: int = 3_000,
    coordination_tokens: int = 500,
    failure_injections: int = 0,
    merge_conflicts: int = 0,
    merge_conflicts_resolved: int = 0,
) -> TaskRun:
    if claims_passed is None:
        claims_passed = [True, True, False]
    if claims_weights is None:
        claims_weights = [0.5, 0.3, 0.2]

    claims = [
        ClaimResult(claim_id=f"c{i}", passed=p, weight=w)
        for i, (p, w) in enumerate(zip(claims_passed, claims_weights))
    ]

    now = datetime.now(timezone.utc)
    agent = AgentRun(
        agent_id="agent_0",
        role="worker",
        start_time=now,
        end_time=now,
        token_usage=TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            coordination_tokens=coordination_tokens,
        ),
    )
    # Patch wall_clock_seconds
    from datetime import timedelta
    agent.end_time = now + timedelta(seconds=wall_clock_seconds)

    run = TaskRun(
        task_id=task_id,
        run_id=f"run_{task_id}",
        adapter="claude-code",
        adapter_version="0.1.0",
        model="claude-opus-4-6",
        start_time=now,
        end_time=now + timedelta(seconds=wall_clock_seconds),
        agents=[agent],
        oracle_result=OracleResult(
            task_id=task_id,
            claims=claims,
            test_pass_rate=0.9,
            static_analysis_score=0.85,
            regression_rate=0.0,
        ),
        failure_injections_triggered=failure_injections,
        merge_conflicts=merge_conflicts,
        merge_conflicts_resolved=merge_conflicts_resolved,
    )
    return run


# ─── Quality Scorer ───────────────────────────────────────────────────────────


class TestQualityScorer:
    def test_perfect_score(self):
        run = make_task_run(claims_passed=[True, True, True])
        result = score_quality([run])
        assert result.score > 0.9

    def test_zero_score_no_claims_passed(self):
        run = make_task_run(claims_passed=[False, False, False])
        result = score_quality([run])
        assert result.score < 0.3

    def test_partial_credit(self):
        # 2 of 3 claims passed, weights 0.5/0.3/0.2
        run = make_task_run(claims_passed=[True, True, False], claims_weights=[0.5, 0.3, 0.2])
        result = score_quality([run])
        # csr = (0.5 + 0.3) / 1.0 = 0.8
        assert result.raw_metrics["csr"] == pytest.approx(0.8, abs=0.01)

    def test_score_in_range(self):
        run = make_task_run()
        result = score_quality([run])
        assert 0.0 <= result.score <= 1.0

    def test_no_oracle_result(self):
        run = make_task_run()
        run.oracle_result = None
        result = score_quality([run])
        assert result.score < 0.2

    def test_multiple_runs_averaged(self):
        run_a = make_task_run("sa_001", claims_passed=[True, True, True])
        run_b = make_task_run("sa_002", claims_passed=[False, False, False])
        result = score_quality([run_a, run_b])
        # Should be roughly halfway between perfect and zero
        assert 0.3 < result.score < 0.7

    def test_weighted_claims_respected(self):
        # Heavy claim passes, light claims fail
        run_a = make_task_run(claims_passed=[True, False, False], claims_weights=[0.8, 0.1, 0.1])
        run_b = make_task_run(claims_passed=[False, True, True], claims_weights=[0.8, 0.1, 0.1])
        result_a = score_quality([run_a])
        result_b = score_quality([run_b])
        # run_a should score higher (heavy claim passed)
        assert result_a.score > result_b.score


# ─── Token Efficiency Scorer ──────────────────────────────────────────────────


class TestTokenEfficiencyScorer:
    def test_low_tokens_scores_higher(self):
        run_cheap = make_task_run(input_tokens=5_000, output_tokens=1_000)
        run_expensive = make_task_run(input_tokens=200_000, output_tokens=50_000)
        result_cheap = score_token_efficiency([run_cheap])
        result_expensive = score_token_efficiency([run_expensive])
        assert result_cheap.score > result_expensive.score

    def test_low_coordination_overhead_scores_higher(self):
        run_low = make_task_run(input_tokens=10_000, coordination_tokens=100)
        run_high = make_task_run(input_tokens=10_000, coordination_tokens=8_000)
        result_low = score_token_efficiency([run_low])
        result_high = score_token_efficiency([run_high])
        assert result_low.score > result_high.score

    def test_score_in_range(self):
        run = make_task_run()
        result = score_token_efficiency([run])
        assert 0.0 <= result.score <= 1.0


# ─── Speed Scorer ─────────────────────────────────────────────────────────────


class TestSpeedScorer:
    def test_faster_scores_higher(self):
        run_fast = make_task_run(wall_clock_seconds=60.0)
        run_slow = make_task_run(wall_clock_seconds=3600.0)
        result_fast = score_speed([run_fast])
        result_slow = score_speed([run_slow])
        assert result_fast.score > result_slow.score

    def test_score_in_range(self):
        run = make_task_run()
        result = score_speed([run])
        assert 0.0 <= result.score <= 1.0


# ─── Composite Score ──────────────────────────────────────────────────────────


class TestCompositeScore:
    def test_geometric_mean_computed(self):
        run = make_task_run(claims_passed=[True, True, True])
        mao = compute_mao_score([run])
        assert isinstance(mao.composite, float)
        assert 0.0 <= mao.composite <= 1.0

    def test_zero_on_one_zero_dimension(self):
        # If quality is 0, composite should be 0 (geometric mean with a zero factor)
        run = make_task_run(claims_passed=[False, False, False])
        run.oracle_result = None
        mao = compute_mao_score([run])
        assert mao.composite == 0.0

    def test_as_dict_has_all_keys(self):
        run = make_task_run()
        mao = compute_mao_score([run])
        d = mao.as_dict()
        required = {"mao_score", "robustness", "persistence", "token_efficiency", "speed", "topology", "quality"}
        assert required.issubset(d.keys())

    def test_all_dimensions_in_range(self):
        run = make_task_run()
        mao = compute_mao_score([run])
        for key, val in mao.as_dict().items():
            assert 0.0 <= val <= 1.0, f"{key} = {val} out of range"
