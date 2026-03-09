"""
Main evaluation harness runner.

The runner:
1. Loads task definitions from YAML files
2. For each task, sets up the sandbox, runs the adapter, scores outputs
3. Aggregates results into a BenchmarkRun
4. Writes results to JSONL

Usage (programmatic):
    runner = EvalRunner(adapter=ClaudeCodeAdapter(), config=RunConfig())
    results = runner.run_suite(tasks, suite="single_agent")

Usage (CLI):
    maorch run --suite single_agent --adapter claude-code
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import yaml

from harness.adapters.base import OrchestratorAdapter
from harness.models import BenchmarkRun, Task, TaskRun
from harness.oracle import TaskOracle
from harness.scoring import MAOScore, compute_mao_score

logger = logging.getLogger(__name__)


class RunConfig:
    """Configuration for a benchmark run."""

    def __init__(
        self,
        results_dir: Path = Path("baselines/results"),
        max_parallel_tasks: int = 1,
        dry_run: bool = False,
        task_timeout: int = 3600,
        skip_oracle: bool = False,
    ):
        self.results_dir = results_dir
        self.max_parallel_tasks = max_parallel_tasks
        self.dry_run = dry_run
        self.task_timeout = task_timeout
        self.skip_oracle = skip_oracle


class EvalRunner:
    """
    Orchestrates evaluation of a suite of tasks against one adapter.
    """

    def __init__(self, adapter: OrchestratorAdapter, config: RunConfig | None = None):
        self.adapter = adapter
        self.config = config or RunConfig()
        self._run_id = uuid.uuid4().hex

    def run_suite(
        self,
        tasks: Sequence[Task],
        suite_name: str = "custom",
    ) -> tuple[BenchmarkRun, MAOScore]:
        """
        Run all tasks and return the aggregated BenchmarkRun and MAOScore.
        """
        import harness

        bench_run = BenchmarkRun(
            run_id=self._run_id,
            adapter=self.adapter.name,
            adapter_version=self.adapter.version,
            model=getattr(self.adapter, "model", "unknown"),
            harness_version=harness.__version__,
            started_at=datetime.now(timezone.utc),
            config={"suite": suite_name, "dry_run": self.config.dry_run},
        )

        for i, task in enumerate(tasks):
            logger.info(f"[{i+1}/{len(tasks)}] Running task {task.id}: {task.title}")

            if self.config.dry_run:
                logger.info("  [DRY RUN] Skipping execution")
                continue

            if task.tier.value not in self.adapter.supported_tiers:
                logger.warning(f"  Skipping — adapter does not support tier {task.tier}")
                continue

            task_run = self._run_task(task)
            bench_run.task_runs.append(task_run)

            status = "✓" if task_run.error is None else "✗"
            logger.info(f"  {status} Completed in {task_run.wall_clock_seconds:.1f}s")

        bench_run.completed_at = datetime.now(timezone.utc)

        score = compute_mao_score(bench_run.task_runs)
        self._write_results(bench_run, score)

        return bench_run, score

    def _run_task(self, task: Task) -> TaskRun:
        """Run a single task: setup → run → oracle → cleanup."""
        run_id = f"{self._run_id}_{task.id}"

        try:
            self.adapter.setup(task, run_config={})
        except Exception as e:
            logger.error(f"  Setup failed for {task.id}: {e}")
            return TaskRun(
                task_id=task.id,
                run_id=run_id,
                adapter=self.adapter.name,
                adapter_version=self.adapter.version,
                model=getattr(self.adapter, "model", "unknown"),
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                error=f"Setup failed: {e}",
            )

        try:
            task_run = self.adapter.run(task, run_id=run_id)
        except Exception as e:
            logger.error(f"  Run failed for {task.id}: {e}")
            task_run = TaskRun(
                task_id=task.id,
                run_id=run_id,
                adapter=self.adapter.name,
                adapter_version=self.adapter.version,
                model=getattr(self.adapter, "model", "unknown"),
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                error=f"Run failed: {e}",
            )
        finally:
            try:
                self.adapter.cleanup(task)
            except Exception as e:
                logger.warning(f"  Cleanup warning for {task.id}: {e}")

        return task_run

    def _write_results(self, bench_run: BenchmarkRun, score: MAOScore) -> None:
        """Write results to JSONL and a summary JSON file."""
        self.config.results_dir.mkdir(parents=True, exist_ok=True)

        # Full run results (JSONL — one line per task run)
        results_file = self.config.results_dir / f"{bench_run.run_id}.jsonl"
        with results_file.open("w") as f:
            for task_run in bench_run.task_runs:
                f.write(task_run.model_dump_json() + "\n")

        # Summary JSON
        summary_file = self.config.results_dir / f"{bench_run.run_id}_summary.json"
        summary = {
            "run_id": bench_run.run_id,
            "adapter": bench_run.adapter,
            "model": bench_run.model,
            "harness_version": bench_run.harness_version,
            "started_at": bench_run.started_at.isoformat(),
            "completed_at": bench_run.completed_at.isoformat() if bench_run.completed_at else None,
            "task_count": len(bench_run.task_runs),
            "scores": score.as_dict(),
        }
        summary_file.write_text(json.dumps(summary, indent=2))

        logger.info(f"\nResults written to {results_file}")
        logger.info(f"Summary written to {summary_file}")
        logger.info(f"\nMAO Score: {score.composite:.3f}")
        for dim, val in score.as_dict().items():
            if dim != "mao_score":
                logger.info(f"  {dim:20s}: {val:.3f}")


def load_tasks_from_dir(tasks_dir: Path, tier: str | None = None) -> list[Task]:
    """Load all task YAML files from a directory (optionally filtered by tier)."""
    tasks = []
    pattern = "**/*.yaml"

    for path in sorted(tasks_dir.glob(pattern)):
        if path.name == "schema.yaml":
            continue

        try:
            data = yaml.safe_load(path.read_text())
            task = Task.model_validate(data)
            if tier is None or task.tier.value == tier:
                tasks.append(task)
        except Exception as e:
            logger.warning(f"Failed to load task from {path}: {e}")

    return tasks
