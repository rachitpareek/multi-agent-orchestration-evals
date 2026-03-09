# Beads — Research Summary

**Source**: Steve Yegge, ["Introducing Beads: A Coding Agent Memory System"](https://steve-yegge.medium.com/introducing-beads-a-coding-agent-memory-system-637d7d92514a), Oct 2025
**Repo**: https://github.com/steveyegge/beads
**CLI**: `bd` (installable via `brew install beads`)

---

## The Core Problem: 50 First Dates

All LLM agents have no memory between sessions. Sessions typically last ~10 minutes before context compaction. The agent wakes up each session knowing only what it can find on disk — like the movie *Memento*, or *50 First Dates*.

Real-world engineering workflows are long. A single feature commonly requires:
- Multiple rounds of testing and debugging
- Code review and iteration
- Documentation
- Integration with other in-flight work

These tasks span many sessions. Without an external memory system, each session re-discovers what was done before, re-reads files already read, re-makes decisions already made. This is the "50 First Dates" failure mode — and it's the primary driver of the persistence metric in MAO-Bench.

---

## What Beads Is

Beads is a **lightweight, git-backed, graph-oriented issue tracker** built specifically as external memory for coding agents. The `bd` CLI stores tasks as structured JSONL files in `.beads/`, committed to git, powered by a version-controlled Dolt database for conflict-free merges and branching.

Key design values:
- **Context efficiency**: Agent wakes up, runs `bd ready --json`, gets a clean list of unblocked prioritized tasks in ~1-2k tokens
- **Dependency-first**: `blocks`, `depends_on`, `relates_to`, `replies_to`, parent-child hierarchies are first-class
- **Multi-agent safe**: `bd update --claim` atomically sets assignee + status — no two agents grab the same task
- **Compaction-aware**: Closed work is semantically compacted (summarized) to avoid bloating context
- **Git-native**: Everything in `.beads/issues.jsonl`, committed, mergeable

---

## Architecture

```
.beads/
├── dolt/               # Dolt DB (version-controlled relational store)
├── config.yaml         # Project config
├── metadata.json       # Project metadata
├── interactions.jsonl  # Agent interaction log
└── hooks/              # Pre/post hooks (SessionStart, PreCompact, etc.)
```

### Dolt Backend
Beads uses [Dolt](https://github.com/dolthub/dolt) — "Git for data" — as its storage engine. This gives:
- Cell-level merge conflict resolution (agents working in parallel don't trash each other's edits)
- Full version history on all issue data
- Branch/merge for experimental work streams
- DoltHub sync for federated access (The Wasteland)

### JSONL Export
All issues are exported to `.beads/issues.jsonl` after changes (5s debounce). This means the full issue graph is git-diffable, grep-able, and importable on `git pull` — making it safe across team repos.

---

## Issue Type Hierarchy

| Type | Purpose |
|------|---------|
| `epic` | Large feature; parent of tasks |
| `task` | Atomic work item |
| `bug` | Defect |
| `feature` | New capability |
| `chore` | Maintenance |
| `decision` | Architecture decision record (ADR) |
| `event` | Structured event log entry |
| `agent` | Registered agent identity |

### Wisps (Ephemeral)
Short-lived beads used by patrol agents. Not written to JSONL/git. Burned or squashed at end of run. Gas Town uses wisps for all patrol agent molecules.

---

## Multi-Agent Protocol

```bash
# Agent wakes up, sees what's ready
bd ready --json

# Atomically claim a task (prevents races between parallel agents)
bd update bd-42 --claim

# File discovered work
bd create "Found regression in login flow" \
  --type bug -p 1 \
  --deps "discovered-from:bd-42"

# Complete
bd close bd-42 --reason "Fixed and tested"
```

The atomic claim protocol is the multi-agent coordination primitive. It's modeled on test-and-set: `--claim` sets `assignee = current_agent` and `status = in_progress` in a single DB transaction.

---

## Claude Code Integration

`bd setup claude` installs two hooks into `~/.claude/settings.json`:
- **SessionStart**: Agent loads beads context on session start, sees ready tasks
- **PreCompact**: Agent checkpoints task state before context compaction

This makes Claude Code agents automatically persistent-memory-capable without any prompt engineering.

---

## Implications for MAO-Bench

The Beads protocol directly defines our persistence metric suite:

| Beads Concept | MAO-Bench Metric |
|--------------|-----------------|
| `bd ready` latency | Context reconstruction overhead (tokens to first productive action) |
| Atomic `--claim` | Coordination correctness (no duplicate work) |
| Session boundary | Multi-session task completion rate measurement point |
| Compaction fidelity | Context reconstruction fidelity score |
| `discovered-from` dependency | Work discovery efficiency |
| Wisp burn/squash | Compaction ratio |

**Every long-horizon task in MAO-Bench should be evaluated against a Beads-instrumented agent** to produce persistence metrics, since Beads is the reference implementation of the session-memory solution we're evaluating against.

---

## References

- [Introducing Beads (Medium)](https://steve-yegge.medium.com/introducing-beads-a-coding-agent-memory-system-637d7d92514a)
- [steveyegge/beads GitHub](https://github.com/steveyegge/beads)
- [Beads on bruton.ai](https://bruton.ai/blog/ai-trends/beads-bd-missing-upgrade-your-ai-coding-agent-needs-2026)
- [Metaist summary](https://metaist.com/blog/2025/12/introducing-beads-a-coding-agent-memory-system.html)
