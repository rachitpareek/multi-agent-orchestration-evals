# MAO-Bench Metrics Specification

**Version**: 0.1.0
**Status**: Draft

This document is the normative definition of all metrics collected and reported by MAO-Bench. Every metric is defined precisely enough to be independently implemented and verified.

---

## Overview

MAO-Bench reports six metric dimensions. Each dimension produces one or more raw measurements and a normalized **dimension score** in `[0, 1]`. The overall **MAO Score** is the geometric mean of all six dimension scores.

```
MAO Score = (R × P × T × S × O × Q)^(1/6)

R = Robustness score
P = Persistence score
T = Token Efficiency score
S = Speed score
O = Topology/Coordination score
Q = Quality score
```

The geometric mean penalizes systems that excel on some dimensions at the expense of others — a system that is fast but unreliable should score lower than one that is balanced.

---

## 1. Robustness (R)

**What it measures**: How well the system maintains task progress under agent failure, tool errors, and adversarial conditions.

### 1.1 Task Completion Rate Under Failure (`tcr_k`)

For each adversarial task, `k` of `N` agents are killed at a random point during execution.

```
tcr_k = (tasks completed despite k failures) / (total adversarial tasks)
```

Reported for `k = 1, floor(N/2), N-1` separately. Dimension input uses `k=1`.

### 1.2 Graceful Degradation Score (`gds`)

Partial credit for tasks where the system makes progress before failing completely:

```
gds = mean(claims_satisfied_at_failure / total_claims)
      across all tasks where tcr_1 = 0
```

A system that completes 8/10 claims before one agent failure scores 0.8 on GDS, not 0.

### 1.3 Error Recovery Rate (`err`)

Fraction of tool errors (non-fatal) that the system successfully recovers from:

```
err = (tool_errors where agent retried and succeeded) /
      (total non-fatal tool errors)
```

Measured from telemetry logs. A tool error is "non-fatal" if the task can still complete afterward.

### 1.4 Merge Conflict Resolution Rate (`mcrr`)

For tasks involving parallel agents writing to the same files:

```
mcrr = (merge conflicts resolved correctly) / (total merge conflicts encountered)
```

A conflict is "resolved correctly" if the merged output passes the task's test oracle.

### Robustness Dimension Score

```
R = 0.4 * tcr_1 + 0.2 * gds + 0.2 * err + 0.2 * mcrr
```

---

## 2. Persistence (P)

**What it measures**: Whether the system maintains task continuity across session boundaries and context compaction events.

### 2.1 Multi-Session Task Completion Rate (`mstcr`)

For long-horizon tasks (tier: `long_horizon`), fraction completed to full oracle satisfaction:

```
mstcr = (long_horizon tasks fully completed) / (total long_horizon tasks)
```

Baseline comparison: fraction completed by systems _without_ Beads-style external memory.

### 2.2 Context Reconstruction Fidelity (`crf`)

At each session boundary, record the ground-truth task state (set of completed sub-tasks, files modified, decisions made). After session restart, measure how accurately the agent reconstructs this state from its memory system.

```
crf = mean(
  |recalled_state ∩ true_state| / |true_state|
  across all session boundaries
)
```

