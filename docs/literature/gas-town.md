# Gas Town — Research Summary

**Source**: Steve Yegge, ["Welcome to Gas Town"](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04), Jan 2026
**Repo**: https://github.com/steveyegge/gastown
**Community**: https://gastownhall.ai

---

## Overview

Gas Town is Steve Yegge's open-source multi-agent orchestration framework for managing 20–50 parallel AI coding agents (primarily Claude Code) through a structured hierarchy of roles, workflows, and persistent state. Built in Go (~189k LOC) on top of the Beads issue-tracking system, it represents the most mature public example of production-grade agent orchestration at the time of this benchmark's design.

Yegge describes it as "Kubernetes for AI coding agents." In two months post-launch: 2,400 submitted PRs, 1,500 merged, 450+ unique contributors.

---

## Seven Agent Roles

| Role | Type | Function |
|------|------|----------|
| **Mayor** | Persistent | Primary human interface; breaks down work, issues slings |
| **Polecats** | Ephemeral | Workers; execute tasks, produce merge requests |
| **Refinery** | Persistent | Manages the merge queue; serializes parallel merges |
| **Witness** | Persistent | Monitors Polecat health; escalates stuck agents |
| **Deacon** | Persistent | Runs patrol loops; maintenance and cleanup |
| **Dogs** | Persistent | Infrastructure maintenance |
| **Crew** | Persistent | Collaborative design work; reusable across tasks |

**Hierarchy**: Human → Mayor → Crew/Polecats, with Witness supervising Polecats and Refinery, and Deacon managing Dogs.

---

## Work Primitives

### Beads (Issue Tracker)
All state — agent identities, work assignments, orchestration metadata — persists in Beads (git-backed JSONL + Dolt). Sessions are ephemeral cattle; agents are persistent identities with continuous memory.

### Convoys
The work-order unit. A Convoy wraps a set of related work items into a tracked delivery unit. `gt sling` is the fundamental work-dispatch primitive: Mayor files a bead and slings it to a Polecat.

### Rigs
Project workspaces. Rig-level workers (Refinery, Witness, Polecats, Crew) can work cross-rig via `gt worktree`, but normally operate within a single project.

### MEOW (Molecular Expression of Work)
The workflow stack enabling persistent, composable, crash-recoverable orchestration. Data hierarchy:

```
Beads → Epics → Molecules → Protomolecules → Formulas (TOML)
```

### Wisps (Ephemeral Beads)
Short-lived, in-memory beads not persisted to Git. All patrol agents create wisp molecules per run. At end of run, wisps are "burned" or squashed into a single-line summary committed to Git. This is how Gas Town manages the signal-to-noise problem at scale.

---

## Observability

- **Agent Tree**: Hierarchical view of all agents grouped by rig and role
- **Convoy Panel**: In-progress and recently-landed convoys
- **Event Stream**: Chronological feed of creates, completions, slings, nudges
- **Problems View**: Surfaces agents needing human intervention by analyzing structured Beads data

At 20–50+ agents, the problems view is critical for spotting stuck agents that would otherwise be invisible in the activity stream.

---

## The Merge Queue Problem

A recurring pain point in multi-agent systems: when 20+ agents each produce PRs simultaneously, naive merge order destroys consistency. Gas Town's Refinery solves this with:

1. A serialized merge queue (one merge at a time)
2. Pre-flight cleanup steps before processing
3. Post-flight hand-off steps when recycling sessions
4. Automatic conflict detection and re-sling on conflict

This is one of the most important design decisions Gas Town makes — and a primary dimension our benchmark must evaluate.

---

## Implications for MAO-Bench

| Gas Town Pattern | MAO-Bench Metric |
|-----------------|-----------------|
| Polecat failure detection (Witness) | Robustness — error recovery rate |
| Wisp burn/summarization | Persistence — compaction ratio, context reconstruction fidelity |
| Merge queue management | Robustness — merge conflict resolution correctness |
| Convoy tracking across sessions | Persistence — multi-session task completion rate |
| `gt sling` overhead | Token efficiency — coordination overhead fraction |
| Agent Tree depth | Topology — fan-out depth, bottleneck agent detection |
| Problems view escalation rate | Robustness — escalation frequency as failure signal |

Gas Town serves as the **primary "state of the art" multi-agent baseline** in MAO-Bench. Its 2,400-PR track record makes it the strongest production reference point available.

---

## References

- [Welcome to Gas Town (Medium)](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04)
- [Gas Town GitHub repo](https://github.com/steveyegge/gastown)
- [Gas Town Hall community](https://gastownhall.ai)
- [maggieappleton.com/gastown — architecture deep dive](https://maggieappleton.com/gastown)
- [Cloud Native Now — "What Kubernetes for AI Coding Agents Actually Looks Like"](https://cloudnativenow.com/features/gas-town-what-kubernetes-for-ai-coding-agents-actually-looks-like/)
