"""
CLI entry point for the MAO-Bench harness.

    maorch run --suite single_agent --adapter claude-code
    maorch run --task tasks/single_agent/sa_001.yaml --adapter claude-code
    maorch report --results baselines/results/run_001.jsonl
    maorch list-tasks --tier parallel_multi
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()
logging.basicConfig(level=logging.INFO, format="%(message)s")


@click.group()
@click.version_option()
def main() -> None:
    """MAO-Bench: Multi-Agent Orchestration Evaluation Framework."""


@main.command()
@click.option("--suite", default=None, help="Task suite (tier name or 'full')")
@click.option("--task", default=None, type=Path, help="Single task YAML file")
@click.option("--adapter", required=True, help="Adapter name (claude-code, gas-town, ...)")
@click.option("--model", default="claude-opus-4-6", help="LLM model identifier")
@click.option("--tasks-dir", default=Path("tasks"), type=Path, help="Tasks directory")
@click.option("--results-dir", default=Path("baselines/results"), type=Path)
@click.option("--dry-run", is_flag=True, help="Print tasks without executing")
@click.option("--verbose", "-v", is_flag=True)
def run(
    suite: str | None,
    task: Path | None,
    adapter: str,
    model: str,
    tasks_dir: Path,
    results_dir: Path,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Run the benchmark against an orchestration system."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    from harness.runner import EvalRunner, RunConfig, load_tasks_from_dir

    adapter_obj = _load_adapter(adapter, model)
    config = RunConfig(results_dir=results_dir, dry_run=dry_run)
    runner = EvalRunner(adapter=adapter_obj, config=config)

    if task:
        import yaml
        from harness.models import Task as TaskModel
        data = yaml.safe_load(task.read_text())
        tasks = [TaskModel.model_validate(data)]
    elif suite == "full":
        tasks = load_tasks_from_dir(tasks_dir)
    elif suite:
        tasks = load_tasks_from_dir(tasks_dir, tier=suite)
    else:
        click.echo("Specify --suite or --task", err=True)
        sys.exit(1)

    console.print(f"\n[bold]MAO-Bench[/bold] | adapter={adapter} | tasks={len(tasks)}")
    console.print(f"Model: {model} | Suite: {suite or 'custom'}\n")

    bench_run, score = runner.run_suite(tasks, suite_name=suite or "custom")

    _print_score_table(score)


@main.command()
@click.argument("results_file", type=Path)
def report(results_file: Path) -> None:
    """Display a formatted report from a results JSONL file."""
    import jsonlines
    from harness.models import TaskRun
    from harness.scoring import compute_mao_score

    with jsonlines.open(results_file) as reader:
        runs = [TaskRun.model_validate(obj) for obj in reader]

    score = compute_mao_score(runs)
    _print_score_table(score)

    console.print(f"\n[dim]Tasks: {len(runs)}[/dim]")


@main.command(name="list-tasks")
@click.option("--tier", default=None, help="Filter by tier")
@click.option("--tasks-dir", default=Path("tasks"), type=Path)
def list_tasks(tier: str | None, tasks_dir: Path) -> None:
    """List all available tasks."""
    from harness.runner import load_tasks_from_dir

    tasks = load_tasks_from_dir(tasks_dir, tier=tier)

    table = Table(title=f"Tasks ({len(tasks)})")
    table.add_column("ID", style="cyan")
    table.add_column("Tier")
    table.add_column("Difficulty")
    table.add_column("Title")

    for task in tasks:
        table.add_row(task.id, task.tier.value, task.difficulty.value, task.title)

    console.print(table)


def _load_adapter(name: str, model: str):  # type: ignore[return]
    if name == "claude-code":
        from harness.adapters.claude_code import ClaudeCodeAdapter
        return ClaudeCodeAdapter(model=model)
    else:
        click.echo(f"Unknown adapter: {name}. Available: claude-code", err=True)
        sys.exit(1)


def _print_score_table(score) -> None:  # type: ignore[type-arg]
    from harness.scoring import MAOScore

    table = Table(title="MAO-Bench Results")
    table.add_column("Dimension", style="bold")
    table.add_column("Score", justify="right")

    scores = score.as_dict()
    for dim, val in scores.items():
        style = "green" if val >= 0.7 else "yellow" if val >= 0.4 else "red"
        label = "★ MAO Score" if dim == "mao_score" else dim.replace("_", " ").title()
        table.add_row(label, f"[{style}]{val:.3f}[/{style}]")

    console.print(table)
