# Task Schema Reference

This document is the annotated guide to the MAO-Bench task format. The normative
specification is `tasks/schema.yaml`.

---

## Quick Start

The fastest way to create a new task is to copy an existing one from the appropriate tier:

```bash
cp tasks/single_agent/sa_001.yaml tasks/single_agent/sa_NNN.yaml
# Edit sa_NNN.yaml — fill in all required fields
```

---

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID: `sa_001`, `pm_042`, `lh_008`, `adv_015`, `fed_003` |
| `version` | string | Task file version: `"0.1.0"` |
| `tier` | enum | `single_agent`, `parallel_multi`, `sequential_multi`, `long_horizon`, `adversarial`, `federated` |
| `title` | string | Short title (≤80 chars) |
| `prompt` | string | Task prompt (≥50 chars). **Do not name specific tools or reveal solution approach.** |
| `environment.docker_image` | string | Pinned Docker image with sha256 digest |
| `oracle.claims` | list | At least 3 claims, at least 70% automated |
| `metadata.created_at` | date | ISO date |
| `metadata.annotators` | list | At least 1 annotator |

---

## Claims: The Heart of the Oracle

Claims are the core scoring mechanism. Each claim is a falsifiable statement about the correct solution.

### Good Claims

```yaml
claims:
  - id: "sa_001_c1"
    claim: "The pagination function returns zero duplicate items when total % page_size == 0"
    weight: 0.50
    automated: true
    test_command: "pytest tests/test_pagination.py::test_no_duplicates -q"
```

**Characteristics of good claims:**
- Falsifiable: has a clear true/false answer
- Independent: can be checked without other claims being true first
- Weighted appropriately: core correctness claims get 0.3–0.5 weight; style/docs get 0.1
- Test command is a shell one-liner that exits 0 on pass, non-zero on fail

### Bad Claims (avoid)

```yaml
# Too vague — not falsifiable
- claim: "The code is well-written and clean"

# Not independent — depends on another claim being true first
- claim: "The tests cover all edge cases of the fixed function"

# Binary all-or-nothing — defeats partial credit
- claim: "The entire migration is complete and all tests pass"
```

### Claim Weights

Weights within a task must be positive floats. They don't need to sum to 1.0 (the scorer normalizes by total weight). Use these guidelines:

| Claim Type | Suggested Weight |
|-----------|-----------------|
| Core correctness (does the main thing work?) | 0.30–0.50 |
| Test coverage | 0.20–0.30 |
| Integration/regression (no breakage) | 0.15–0.25 |
| Style/docs/formatting | 0.05–0.15 |
| Meta (did system use correct process?) | 0.05–0.15 |

---

## Environment Specification

### Docker Image

All task environments must use a pinned Docker image:

```yaml
environment:
  docker_image: "ghcr.io/rachitpareek/maobench-sandbox-python:3.12@sha256:abc123..."
```

MAO-Bench maintains a set of standard sandbox images:
- `maobench-sandbox-python:3.12` — Python 3.12, git, pip, pytest, ruff
- `maobench-sandbox-node:20` — Node 20, npm, Jest (coming soon)
- `maobench-sandbox-go:1.23` — Go 1.23, go test (coming soon)

For custom images, include a `Dockerfile` in your PR.

### Failure Injections (adversarial tier only)

```yaml
environment:
  failure_injections:
    - type: kill_agent       # or delay_tool, corrupt_tool_output, drop_network
      target: test_writer    # role name to target
      trigger:
        task_progress_fraction: 0.40   # inject at 40% of expected run time
      severity: hard         # hard = cannot recover this agent; soft = transient error
```

---

## Agent Configuration

### Single-Agent Tasks

```yaml
agent_config:
  min_agents: 1
  max_agents: 1
  recommended_agents: 1
  max_sessions: 1
```

### Multi-Agent Tasks

```yaml
agent_config:
  min_agents: 2
  max_agents: 6
  recommended_agents: 4
  roles:
    - role: orchestrator
      count: 1
      description: "Decomposes work and assigns to workers"
    - role: worker
      count: 3
      description: "Implements assigned sub-tasks"
  topology: star      # orchestrator in center; workers report to it
  max_sessions: 2
```

### Topology Options

| Topology | Shape | When to use |
|----------|-------|-------------|
| `star` | One central orchestrator, N workers | Most multi-agent tasks |
| `chain` | A → B → C → D sequential | Pipeline tasks where output feeds next stage |
| `tree` | Hierarchical orchestrators | Large complex tasks with sub-coordination |
| `graph` | Any-to-any communication | Fully collaborative, no hierarchy |
| `free` | System chooses | When you don't want to prescribe topology |

---

## Tier-Specific Guidelines

### `long_horizon` Tasks

- Set `max_sessions: 4` or higher
- Include a claim that rewards explicit use of an issue tracker across sessions
- Prompt should instruct the agent to "track your progress explicitly"
- Token budget should span multiple sessions (500k+ input tokens)

### `adversarial` Tasks

- Always define `failure_injections` in the environment spec
- Include a claim for "system detected failure and recovered" (weight 0.10–0.15)
- Claims should test the _final_ state, not the process (the system should recover)
- Set `severity: hard` for interesting robustness tests; `soft` for transient-error tests

### `federated` Tasks

- Requires `network_policy: full` (DoltHub access needed)
- Define multiple repos in `context.repo` (comma-separated)
- Include claims that verify cross-repo correctness
- Agent config should include a `coordinator` role that manages cross-org work

---

## Contamination Checking

Before submitting a task, check that it is not derivable from common LLM training data:

1. **For sourced tasks** (from real GitHub issues): check that the issue and PR were created after the model's training cutoff
2. **For synthetic tasks**: confirm the specific combination of requirements is novel
3. **Fill in the contamination_check block**:

```yaml
metadata:
  contamination_check:
    checked_at: "2026-03-08"
    method: "web search for task title + GitHub search for similar issues"
    result: "clean"   # clean | suspected | confirmed_contaminated
```

Tasks with `confirmed_contaminated` will not be accepted into the benchmark.
