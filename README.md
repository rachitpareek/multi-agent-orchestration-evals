# Multi-Agent Orchestration Evals (MAO-Bench)

**An industry-leading benchmark and evaluation framework for multi-agent LLM orchestration systems.**

> *"Anthropic lists 'mastering multi-agent coordination' as the top organizational priority for 2026."*
> *Gartner reported a 1,445% surge in multi-agent system inquiries between Q1 2024 and Q2 2025.*

We have SWE-bench for single-agent coding. We have MCP-Atlas for tool-use. We have nothing rigorous for **multi-agent orchestration** — the coordination layer that determines whether 20 agents working in parallel produce 20× value or 0.2× chaos.

MAO-Bench fills that gap.

---

## What MAO-Bench Measures

Single-agent benchmarks (SWE-bench, HumanEval, MBPP) tell you whether a model can solve a coding task. They say nothing about:

- **Persistence**: Can a system maintain task continuity across compaction cycles and session boundaries? (The "50 First Dates" problem from Beads)
- **Robustness**: Does the system gracefully degrade when agents fail mid-flight, or does one failure cascade into total loss?
- **Token efficiency**: How many tokens does the orchestration layer burn per unit of useful work? What fraction is coordination overhead?
- **Parallelism quality**: Does adding agents actually speed things up, or does coordination cost eat the gains?
- **Topology correctness**: Are the right agents doing the right work with the right dependencies?
- **Long-horizon coherence**: Can a system handle tasks that span dozens of sessions and hundreds of sub-issues without losing track?

These are the dimensions that separate a toy multi-agent demo from production-grade orchestration.

---

## Benchmark Structure

```
425 tasks across 5 tiers:

Single-agent baselines    (100)  — floor; any good single agent should pass
Parallel multi-agent      (100)  — independent work units; tests fan-out quality
Sequential multi-agent    (100)  — dependency chains; tests hand-off fidelity
Long-horizon multi-session (50)  — spans 3+ compaction cycles; tests persistence
Adversarial / robustness   (50)  — injected failures, conflicts, ambiguity; tests recovery
Federated / cross-repo     (25)  — multi-repo coordination; tests trust + merge protocols
```

Each task includes:
- Structured natural-language prompt (no tool names revealed)
- Hermetic sandbox environment (Docker, pinned deps)
- Automated test oracle (test suite + claims rubric)
- Token budget and agent-count hints
- Difficulty tier (Easy / Medium / Hard / Expert)
- Ground-truth partial-credit checklist

---

## Metric Suite

| Dimension | Key Metrics |
|-----------|-------------|
| **Robustness** | Task completion under k-of-N agent failure; error recovery rate |
| **Persistence** | Multi-session task completion rate; context reconstruction fidelity; re-discovery overhead |
| **Token Efficiency** | Tokens/task; coordination overhead fraction; compaction ratio; redundant-read coefficient |
| **Speed** | Wall-clock time to completion; agent-hours consumed; parallelism efficiency; time-to-first-deliverable |
| **Topology** | Fan-out depth; bottleneck agent detection; optimal agent count curve |
| **Quality** | Test pass rate; PR acceptance rate; claims satisfaction; static analysis score |

All metrics are normalized to `[0, 1]` and combined into a **composite MAO score** (geometric mean of dimension scores).

---

## Leaderboard (Seeded Baselines)

| System | MAO Score | Robustness | Persistence | Token Eff. | Speed | Quality |
|--------|-----------|-----------|-------------|------------|-------|---------|
| *Single Claude Code (baseline)* | — | — | — | — | — | — |
| *Gas Town (multi-agent)* | — | — | — | — | — | — |
| *CrewAI* | — | — | — | — | — | — |
| *AutoGen / AG2* | — | — | — | — | — | — |
| *LangGraph* | — | — | — | — | — | — |

> Leaderboard populates as baseline runs complete. See `baselines/results/`.

---

## Quick Start

```bash
# Install
pip install maorch-eval

# Run a single task against a system
maorch run --task tasks/single_agent/sa_001.yaml --adapter claude-code

# Run the full benchmark
maorch run --suite full --adapter gas-town --config baselines/configs/gas_town.yaml

# View results
maorch report --results baselines/results/gas_town_run_001.jsonl
```

---

## Repository Structure

```
maorch-eval/
├── harness/            # Evaluation harness (Python)
│   ├── runner.py       # Main task executor
│   ├── metrics.py      # Metric collectors
│   ├── scoring.py      # Scoring engines
│   ├── oracle.py       # Test oracle
│   ├── telemetry.py    # OpenTelemetry pipeline
│   └── adapters/       # Orchestrator adapters
│       ├── base.py     # Abstract adapter interface
│       ├── claude_code.py
│       └── gas_town.py
├── tasks/              # Benchmark task suite (YAML)
│   ├── schema.yaml     # Task format specification
│   ├── single_agent/
│   ├── parallel_multi/
│   ├── sequential_multi/
│   ├── long_horizon/
│   ├── adversarial/
│   └── federated/
├── data/               # Dataset (raw → annotated → splits)
├── baselines/          # Configs and results for all baseline runs
├── docs/               # Architecture, metrics spec, literature reviews
│   └── literature/     # Per-system research summaries
├── paper/              # LaTeX source for the benchmark paper
├── scripts/            # Setup, analysis, and utility scripts
└── tests/              # Unit and integration tests for the harness
```

---

## Contributing

- **New tasks**: See [docs/TASK_SCHEMA.md](docs/TASK_SCHEMA.md) for the task format and annotation guide.
- **New adapters**: See [CONTRIBUTING.md](CONTRIBUTING.md) for the adapter interface contract.
- **Leaderboard submissions**: Run the harness, produce a result JSONL, open a PR against `baselines/results/`.

All contributions are reviewed for task quality, contamination risk, and annotation completeness.

---

## Design Principles

1. **Measure what matters in production**: Token efficiency, persistence, robustness under failure — not just pass@1.
2. **Ground truth first**: Every task has an automated oracle. No pure LLM-as-judge.
3. **Reproducible by construction**: Hermetic Docker environments, pinned deps, deterministic seeds.
4. **Partial credit, not binary**: Claims-based rubrics reward progress even on hard tasks.
5. **Open extension**: Adapters, tasks, and metric modules are pluggable interfaces.

---

## Citation

```bibtex
@misc{maobench2026,
  title  = {MAO-Bench: An Evaluation Framework for Multi-Agent LLM Orchestration},
  year   = {2026},
  url    = {https://github.com/rachitpareek/multi-agent-orchestration-evals}
}
```

---

## Related Work

- [Gas Town](https://github.com/steveyegge/gastown) — multi-agent orchestration system (primary baseline)
- [Beads](https://github.com/steveyegge/beads) — agent memory system underpinning Gas Town
- [MCP-Atlas](https://arxiv.org/abs/2602.00933) — tool-use benchmark over real MCP servers
- [SWE-bench](https://github.com/SWE-bench/SWE-bench) — single-agent code task benchmark
- [MultiAgentBench](https://arxiv.org/abs/2503.01935) — collaboration/competition benchmark (MARBLE)
