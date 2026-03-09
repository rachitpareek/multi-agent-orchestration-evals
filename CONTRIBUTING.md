# Contributing to MAO-Bench

Thank you for contributing. This guide covers three contribution types:
1. **New tasks** — adding evaluation tasks to the benchmark
2. **New adapters** — adding support for a new orchestration system
3. **Harness improvements** — fixing bugs or improving the evaluation infrastructure

---

## Table of Contents

- [Development Setup](#development-setup)
- [Contributing Tasks](#contributing-tasks)
- [Contributing Adapters](#contributing-adapters)
- [Code Style](#code-style)
- [Running Tests](#running-tests)
- [PR Process](#pr-process)

---

## Development Setup

```bash
git clone https://github.com/rachitpareek/multi-agent-orchestration-evals
cd multi-agent-orchestration-evals

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify setup
maorch list-tasks
```

---

## Contributing Tasks

### Task Quality Bar

Every task must:
- **Be completable**: at least one known solution exists (document it in `reference_output`)
- **Have an automated oracle**: at least 70% of claims must be auto-scorable via `test_command`
- **Be contamination-safe**: tasks should not be derivable from common LLM training data
- **Have partial credit**: claims must be independently scorable (no all-or-nothing)
- **Be reproducible**: the Docker environment must produce identical results on re-runs

### Task Format

See `tasks/schema.yaml` for the full specification. Example tasks:
- `tasks/single_agent/sa_001.yaml` — minimal single-agent task
- `tasks/long_horizon/lh_001.yaml` — multi-session persistence task
- `tasks/adversarial/adv_001.yaml` — failure injection task
- `tasks/parallel_multi/pm_001.yaml` — parallel fan-out task

### Adding a Task

1. Choose the right tier based on the complexity table:

   | Tier | Agents | Sessions | Use when |
   |------|--------|----------|---------|
   | `single_agent` | 1 | 1 | Solvable by one agent in one context window |
   | `parallel_multi` | 2–10 | 1 | Independent parallel sub-problems |
   | `sequential_multi` | 2–10 | 1–2 | Dependent chain, requires hand-off |
   | `long_horizon` | 1–5 | 3+ | Cannot fit in one context window |
   | `adversarial` | 2–10 | 1–3 | Tests robustness under failure |
   | `federated` | 2–20 | 1–5 | Cross-repo or cross-organization |

2. Copy the appropriate tier's example task and fill in all required fields.

3. Set a valid ID: `<tier_prefix>_<NNN>` (e.g., `sa_042`, `pm_012`).

4. Write at least 4 claims. At least 3 must have `automated: true` with a working `test_command`.

5. Test your task locally:
   ```bash
   maorch run --task tasks/your_tier/your_task.yaml --adapter claude-code --dry-run
   ```

6. Verify all automated claims pass against your reference solution:
   ```bash
   # Apply your reference patch, then:
   for cmd in $(yq '.oracle.claims[].test_command' tasks/your_task.yaml); do
     echo "--- $cmd"; bash -c "$cmd"; done
   ```

7. Open a PR. The review checklist:
   - [ ] Task ID follows naming convention
   - [ ] All required YAML fields are present
   - [ ] Docker image is pinned (includes `@sha256:...` digest)
   - [ ] All automated claims have been tested
   - [ ] Contamination check is filled in
   - [ ] Reference output or patch is included in the PR (not committed, for reviewer only)
   - [ ] At least one annotator besides the author reviewed the task

---

## Contributing Adapters

An adapter wraps any orchestration system behind the `OrchestratorAdapter` interface.

### Adapter Interface

```python
from harness.adapters.base import OrchestratorAdapter
from harness.models import Task, TaskRun

class MyAdapter(OrchestratorAdapter):
    @property
    def name(self) -> str:
        return "my-system"

    @property
    def version(self) -> str:
        return "0.1.0"

    def setup(self, task: Task, run_config: dict) -> None:
        # Pull containers, initialize orchestration system, etc.
        ...

    def run(self, task: Task, run_id: str) -> TaskRun:
        # Inject prompt, run agents, collect metrics
        # MUST return a TaskRun even if the task fails
        ...

    def cleanup(self, task: Task) -> None:
        # Tear down containers, remove temp files
        ...
```

See `harness/adapters/claude_code.py` for a complete example.

### Metric Collection Requirements

Your adapter must populate these `TaskRun` fields for a valid leaderboard submission:
- `agents` — list of `AgentRun` objects with timing and token usage
- `merge_conflicts` + `merge_conflicts_resolved` — if applicable
- `failure_injections_triggered` — for adversarial tasks

Token usage must be populated in `AgentRun.token_usage`:
- `input_tokens`, `output_tokens` — required
- `coordination_tokens` — required for topology metrics
- `cache_read_tokens`, `cache_write_tokens` — optional but recommended

### Adding Your Adapter

1. Create `harness/adapters/your_system.py`
2. Register it in `harness/cli.py` → `_load_adapter()`
3. Write integration tests in `tests/integration/test_adapter_your_system.py`
4. Add a config template in `baselines/configs/your_system.yaml`
5. Open a PR

---

## Code Style

```bash
# Format
make fmt

# Lint
make lint

# Type check
make typecheck
```

We use `ruff` for linting, `black` for formatting, `mypy --strict` for types.

---

## Running Tests

```bash
# All tests
make test

# Just unit tests (fast, no Docker)
pytest tests/unit/ -v

# Integration tests (requires Docker)
pytest tests/integration/ -v
```

---

## PR Process

1. Fork the repo, create a feature branch (`task/sa-042-pagination-bug` or `adapter/crewai` or `fix/scoring-edge-case`)
2. Write or update tests
3. Run `make lint typecheck test`
4. Open a PR with a clear description: what changed, why, and how to verify
5. Leaderboard result submissions: include a `baselines/results/<run_id>_summary.json`

Maintainers aim to review PRs within 5 business days.

---

## Questions?

Open a GitHub issue or start a discussion. For real-time chat, join [gastownhall.ai](https://gastownhall.ai) — that's where the MAO-Bench and Gas Town communities overlap.
