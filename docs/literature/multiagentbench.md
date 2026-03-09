# MultiAgentBench (MARBLE) — Research Summary

**Paper**: ["MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents"](https://arxiv.org/abs/2503.01935), ACL 2025
**Repo**: https://github.com/ulab-uiuc/MARBLE
**ACL Anthology**: [2025.acl-long.421](https://aclanthology.org/2025.acl-long.421/)

---

## Overview

MultiAgentBench (MARBLE) is the closest academic benchmark to MAO-Bench in scope. It evaluates LLM-based multi-agent systems across diverse interactive scenarios, measuring both **collaborative** (mutual-goal) and **competitive** (conflicting-goal) behaviors.

Unlike MAO-Bench, MARBLE focuses on abstract multi-agent scenarios (research, coding, social deduction games like Werewolf) rather than real-world software engineering orchestration tasks.

---

## Task Design

Tasks span:
- **Collaborative scenarios**: research synthesis, code co-development
- **Competitive scenarios**: resource allocation, social deduction (Werewolf)
- **Mixed scenarios**: negotiation with partially-aligned goals

Tasks are evaluated using **milestone-based KPIs** — intermediate goals within a task that signal progress. This partial-credit approach is directly analogous to MAO-Bench's claims-based rubric.

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **Task Score (TS)** | Fraction of task milestones completed |
| **Coordination Score** | Quality of agent-to-agent communication and synchronization |
| **Planning Score** | Quality of agent task decomposition and sequencing |
| **Competition Score** | Performance in conflicting-goal scenarios |
| **Communication Score** | Efficiency and clarity of inter-agent messages |

These metrics are additive; no composite score is computed. MAO-Bench adopts a normalized geometric mean composite to enable single-number rankings.

---

## Topology Findings

MARBLE tests four coordination topologies: **star, chain, tree, graph**. Key results:
- **Graph/mesh topology** consistently yields the best task scores
- **Tree topology** is the least effective (bottleneck at root)
- Performance generally improves with more iterations up to a threshold, then plateaus or drops
- Agent count increases total task score up to a saturation point, after which per-agent contribution falls

**MAO-Bench implication**: topology testing is not optional — we must test all four topologies for each benchmark system and report the optimal agent count curve.

---

## Model Performance

| Model | Scenario | Task Score |
|-------|----------|-----------|
| GPT-4o-mini | Research | 84.13% |
| GPT-4o-mini | Coding | 65.10% |
| Meta-Llama-3.3-70B | Werewolf | High coordination but low task |

Key finding: **a model's task performance and its coordination performance are not correlated**. A model that is excellent at task execution may be poor at coordination, and vice versa. This validates MAO-Bench's decision to measure these dimensions independently.

---

## Planning Strategy: Cognitive Self-Evolving Planning

MARBLE's best planning strategy:
1. Planner generates expected outcomes and sub-milestones
2. Agents execute, log actual outcomes
3. Planner compares expected vs. actual, updates an experience memory
4. Future iterations retrieve from experience memory via RAG

This yields ~3% coordination score improvement over vanilla planning. MAO-Bench should test whether this pattern holds in software engineering contexts.

---

## Emergent Social Behaviors

MARBLE surfaces behaviors that only appear in multi-agent settings:
- **Strategic information withholding**: agents in social deduction games delay disclosures, sometimes leading to task failure
- **Trust polarization**: internal distrust among collaborators is exploitable by adversaries
- **Coalition formation**: agents spontaneously form subgroups, sometimes misaligned with task goals

For MAO-Bench's adversarial tier, these findings motivate tasks that test whether orchestration systems are robust to misaligned sub-agents.

---

## Gaps Relative to MAO-Bench

| MARBLE | MAO-Bench Extension |
|--------|---------------------|
| Abstract/game scenarios | Real software engineering repos |
| Single-session only | Multi-session (persistence) |
| No failure injection | Robustness tier with injected failures |
| No token tracking | Token efficiency as primary metric |
| No tool use (MCP) | MCP server integration |
| No persistence mechanism | Beads-style memory evaluation |
| No cross-repo tasks | Federated task tier |

MARBLE is complementary, not competing. It tests coordination dynamics in controlled environments; MAO-Bench tests orchestration quality in real engineering workflows.

---

## What MAO-Bench Takes from MARBLE

- **Milestone-based partial credit** (extended into claims-based rubrics)
- **Topology as an independent variable** (test all four topologies per system)
- **Separate coordination and task quality metrics** (don't conflate them)
- **Agent count saturation curve** (plot performance vs. N agents)

---

## Citation

```bibtex
@inproceedings{marble2025,
  title     = {MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents},
  booktitle = {Proceedings of the 63rd Annual Meeting of the ACL},
  pages     = {8580--8622},
  year      = {2025},
  url       = {https://arxiv.org/abs/2503.01935}
}
```

---

## References

- [arXiv: 2503.01935](https://arxiv.org/abs/2503.01935)
- [MARBLE GitHub](https://github.com/ulab-uiuc/MARBLE)
- [ACL Anthology](https://aclanthology.org/2025.acl-long.421/)
