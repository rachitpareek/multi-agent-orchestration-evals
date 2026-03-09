# Context Management & Token Efficiency — Research Summary

A synthesis of research on LLM agent context management, compaction, and long-horizon task efficiency, directly informing MAO-Bench's persistence and token efficiency metric suite.

---

## The Fundamental Problem

As agents run longer, context windows fill. The naive fix — larger context windows — doesn't scale: production studies show that models struggle to effectively use information beyond a certain point even within their nominal window. The real solution is **active context management**.

Key insight: *most tokens in an agent's context are not useful for the current step*. Prior observations, completed sub-tasks, intermediate reasoning — all of this occupies space that could be used for new information. The challenge is deciding what to keep.

---

## Technique 1: ACON — Adaptive Context Compression

**Paper**: [arXiv 2510.00615](https://arxiv.org/html/2510.00615v1)

ACON (Agent Context Optimization) is a unified framework for **task-specific, adaptive compression**. Unlike generic summarization, ACON generates task-specific compression guidelines based on which signal types matter for that particular task:

- Factual history (what did we find?)
- Action-outcome relationships (what worked? what failed?)
- Environment state (what is currently true?)
- Success preconditions (what needs to be true to proceed?)
- Future decision cues (what decisions are coming up?)

**Results**:
- 26–54% reduction in peak token usage
- Small models (with ACON) match large models (without ACON) on complex agent tasks
- Validated on AppWorld, OfficeBench, Multi-objective QA

**MAO-Bench implication**: Token efficiency metric must distinguish between raw token count and _useful_ token count. ACON's compression ratio is a useful baseline for comparing orchestration systems' built-in context management.

---

## Technique 2: Context-Folding

**Paper**: [arXiv 2510.11967](https://arxiv.org/abs/2510.11967)

Context-Folding gives agents two special actions:
- `branch(description, prompt)`: start a sub-trajectory for a localized sub-task
- `return(message)`: complete the branch, folding intermediate steps into a concise outcome summary

The key insight: summarization should happen at **sub-task boundaries** (when the utility of intermediate steps is fully realized), not on a fixed schedule.

**Training**: FoldGRPO — Group Relative Policy Optimization with dynamic folded contexts and token-level process rewards.

**Results**: A 32K active-window Folding Agent matches a ReAct agent with 327K passive context. Effective compression ratio: ~10x.

**MAO-Bench implication**: Long-horizon tasks should be instrumented to detect whether systems apply sub-task-boundary compaction (like Context-Folding or Beads's PreCompact hook) vs. naive truncation.

---

## Technique 3: Compaction vs. Summarization

**Source**: Manus production analysis; [Morph comparison](https://www.morphllm.com/compaction-vs-summarization)

Two fundamentally different approaches:

| | Compaction | Summarization |
|---|---|---|
| Method | Delete tokens from original text | LLM rewrites history as condensed prose |
| Lossiness | Lossless (survivors are verbatim) | Lossy (paraphrasing, potential hallucination) |
| Reversibility | Reversible (original recoverable) | Irreversible |
| Compression ratio | Lower | Higher |
| Latency | Low | High (requires LLM call) |

**Production recommendation (Manus)**: Stage compaction before summarization. Compact the oldest 50% of tool calls first; only summarize when multiple compaction rounds yield diminishing returns. Always preserve the last N tool calls in full to maintain behavioral continuity.

**Claude Code's compaction**: Generates structured summaries of 7,000–12,000 characters with sections for: analysis completed, files modified, key decisions, pending tasks. Designed to be comprehensive enough that the agent can immediately resume work after a context reset.

**MAO-Bench implication**: Compaction ratio metric = (original context size) / (post-compaction context size). Compaction fidelity metric = (tasks the agent can correctly resume after compaction) / (tasks attempted after compaction).

---

## Technique 4: Observation Masking

**Source**: [JetBrains Research](https://blog.jetbrains.com/research/2025/12/efficient-context-management/)

In software engineering agent trajectories, each turn is heavily weighted toward **observations** (tool outputs, file contents) over **actions** (agent reasoning, decisions). Observation masking:
- Hides old tool outputs from context
- Preserves full action and reasoning history

This is efficient because: (a) reasoning chains are generally short, (b) old tool outputs can be re-fetched if needed, (c) the reasoning trace is the most valuable part for task continuity.

**Tested on**: SWE-bench Verified (500 instances), Qwen3 (32B) and Gemini 2.5 Flash (480B).

**MAO-Bench implication**: For software engineering tasks, orchestration systems that mask old observations before compaction should achieve better token efficiency without sacrificing task quality.

---

## Beads's Approach

Beads (the MAO-Bench reference persistence system) implements a pragmatic hybrid:
1. **Structured external memory**: completed and closed issues are stored in Dolt, not the agent's context
2. **Semantic compaction**: old issues are summarized into compact representations, not deleted
3. **Context budget management**: `bd ready --json` returns only the relevant work items for the current session (~1-2k tokens), not the full graph
4. **PreCompact hook**: before Claude Code compacts, Beads checkpoints the current task state to the DB so it can be recovered cleanly

This is an **external memory** approach rather than an in-context compression approach. The benchmark should measure both approaches.

---

## Key Metrics Derived from this Literature

| Metric | Definition | Source Idea |
|--------|-----------|-------------|
| `peak_tokens` | Max context length during task execution | ACON |
| `compaction_ratio` | Original size / post-compaction size | Manus/Morph |
| `compaction_fidelity` | Task resumption success rate post-compaction | Beads PreCompact |
| `re_discovery_overhead` | Tokens spent re-reading already-read content | 50 First Dates problem |
| `coordination_overhead_fraction` | Tokens on coordination / total tokens | MARBLE |
| `context_reconstruction_fidelity` | Correctness of recalled state vs. ground truth | ACON/Context-Folding |
| `useful_token_ratio` | Tokens contributing to correct decisions / total | ACON |

---

## References

- [ACON: Optimizing Context Compression (arXiv 2510.00615)](https://arxiv.org/html/2510.00615v1)
- [Context-Folding (arXiv 2510.11967)](https://arxiv.org/abs/2510.11967)
- [JetBrains: Smarter Context Management](https://blog.jetbrains.com/research/2025/12/efficient-context-management/)
- [Morph: Compaction vs. Summarization](https://www.morphllm.com/compaction-vs-summarization)
- [Fundamentals of Compaction in LLMs (Medium)](https://kargarisaac.medium.com/the-fundamentals-of-context-management-and-compaction-in-llms-171ea31741a2)
