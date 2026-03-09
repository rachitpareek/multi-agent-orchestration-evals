"""
Adapter for single Claude Code agent (the floor baseline).

This adapter runs a single `claude` CLI process inside the task Docker sandbox,
injects the task prompt, and collects all metrics via Claude Code hooks.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness.adapters.base import OrchestratorAdapter
from harness.models import AgentRun, Task, TaskRun, TokenUsage


class ClaudeCodeAdapter(OrchestratorAdapter):
    """
    Single-agent Claude Code baseline adapter.

    Uses the `claude` CLI with a custom CLAUDE.md that:
    - Injects the task prompt and oracle acceptance criteria
    - Configures the PreCompact hook to checkpoint state
    - Wires a SessionStart hook to load task context
    - Captures all tool call events via the PostToolUse hook

    Token usage is read from Claude Code's structured output (--output-format json).
    """

    SUPPORTED_TIERS = {"single_agent"}  # single-agent only

    def __init__(self, model: str = "claude-opus-4-6", timeout_seconds: int = 1800):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._sandbox_dir: Path | None = None
        self._container_id: str | None = None

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def supported_tiers(self) -> set[str]:
        return self.SUPPORTED_TIERS

    def setup(self, task: Task, run_config: dict[str, Any]) -> None:
        """
        Pull the task Docker image, start the container, clone the repo,
        and write CLAUDE.md with task context and hook configuration.
        """
        self._sandbox_dir = Path(tempfile.mkdtemp(prefix=f"maorch_{task.id}_"))

        # Write CLAUDE.md into the sandbox
        claude_md = self._build_claude_md(task)
        (self._sandbox_dir / "CLAUDE.md").write_text(claude_md)

        # TODO: pull docker image, start container, mount sandbox_dir
        # docker run -d --rm -v {sandbox_dir}:/workspace {task.environment.docker_image}
        # self._container_id = ...

    def run(self, task: Task, run_id: str) -> TaskRun:
        """
        Run `claude --print --output-format json -p "<prompt>"` inside the sandbox.

        Returns a TaskRun with timing and token metrics populated from
        Claude Code's structured JSON output.
        """
        start_time = datetime.now(timezone.utc)
        agent_id = f"cc_{uuid.uuid4().hex[:8]}"

        agent_run = AgentRun(
            agent_id=agent_id,
            role="worker",
            start_time=start_time,
        )

        error: str | None = None
        raw_output: dict[str, Any] = {}

        try:
            result = subprocess.run(
                [
                    "claude",
                    "--print",
                    "--output-format", "json",
                    "--model", self.model,
                    "-p", task.prompt,
                ],
                cwd=self._sandbox_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )

            if result.stdout:
                try:
                    raw_output = json.loads(result.stdout)
                except json.JSONDecodeError:
                    raw_output = {"raw": result.stdout}

            if result.returncode != 0:
                error = f"claude exited with code {result.returncode}: {result.stderr[:500]}"

        except subprocess.TimeoutExpired:
            error = f"Task timed out after {self.timeout_seconds}s"
        except FileNotFoundError:
            error = "claude CLI not found — is Claude Code installed?"

        end_time = datetime.now(timezone.utc)
        agent_run.end_time = end_time
        agent_run.failed = error is not None

        # Extract token usage from Claude Code JSON output
        if "usage" in raw_output:
            usage = raw_output["usage"]
            agent_run.token_usage = TokenUsage(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                cache_read_tokens=usage.get("cache_read_input_tokens", 0),
                cache_write_tokens=usage.get("cache_creation_input_tokens", 0),
            )

        return TaskRun(
            task_id=task.id,
            run_id=run_id,
            adapter=self.name,
            adapter_version=self.version,
            model=self.model,
            start_time=start_time,
            end_time=end_time,
            agents=[agent_run],
            error=error,
        )

    def cleanup(self, task: Task) -> None:
        """Stop the container and remove the sandbox directory."""
        if self._container_id:
            try:
                subprocess.run(
                    ["docker", "stop", self._container_id],
                    capture_output=True,
                    timeout=30,
                )
            except Exception:
                pass  # best-effort cleanup
            self._container_id = None

        if self._sandbox_dir and self._sandbox_dir.exists():
            import shutil
            try:
                shutil.rmtree(self._sandbox_dir)
            except Exception:
                pass
            self._sandbox_dir = None

    def _build_claude_md(self, task: Task) -> str:
        """Build the CLAUDE.md injected into the task sandbox."""
        lines = [
            "# Task Context (MAO-Bench Evaluation)",
            "",
            "You are being evaluated by the MAO-Bench harness.",
            "Complete the task described below as thoroughly as possible.",
            "",
            "## Task",
            "",
            task.prompt,
            "",
        ]

        if task.context.background:
            lines += ["## Background", "", task.context.background, ""]

        lines += [
            "## Acceptance Criteria",
            "",
            "Your solution will be scored against the following claims:",
            "",
        ]
        for claim in task.oracle.claims:
            lines.append(f"- [ ] {claim.claim}")

        lines += [
            "",
            "## Completion",
            "",
            "When you believe the task is complete, write a brief summary of:",
            "1. What you changed and why",
            "2. Which acceptance criteria you believe are satisfied",
            "3. Any known limitations or edge cases you didn't address",
        ]

        return "\n".join(lines)
