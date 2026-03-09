# MCP-Atlas — Research Summary

**Paper**: ["MCP-Atlas: A Large-Scale Benchmark for Tool-Use Competency with Real MCP Servers"](https://arxiv.org/abs/2602.00933)
**arXiv**: 2602.00933 | Submitted: Jan 31, 2026 | Authors: Chaithanya Bandi et al. (16 authors)

---

## Overview

MCP-Atlas is the most comprehensive tool-use benchmark built on the Model Context Protocol (MCP) to date. It evaluates LLM agents on realistic, multi-step tool-use workflows across real MCP servers — not synthetic or simplified tool environments.

**Scale**: 36 real MCP servers, 220 tools, 1,000 tasks.

---

## Why MCP-Atlas Matters for MAO-Bench

MCP-Atlas is the closest prior work to MAO-Bench in spirit — a rigorous, reproducible, large-scale evaluation of LLM agents in realistic tool environments. It establishes the methodological baseline we build on.

**Where MCP-Atlas stops, MAO-Bench begins**: MCP-Atlas evaluates a *single agent* using *multiple tools*. MAO-Bench evaluates *multiple agents* coordinating to solve tasks that no single agent could handle alone. MCP-Atlas is a prerequisite skill; MAO-Bench measures the orchestration layer on top.

---

## Task Design

Tasks use **natural language prompts that avoid naming specific tools or servers**. The agent must:
1. Discover the right tools from the available server catalog
2. Sequence 3–6 tool calls across multiple servers
3. Handle tool errors and retry where appropriate
4. Produce a final answer satisfying the task claims

This "no tool name" design is borrowed directly into MAO-Bench task prompts — agents must demonstrate genuine tool discovery, not just tool invocation.

---

## Scoring: Claims-Based Rubric

Each task is scored against a **structured claims checklist** — a list of factual assertions the correct answer must satisfy. Partial credit is awarded per-claim, making the score continuous (not binary pass/fail).

Complementary diagnostics:
| Diagnostic Axis | What It Measures |
|----------------|-----------------|
| Tool discovery | Did the agent find the right server/tool? |
| Parameterization | Were tool call parameters correct? |
| Syntax | Were calls syntactically valid? |
| Error recovery | Did the agent retry on failure? |
| Efficiency | How many unnecessary tool calls were made? |

MAO-Bench adopts this exact rubric structure and extends it with multi-agent coordination diagnostics.

---

## Results

Best-performing model: **Claude Opus 4.5 at 62.3% success rate**.

Key findings:
- Top models exceed 50%; next-best cluster in 20–40% range with high variance
- Failures concentrate in **Tool Usage** (wrong server, bad parameters, sequencing errors) and **Task Understanding** (premature stopping, misinterpreted goals)
- Performance drops sharply on tasks requiring 5+ tool calls vs. 3-call tasks
- Error recovery is a significant differentiator between top and mid-tier models

This establishes the single-agent tool-use ceiling that MAO-Bench's multi-agent orchestration should, in theory, be able to surpass.

---

## Infrastructure

- **Containerized harness**: Docker-based, hermetic, reproducible
- **500-task public subset**: released for community use
- **Full task schema**: released for task contribution
- **Claims-based scoring engine**: released for reproducible comparison

MAO-Bench's harness architecture borrows directly from MCP-Atlas's containerization approach.

---

## Gaps Relative to MAO-Bench

| MCP-Atlas | MAO-Bench Extension |
|-----------|---------------------|
| Single agent | Multi-agent orchestration |
| Single session | Multi-session (persistence) |
| Tools available throughout | Agent failure injection (robustness) |
| 3–6 tool calls | 10–100+ tool calls across 2–20 agents |
| No coordination overhead | Coordination overhead as primary metric |
| No memory management | Compaction fidelity, re-discovery overhead |
| No parallelism | Parallelism efficiency as primary metric |
| Single repo | Cross-repo and federated tasks |

---

## Citation

```bibtex
@misc{bandi2026mcpatlas,
  title  = {MCP-Atlas: A Large-Scale Benchmark for Tool-Use Competency with Real MCP Servers},
  author = {Chaithanya Bandi and others},
  year   = {2026},
  eprint = {2602.00933},
  archivePrefix = {arXiv}
}
```

---

## References

- [arXiv: 2602.00933](https://arxiv.org/abs/2602.00933)
- [HTML version](https://arxiv.org/html/2602.00933)
- [Cool Papers](https://papers.cool/arxiv/2602.00933)
