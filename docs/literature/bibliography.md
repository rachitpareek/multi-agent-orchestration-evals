# Annotated Bibliography

All sources used in the design of MAO-Bench, organized by category.

---

## Multi-Agent Orchestration Systems

### Gas Town
- **Yegge, S.** (2026, Jan). *Welcome to Gas Town*. Medium.
  https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04
  - **Summary**: Introduces Gas Town, a multi-agent orchestration framework for 20–50 parallel Claude Code agents. Defines the seven roles (Mayor, Polecats, Refinery, Witness, Deacon, Dogs, Crew), the MEOW workflow stack, and the Convoy/Wisp work primitives. Reports 2,400 PRs in two months.
  - **Relevance**: Primary real-world multi-agent orchestration baseline. Most of our robustness and topology metrics are grounded in problems Gas Town has had to solve (merge queue, agent health monitoring, context compaction).

### The Wasteland
- **Yegge, S.** (2026, Mar). *Welcome to the Wasteland: A Thousand Gas Towns*. Medium.
  https://steve-yegge.medium.com/welcome-to-the-wasteland-a-thousand-gas-towns-a5eb9bc8dc1f
  - **Summary**: Describes the federated layer on top of Gas Town — a global Wanted Board, stamp-based reputation system, trust levels (registered/contributor/maintainer), and Dolt-backed federation. Introduces gamified character sheets and leaderboards.
  - **Relevance**: Motivates the federated task tier in MAO-Bench (25 tasks). Defines cross-organization trust and reputation as evaluation dimensions.

### Beads
- **Yegge, S.** (2025, Oct). *Introducing Beads: A Coding Agent Memory System*. Medium.
  https://steve-yegge.medium.com/introducing-beads-a-coding-agent-memory-system-637d7d92514a
  - **Summary**: Introduces the `bd` CLI — a git-backed, Dolt-powered, graph-oriented issue tracker as external agent memory. Solves the "50 First Dates" problem of stateless agents. Features atomic claim protocol, dependency graph, compaction, and Claude Code integration via hooks.
  - **Relevance**: Defines the persistence metric suite (multi-session completion, context reconstruction fidelity, re-discovery overhead). MAO-Bench uses Beads as the reference persistence implementation.

---

## Tool-Use Benchmarks

### MCP-Atlas
- **Bandi, C., et al.** (2026). *MCP-Atlas: A Large-Scale Benchmark for Tool-Use Competency with Real MCP Servers*. arXiv:2602.00933.
  https://arxiv.org/abs/2602.00933
  - **Summary**: 36 real MCP servers, 220 tools, 1,000 tasks requiring 3–6 tool calls. Claims-based rubric with partial credit. Claude Opus 4.5 achieves 62.3%. Containerized harness + 500-task public subset released.
  - **Relevance**: Closest methodological predecessor to MAO-Bench. We adopt its claims rubric, containerized evaluation approach, and "no tool names in prompts" design. MAO-Bench extends to multi-agent, multi-session settings.

### MCP-AgentBench
- **[Various]** (2025). *MCP-AgentBench: Evaluating Real-World Language Agent Performance with MCP-Mediated Tools*. arXiv:2509.09734.
  https://arxiv.org/abs/2509.09734
  - **Summary**: Evaluates agents on complex multi-server tasks. Assesses cross-server composition, parameter accuracy, and multi-step planning.
  - **Relevance**: Secondary tool-use reference; broader than MCP-Atlas in server count, less rigorous in evaluation protocol.

---

## Code Task Benchmarks

### SWE-bench
- **Jiménez, C. E., et al.** (2024). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR 2024. arXiv:2310.06770.
  https://arxiv.org/pdf/2310.06770
  - **Summary**: 2,294 GitHub issue/PR pairs from 12 Python repos. Hidden test-suite evaluation. Docker harness. Performance went from ~2% (2023) to ~75% (2025).
  - **Relevance**: Primary single-agent code task baseline. MAO-Bench single-agent tier draws from SWE-bench Verified for direct comparability. SWE-bench's saturation motivates the multi-agent extension.