Recall: what fraction of true state the agent correctly remembers.
Precision analog: checked via hallucination detection (did the agent claim work it didn't do?).

### 2.3 Re-Discovery Overhead (`rdo`)

Tokens spent in a new session before the agent begins productive new work, expressed as a fraction of that session's total tokens:

```
rdo = mean(
  tokens_before_first_new_tool_call_or_edit /
  total_session_tokens
  across all sessions after the first
)
```

Lower is better. A system with perfect external memory should have `rdo ≈ 0` (immediately knows what to do). A system with no memory might spend 30–50% of tokens re-reading files already seen.

### 2.4 Dependency Graph Preservation (`dgp`)

After session restart, measure how accurately the agent reconstructs the task dependency graph (which tasks are done, which are blocked, which are ready):

```
dgp = |reconstructed_deps ∩ true_deps| / |true_deps|
```

Measured by comparing agent's `bd ready` output (or equivalent) against ground truth.

### Persistence Dimension Score

```
P = 0.35 * mstcr + 0.25 * crf + 0.25 * rdo_score + 0.15 * dgp

rdo_score = max(0, 1 - rdo * 5)   # 0% overhead → 1.0; 20%+ overhead → 0.0
```

---

## 3. Token Efficiency (T)

**What it measures**: How many tokens the system consumes per unit of useful work.

### 3.1 Tokens Per Task (`tpt`)

```
tpt = total_tokens_consumed / tasks_completed
```

`total_tokens` = sum of input + output tokens across all agents, all sessions, for the task. Normalized across task tiers (long-horizon tasks naturally use more tokens; normalize by task complexity tier).

### 3.2 Coordination Overhead Fraction (`cof`)

Fraction of tokens spent on coordination (agent-to-agent communication, issue updates, status checks) rather than productive work (file reads, code edits, test runs):

```
cof = coordination_tokens / total_tokens
```

Coordination tokens are identified by tool call type: `bd update`, `bd create`, `bd ready`, status polling calls, inter-agent message passing.

### 3.3 Redundant Read Coefficient (`rrc`)

```
rrc = (file reads of already-read files) / (total file reads)
```

A file is "already read" if the same agent (or another agent in the same session) read it within the past N tool calls. Lower is better.

### 3.4 Compaction Ratio (`cr`)

```
cr = context_size_before_compaction / context_size_after_compaction
```

Higher is better (more compression). Measured at each compaction event. Averaged across all compaction events for the task.

### Token Efficiency Dimension Score

```
T = normalize(1 / tpt) * 0.35   # lower tpt → higher score
  + (1 - cof) * 0.30            # lower coordination overhead → higher score
  + (1 - rrc) * 0.20            # lower redundant reads → higher score
  + normalize(cr) * 0.15        # higher compaction → higher score
```

All `normalize()` calls use min-max normalization across all evaluated systems.

---

## 4. Speed (S)

**What it measures**: How quickly the system produces correct results.

### 4.1 Wall-Clock Time to Completion (`wctc`)

```
wctc = task_end_timestamp - task_start_timestamp   [seconds]
```

Measured from when the task prompt is injected to when the oracle first returns a passing score.

### 4.2 Agent-Hours Consumed (`ahc`)

```
ahc = sum(agent_active_seconds) / 3600   [agent-hours]
```

`agent_active_seconds` = time each agent process spends in an active state (not waiting for dependencies or user input). This distinguishes compute efficiency from calendar efficiency.

### 4.3 Parallelism Efficiency (`pe`)

```
pe = ahc_single_agent_baseline / ahc_multi_agent
     capped at min(actual_agent_count, theoretical_speedup)
```

A perfect parallel system running 4 agents should take ¼ the agent-hours of a single agent. `pe = 1.0` means perfect parallelism. `pe < 1.0` means coordination overhead is eating gains. `pe > 1.0` would indicate synergies (unlikely).

### 4.4 Time to First Deliverable (`ttfd`)

```
ttfd = first_passing_test_or_merged_pr_timestamp - task_start_timestamp
```

A system that produces fast intermediate results even if the full task takes longer should score well on TTFD. Rewards incremental delivery patterns.

### Speed Dimension Score

```
S = normalize(1 / wctc) * 0.40   # lower wctc → higher score
  + normalize(1 / ahc) * 0.25    # lower ahc → higher score
  + pe * 0.20                    # higher parallelism efficiency → higher score
  + normalize(1 / ttfd) * 0.15   # lower ttfd → higher score
```

---

## 5. Topology / Coordination Quality (O)

**What it measures**: Whether the system uses agents efficiently and routes work to the right agents.

### 5.1 Fan-Out Depth (`fod`)

```
fod = max depth of the agent spawning tree
```

Measured from telemetry (who spawned whom). Depth 0 = single agent. Depth 1 = orchestrator + workers. Depth 2 = orchestrator + sub-orchestrators + workers. Reported as a descriptive statistic, not scored.

### 5.2 Bottleneck Agent Score (`bas`)

Identify the bottleneck agent: the one with the highest centrality in the coordination graph. Score measures how much this agent constrains the whole system:

```
bas = 1 - (bottleneck_agent_wait_time / total_wall_time)
```

Higher is better. `bas = 1.0` means no agent is a bottleneck. `bas = 0.0` means the whole run waits for one agent.

### 5.3 Optimal Agent Count Efficiency (`oace`)

Run each task with `{1, 2, 4, 8, 16}` agents (when the tier supports it). Find the optimal count `n*` (maximizes quality / agent-hours). Report:

```
oace = quality_at_n* / (n* * quality_at_1)   [normalized]
```

High `oace` means the system finds good parallelism. Low `oace` means coordination costs dominate at higher agent counts.

### 5.4 Duplicate Work Rate (`dwr`)

```
dwr = (tasks claimed by 2+ agents) / (total tasks in the run)
```

A correct atomic claim protocol should produce `dwr ≈ 0`. Any `dwr > 0` indicates a race condition in the orchestration system's work assignment.

### Topology Dimension Score

```
O = bas * 0.35
  + normalize(oace) * 0.35
  + (1 - min(dwr * 10, 1.0)) * 0.30   # DWR > 10% → score 0
```

---

## 6. Quality (Q)

**What it measures**: Correctness and completeness of the agent's outputs.

### 6.1 Claims Satisfaction Rate (`csr`)

The primary quality metric. For each task, score = claims satisfied / total claims (weighted by claim weights from the task schema):

```
csr = sum(claim_weight_i * claim_passed_i) / sum(claim_weight_i)
```

Averaged across all tasks in the evaluation suite.

### 6.2 Test Pass Rate (`tpr`)

```
tpr = (tests passing in oracle test suite after agent changes) /
      (total tests in oracle test suite)
```

Averaged across all tasks with a test suite.

### 6.3 Static Analysis Score (`sas`)

Run ruff/flake8/eslint/etc. on all agent-modified files. Score = 1 - (new violations introduced / max_violations). Penalizes agents that produce working-but-dirty code.

```
sas = max(0, 1 - new_lint_violations / 100)
```

### 6.4 Regression Rate (`rr`)

```
rr = (tests that were passing before agent changes and fail after) /
     (tests passing before agent changes)
```

Lower is better. `rr = 0` means the agent introduced no regressions.

### Quality Dimension Score

```
Q = csr * 0.45
  + tpr * 0.30
  + sas * 0.10
  + (1 - rr) * 0.15
```

---

## Composite MAO Score

```
MAO = (R × P × T × S × O × Q)^(1/6)
```

All dimension scores are already in `[0, 1]`. The geometric mean is used because:
1. It penalizes imbalanced profiles (a system that scores 1.0 on 5 dimensions but 0.1 on one gets MAO ≈ 0.55, not 0.92)
2. It is scale-invariant (each dimension contributes equally regardless of variance)
3. It is standard in multi-criteria benchmarks (e.g., SWE-bench Lite composite)

---

## Reporting Requirements

Every leaderboard submission MUST report:

1. Full score table (all 6 dimensions + composite MAO score)
2. Per-tier breakdown (single_agent, parallel_multi, sequential_multi, long_horizon, adversarial, federated)
3. Per-metric raw values (not just normalized scores)
4. System configuration (model, orchestration framework, agent count, version)
5. Run metadata (date, harness version, environment)
6. Confidence intervals (bootstrap 95% CI over all tasks)

Submissions that report only the composite MAO score are invalid.

---

## Stability and Versioning

- Metric definitions are versioned with the benchmark (SemVer)
- Breaking metric changes (new formula, new weights) increment the major version
- Scores from different major versions are NOT comparable
- Minor versions (new metrics added, weights rebalanced with justification) include a crosswalk table for historical comparison
