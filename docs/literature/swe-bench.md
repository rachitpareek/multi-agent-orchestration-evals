# SWE-bench — Research Summary

**Paper**: ["SWE-bench: Can Language Models Resolve Real-World GitHub Issues?"](https://arxiv.org/pdf/2310.06770), ICLR 2024
**Repo**: https://github.com/SWE-bench/SWE-bench

---

## Overview

SWE-bench is the canonical benchmark for evaluating LLMs on real-world software engineering tasks. Tasks are sourced from GitHub issue/PR pairs across 12 Python repositories, requiring agents to edit codebases to resolve issues using execution-based validation (hidden test suites).

It is the most cited coding-agent benchmark and the primary reference point for "can LLMs write real code?" research.

---

## Task Format

Each task provides:
- **Issue description** (avg 195 words — short)
- **Repository snapshot** at issue-filing time (avg 438K lines — large)
- No access to the hidden gold patch or test files

The agent must:
1. Navigate the codebase to understand context
2. Identify root cause
3. Produce a patch (unified diff format)
4. Pass all associated tests

### Evaluation

```
patch -p1 < agent.patch  →  run test suite  →  pass/fail
```

Metric: **resolve rate** (% of instances where all hidden tests pass after applying the agent's patch). Typically reported as pass@1.

Since June 2024: fully containerized via Docker for reproducibility.

---

## SWE-bench Verified (2024)

A human-validated 500-task subset, screened by 93 software developers to remove:
- Tasks with overly specific/unrelated unit tests
- Underspecified issue descriptions
- Difficult environment setups

SWE-bench Verified has superseded the original for most evaluation purposes.

---

## Performance Trajectory

| Era | Best Resolve Rate | Context |
|-----|------------------|---------|
| Original (2023) | ~1.96% | Claude/GPT-4 direct |
| 2024 | ~40% | Scaffolded agents (SWE-agent, Devin) |
| 2025 | ~75% | Best system (TRAE/ByteDance); Anthropic ~73% |

The rapid saturation of SWE-bench is itself a data point: once a benchmark crosses ~60–70%, it stops discriminating well between systems. MAO-Bench is designed to avoid early saturation by adding dimensions (orchestration, persistence, robustness) where current systems are far from ceiling.

---

## Key Limitations

### 1. Single-agent, single-session
SWE-bench measures one agent completing one task in one session. It cannot measure:
- How a multi-agent system decomposes and parallelizes work
- Session continuity after context compaction
- Coordination overhead between agents
- Agent failure recovery

### 2. Binary pass/fail
An agent that fixes 9 of 10 bugs in a complex PR gets the same score as an agent that fixes 0. MAO-Bench's claims-based rubric awards partial credit.

### 3. Short tasks
SWE-bench tasks are completable in one context window. Real engineering work spans days/weeks. MAO-Bench's long-horizon tier directly targets this gap.

### 4. Data contamination
SWE-bench instances predate many model training cutoffs. The SWE-bench-Live variant (1,319 tasks from real GitHub issues since 2024) addresses this; MAO-Bench adopts similar freshness controls for its dataset.

### 5. Solution leakage
Studies find up to 54% relative overestimation on SWE-bench Verified due to solution hints in issue descriptions. MAO-Bench task prompts are reviewed for information leakage.

---

## What MAO-Bench Takes from SWE-bench

- **Containerized evaluation harness** (Docker, hermetic)
- **Hidden test oracle** (tests not visible to agent)
- **Real code repositories** as task workspaces
- **Pass@1 as quality baseline** within each task tier
- **Partial overlap**: 100 MAO-Bench single-agent tasks are drawn from SWE-bench Verified to allow direct comparison of single-agent vs. multi-agent performance on the same underlying problems

---

## Citation

```bibtex
@inproceedings{jimenez2024swebench,
  title     = {{SWE}-bench: Can Language Models Resolve Real-World {GitHub} Issues?},
  author    = {Carlos E. Jiménez and others},
  booktitle = {International Conference on Learning Representations},
  year      = {2024},
  url       = {https://arxiv.org/abs/2310.06770}
}
```

---

## References

- [arXiv: 2310.06770](https://arxiv.org/pdf/2310.06770)
- [SWE-bench website](https://www.swebench.com/original.html)
- [SWE-bench GitHub](https://github.com/SWE-bench/SWE-bench)
- [SWE-bench Verified announcement (OpenAI)](https://openai.com/index/introducing-swe-bench-verified/)
