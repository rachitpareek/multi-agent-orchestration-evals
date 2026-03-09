"""
Orchestration system adapters for MAO-Bench.

Each adapter wraps a specific orchestration system (Claude Code, Gas Town,
CrewAI, etc.) behind the OrchestratorAdapter interface.
"""

from harness.adapters.base import OrchestratorAdapter

__all__ = ["OrchestratorAdapter"]
