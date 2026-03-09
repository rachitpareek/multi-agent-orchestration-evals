"""
Abstract base class for all orchestration system adapters.

To add a new orchestration system to MAO-Bench, subclass OrchestratorAdapter
and implement all abstract methods. See adapters/claude_code.py for the
reference implementation.
"""

from __future__ import annotations

import abc
from typing import Any

from harness.models import BenchmarkRun, Task, TaskRun


class OrchestratorAdapter(abc.ABC):
    """
    Abstract interface that every orchestration system must implement
    to participate in MAO-Bench evaluation.

    Lifecycle per task:
        1. harness calls `setup(task)` → adapter prepares environment
        2. harness calls `run(task)` → adapter runs the orchestration, returns TaskRun
        3. harness calls `cleanup(task)` → adapter tears down environment
        4. harness aggregates results into BenchmarkRun

    Thread safety: each task is run in its own process or subprocess.
    The adapter does not need to be thread-safe.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Short identifier for this adapter (e.g., 'claude-code', 'gas-town')."""
        ...

    @property
    @abc.abstractmethod
    def version(self) -> str:
        """SemVer version string of this adapter."""
        ...

    @property
    def supported_tiers(self) -> set[str]:
        """
        Task tiers this adapter supports. Default: all tiers.
        Override to restrict (e.g., single-agent adapters might not support
        long_horizon or federated tiers).
        """
        return {
            "single_agent",
            "parallel_multi",
            "sequential_multi",
            "long_horizon",
            "adversarial",
            "federated",
        }

    @abc.abstractmethod
    def setup(self, task: Task, run_config: dict[str, Any]) -> None:
        """
        Prepare the execution environment for this task.

        This may include:
        - Pulling and starting Docker containers
        - Cloning the task repository into the sandbox
        - Initializing the orchestration system (e.g., bd init)
        - Configuring MCP servers
        - Setting up telemetry hooks

        Must be idempotent (safe to call again after a failed setup).
        Raises: RuntimeError if setup cannot complete.
        """
        ...

    @abc.abstractmethod
    def run(self, task: Task, run_id: str) -> TaskRun:
        """
        Execute the task using this orchestration system.

        The adapter is responsible for:
        - Injecting the task prompt into the orchestration system
        - Starting the appropriate number and type of agents
        - Monitoring agent health and handling failures
        - Collecting all telemetry (token usage, timing, tool calls)
        - Returning a complete TaskRun on success OR failure

        This method MUST return even if the task fails — errors are recorded
        in TaskRun.error and TaskRun.oracle_result will reflect partial progress.

        Args:
            task: The task definition.
            run_id: Unique identifier for this run (used for telemetry correlation).

        Returns:
            TaskRun with all collected metrics populated.
        """
        ...

    @abc.abstractmethod
    def cleanup(self, task: Task) -> None:
        """
        Tear down all resources created during setup() and run().

        Must be called even if run() raised an exception.
        Should not raise exceptions — log and continue on cleanup errors.
        """
        ...

    def get_capabilities(self) -> dict[str, Any]:
        """
        Return a machine-readable capability descriptor for this adapter.
        Used by the harness to filter tasks appropriately.
        """
        return {
            "name": self.name,
            "version": self.version,
            "supported_tiers": list(self.supported_tiers),
        }

    # ─── Optional hooks ──────────────────────────────────────────────────────

    def on_agent_start(self, agent_id: str, role: str) -> None:
        """Called when an agent process is started. Override for custom logging."""

    def on_agent_fail(self, agent_id: str, error: str) -> None:
        """Called when an agent process fails unexpectedly."""

    def on_compaction(self, agent_id: str, before_tokens: int, after_tokens: int) -> None:
        """Called when an agent's context is compacted."""

    def on_merge_conflict(self, agent_id: str, file_path: str, resolved: bool) -> None:
        """Called when a merge conflict is detected and (optionally) resolved."""
