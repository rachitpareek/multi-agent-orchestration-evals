"""
Core data models for MAO-Bench.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class TaskTier(str, enum.Enum):
    SINGLE_AGENT = "single_agent"
    PARALLEL_MULTI = "parallel_multi"
    SEQUENTIAL_MULTI = "sequential_multi"
    LONG_HORIZON = "long_horizon"
    ADVERSARIAL = "adversarial"
    FEDERATED = "federated"


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class NetworkPolicy(str, enum.Enum):
    ISOLATED = "isolated"
    MCP_ONLY = "mcp_only"
    FULL = "full"


class FailureInjectionType(str, enum.Enum):
    KILL_AGENT = "kill_agent"
    DELAY_TOOL = "delay_tool"
    CORRUPT_TOOL_OUTPUT = "corrupt_tool_output"
    DROP_NETWORK = "drop_network"


# ─── Task Schema ──────────────────────────────────────────────────────────────


class Claim(BaseModel):
    id: str
    claim: str
    weight: float = Field(ge=0.0, le=1.0)
    automated: bool = True
    test_command: str | None = None


class TestSuite(BaseModel):
    command: str
    pass_threshold: float = Field(default=1.0, ge=0.0, le=1.0)
    timeout_seconds: int = 300


class Oracle(BaseModel):
    claims: list[Claim]
    test_suite: TestSuite | None = None
    reference_output: str | None = None
    partial_credit: bool = True


class FailureInjection(BaseModel):
    type: FailureInjectionType
    target: str
    trigger: dict[str, Any]
    severity: str = "soft"  # "soft" | "hard"


class AgentRole(BaseModel):
    role: str
    count: int
    description: str


class AgentConfig(BaseModel):
    min_agents: int = 1
    max_agents: int = 1
    recommended_agents: int = 1
    roles: list[AgentRole] = Field(default_factory=list)
    topology: str = "free"
    max_sessions: int = 1


class TokenBudget(BaseModel):
    input_budget: int | None = None
    output_budget: int | None = None
    coordination_budget: int | None = None


class MCPServer(BaseModel):
    name: str
    image: str
    config: dict[str, Any] = Field(default_factory=dict)


class Environment(BaseModel):
    docker_image: str
    setup_commands: list[str] = Field(default_factory=list)
    env_vars: dict[str, str] = Field(default_factory=dict)
    mcp_servers: list[MCPServer] = Field(default_factory=list)
    network_policy: NetworkPolicy = NetworkPolicy.ISOLATED
    failure_injections: list[FailureInjection] = Field(default_factory=list)


class TaskContext(BaseModel):
    issue_url: str | None = None
    repo: str | None = None
    base_commit: str | None = None
    relevant_files: list[str] = Field(default_factory=list)
    background: str | None = None


class TaskMetadata(BaseModel):
    created_at: str
    updated_at: str | None = None
    annotators: list[str]
    source: str | None = None
    source_url: str | None = None
    programming_language: str | None = None
    domain: str | None = None
    tags: list[str] = Field(default_factory=list)


class Task(BaseModel):
    """Full task definition, parsed from a YAML task file."""

    id: str
    version: str = "0.1.0"
    tier: TaskTier
    title: str
    difficulty: Difficulty = Difficulty.MEDIUM
    prompt: str
    context: TaskContext = Field(default_factory=TaskContext)
    agent_config: AgentConfig = Field(default_factory=AgentConfig)
    token_budget: TokenBudget = Field(default_factory=TokenBudget)
    environment: Environment
    oracle: Oracle
    metadata: TaskMetadata


# ─── Run Results ──────────────────────────────────────────────────────────────


class ClaimResult(BaseModel):
    claim_id: str
    passed: bool
    weight: float
    evidence: str | None = None


class OracleResult(BaseModel):
    task_id: str
    claims: list[ClaimResult]
    test_pass_rate: float | None = None
    static_analysis_score: float | None = None
    regression_rate: float | None = None

    @property
    def claims_satisfaction_rate(self) -> float:
        if not self.claims:
            return 0.0
        total_weight = sum(c.weight for c in self.claims)
        if total_weight == 0:
            return 0.0
        return sum(c.weight for c in self.claims if c.passed) / total_weight


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    coordination_tokens: int = 0  # subset of input+output attributable to coordination

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def coordination_overhead_fraction(self) -> float:
        if self.total_tokens == 0:
            return 0.0
        return self.coordination_tokens / self.total_tokens


class AgentRun(BaseModel):
    agent_id: str
    role: str
    start_time: datetime
    end_time: datetime | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    sessions: int = 1
    compaction_events: int = 0
    tool_calls: int = 0
    failed: bool = False

    @property
    def active_seconds(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()


class TaskRun(BaseModel):
    """Full run result for a single task."""

    task_id: str
    run_id: str
    adapter: str
    adapter_version: str
    model: str
    start_time: datetime
    end_time: datetime | None = None
    agents: list[AgentRun] = Field(default_factory=list)
    oracle_result: OracleResult | None = None
    failure_injections_triggered: int = 0
    merge_conflicts: int = 0
    merge_conflicts_resolved: int = 0
    error: str | None = None

    @property
    def wall_clock_seconds(self) -> float:
        if self.end_time is None or self.start_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    @property
    def agent_hours(self) -> float:
        return sum(a.active_seconds for a in self.agents) / 3600.0

    @property
    def total_token_usage(self) -> TokenUsage:
        combined = TokenUsage()
        for agent in self.agents:
            combined.input_tokens += agent.token_usage.input_tokens
            combined.output_tokens += agent.token_usage.output_tokens
            combined.cache_read_tokens += agent.token_usage.cache_read_tokens
            combined.coordination_tokens += agent.token_usage.coordination_tokens
        return combined


class BenchmarkRun(BaseModel):
    """Aggregated results for a full benchmark run."""

    run_id: str
    adapter: str
    adapter_version: str
    model: str
    harness_version: str
    started_at: datetime
    completed_at: datetime | None = None
    task_runs: list[TaskRun] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