### SWE-bench Verified
- **OpenAI + SWE-bench authors** (2024). *Introducing SWE-bench Verified*. OpenAI Blog.
  https://openai.com/index/introducing-swe-bench-verified/
  - **Summary**: 500-task human-validated subset. Screened by 93 developers to remove underspecified tasks and bad test cases.
  - **Relevance**: Source for MAO-Bench's single-agent baseline tier.

---

## Multi-Agent Benchmarks

### MultiAgentBench (MARBLE)
- **[ulab-uiuc]** (2025). *MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents*. ACL 2025. arXiv:2503.01935.
  https://arxiv.org/abs/2503.01935
  - **Summary**: Collaborative and competitive multi-agent scenarios (research, coding, Werewolf). Milestone-based KPIs. Tests star/chain/tree/graph topologies. Graph/mesh beats tree. Agent count saturation observed. GPT-4o-mini strong on task; coordination scores don't correlate with task scores.
  - **Relevance**: Primary multi-agent benchmark reference. MAO-Bench adopts its milestone/claims approach and topology testing methodology.

### AgentBench
- **[THUDM]** (2023). *AgentBench: A Comprehensive Benchmark to Evaluate LLMs as Agents*. ICLR 2024.
  https://github.com/THUDM/AgentBench
  - **Summary**: Multi-environment agent evaluation: web browsing, coding, operating systems, DB querying, knowledge graphs. Binary completion metrics.
  - **Relevance**: Established the "multi-environment single-agent" evaluation paradigm. MAO-Bench extends to multi-agent.

---

## Context Management & Long-Horizon Tasks

### ACON
- **Kang, M., et al.** (2025). *Acon: Optimizing Context Compression for Long-horizon LLM Agents*. arXiv:2510.00615.
  https://arxiv.org/html/2510.00615v1
  - **Summary**: Task-specific, adaptive context compression framework. 26–54% peak token reduction. Validated on AppWorld, OfficeBench.
  - **Relevance**: Informs compaction ratio and useful-token-ratio metrics.

### Context-Folding
- **[Various]** (2025). *Scaling Long-Horizon LLM Agent via Context-Folding*. arXiv:2510.11967.
  https://arxiv.org/abs/2510.11967
  - **Summary**: Branch/return actions for sub-task-boundary context folding. FoldGRPO training. 32K active = 327K passive performance.
  - **Relevance**: Informs how we measure context management efficiency; highlights that compaction timing matters.

### JetBrains Context Management Study
- **JetBrains Research** (2025). *Cutting Through the Noise: Smarter Context Management for LLM-Powered Agents*.
  https://blog.jetbrains.com/research/2025/12/efficient-context-management/
  - **Summary**: Empirical study of observation masking vs. LLM summarization on SWE-bench Verified. Observation masking is efficient and preserves reasoning continuity.
  - **Relevance**: Informs observation-masking as a metric dimension; provides SWE-bench baseline for comparison.

---

## Evaluation Methodology

### CLEAR Framework
- **[Various]** (2025). *CLEAR Framework: Cost, Latency, Efficiency, Assurance, Reliability*.
  - **Summary**: Five-dimensional evaluation framework for production AI agents. Argues accuracy-only evals miss what matters in deployment.
  - **Relevance**: Validates MAO-Bench's multi-dimensional metric approach. Production dimensions (latency, cost) map to our speed and token efficiency metrics.

### General Agent Evaluation Survey
- **[Various]** (2025). *Evaluation and Benchmarking of LLM Agents: A Survey*. arXiv:2507.21504.
  https://arxiv.org/html/2507.21504v1
  - **Summary**: Comprehensive survey of agent evaluation approaches across task types, environments, and metric families.
  - **Relevance**: Background and related work for the paper.

---

## Infrastructure References

### Dolt
- **DoltHub**. *Dolt: Git for Data*.
  https://github.com/dolthub/dolt
  - **Summary**: Git-semantics relational database with cell-level merge, branching, and DoltHub sync.
  - **Relevance**: Storage backend for Beads and Gas Town; also used in MAO-Bench for version-controlled results.

### OpenTelemetry
- **CNCF**. *OpenTelemetry SDK*.
  https://opentelemetry.io
  - **Summary**: Vendor-neutral observability framework (traces, metrics, logs).
  - **Relevance**: MAO-Bench telemetry pipeline is built on OTel for portability and community familiarity.
