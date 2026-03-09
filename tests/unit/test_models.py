"""
Unit tests for MAO-Bench data models.
"""

from datetime import datetime, timedelta, timezone

import pytest

from harness.models import (
    AgentRun,
    BenchmarkRun,
    ClaimResult,
    OracleResult,
    TaskRun,
    TokenUsage,
)


class TestTokenUsage:
    def test_total_tokens(self):
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        assert usage.total_tokens == 1500

    def test_coordination_overhead_fraction(self):
        usage = TokenUsage(input_tokens=1000, output_tokens=1000, coordination_tokens=400)
        assert usage.coordination_overhead_fraction == pytest.approx(0.2)

    def test_zero_total_tokens(self):
        usage = TokenUsage()
        assert usage.coordination_overhead_fraction == 0.0


class TestAgentRun:
    def test_active_seconds(self):
        now = datetime.now(timezone.utc)
        agent = AgentRun(
            agent_id="a1",
            role="worker",
            start_time=now,
            end_time=now + timedelta(seconds=120),
        )
        assert agent.active_seconds == pytest.approx(120.0)

    def test_active_seconds_no_end_time(self):
        now = datetime.now(timezone.utc)
        agent = AgentRun(agent_id="a1", role="worker", start_time=now)
        assert agent.active_seconds == 0.0


class TestTaskRun:
    def test_wall_clock_seconds(self):
        now = datetime.now(timezone.utc)
        run = TaskRun(
            task_id="sa_001",
            run_id="r1",
            adapter="test",
            adapter_version="0.1",
            model="test-model",
            start_time=now,
            end_time=now + timedelta(seconds=300),
        )
        assert run.wall_clock_seconds == pytest.approx(300.0)

    def test_agent_hours(self):
        now = datetime.now(timezone.utc)
        agent = AgentRun(
            agent_id="a1",
            role="worker",
            start_time=now,
            end_time=now + timedelta(seconds=3600),
        )
        run = TaskRun(
            task_id="sa_001",
            run_id="r1",
            adapter="test",
            adapter_version="0.1",
            model="test-model",
            start_time=now,
            agents=[agent],
        )
        assert run.agent_hours == pytest.approx(1.0)

    def test_total_token_usage_aggregation(self):
        now = datetime.now(timezone.utc)
        agent_a = AgentRun(
            agent_id="a1", role="worker", start_time=now,
            token_usage=TokenUsage(input_tokens=1000, output_tokens=500),
        )
        agent_b = AgentRun(
            agent_id="a2", role="worker", start_time=now,
            token_usage=TokenUsage(input_tokens=2000, output_tokens=800),
        )
        run = TaskRun(
            task_id="sa_001", run_id="r1", adapter="test",
            adapter_version="0.1", model="test-model", start_time=now,
            agents=[agent_a, agent_b],
        )
        assert run.total_token_usage.input_tokens == 3000
        assert run.total_token_usage.output_tokens == 1300


class TestOracleResult:
    def test_claims_satisfaction_rate_all_pass(self):
        result = OracleResult(
            task_id="sa_001",
            claims=[
                ClaimResult(claim_id="c1", passed=True, weight=0.5),
                ClaimResult(claim_id="c2", passed=True, weight=0.5),
            ],
        )
        assert result.claims_satisfaction_rate == pytest.approx(1.0)

    def test_claims_satisfaction_rate_partial(self):
        result = OracleResult(
            task_id="sa_001",
            claims=[
                ClaimResult(claim_id="c1", passed=True, weight=0.6),
                ClaimResult(claim_id="c2", passed=False, weight=0.4),
            ],
        )
        assert result.claims_satisfaction_rate == pytest.approx(0.6)

    def test_claims_satisfaction_rate_none_pass(self):
        result = OracleResult(
            task_id="sa_001",
            claims=[
                ClaimResult(claim_id="c1", passed=False, weight=1.0),
            ],
        )
        assert result.claims_satisfaction_rate == pytest.approx(0.0)

    def test_empty_claims(self):
        result = OracleResult(task_id="sa_001", claims=[])
        assert result.claims_satisfaction_rate == 0.0
