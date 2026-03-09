# MAO-Bench Paper Outline

**Working Title**: "MAO-Bench: A Comprehensive Evaluation Framework for Multi-Agent LLM Orchestration"
**Target Venue**: COLM 2026 (primary); NeurIPS 2026 Datasets & Benchmarks Track (secondary)
**Status**: Outline / pre-draft

---

## Abstract (draft)

The rapid adoption of multi-agent LLM orchestration systems — exemplified by Gas Town's 2,400 merged PRs
in two months and Gartner's reported 1,445% surge in multi-agent system inquiries — has created
an urgent need for rigorous evaluation infrastructure. Existing benchmarks evaluate single-agent
code quality (SWE-bench), tool-use competency (MCP-Atlas), and multi-agent collaboration in
abstract settings (MultiAgentBench). None measure the dimensions that determine whether a
multi-agent orchestration system is production-ready: persistence across session boundaries,
robustness under agent failure, token efficiency of coordination overhead, and quality under
federated, cross-organization workflows.

We introduce MAO-Bench, the first evaluation framework specifically designed for multi-agent
LLM orchestration. MAO-Bench comprises 425 tasks across six tiers, a six-dimensional metric
suite (robustness, persistence, token efficiency, speed, topology, quality), and a composite
MAO score computed as the geometric mean of normalized dimension scores. We evaluate five
orchestration systems and find that [TBD after baselines]. Our benchmark, dataset, and
evaluation harness are publicly released.

---

## 1. Introduction

**Hook**: The inflection point. Gas Town exists. The Wasteland is live. 1,445% Gartner surge.
We are in the early innings of the multi-agent era. But we have no good evals.

**Problem statement**:
- SWE-bench: single agent, single session, binary pass/fail
- MCP-Atlas: single agent, tool-use only, no coordination overhead
- MultiAgentBench: abstract scenarios, no real code, no persistence, no token tracking
- None measure the things that actually break in production orchestration:
  the 50-First-Dates problem, merge queue storms, coordination token waste,
  agent dropout cascades, cross-org trust protocols

**Research questions**:
1. What dimensions best discriminate between orchestration systems?
2. How does orchestration overhead grow with agent count?
3. Does multi-agent orchestration actually improve quality/speed on real software tasks?
4. What failure modes are most common, and which systems recover best?

**Contributions**:
- MAO-Bench: 425 tasks across 6 tiers, including the first benchmark tier for long-horizon
  multi-session orchestration and federated cross-organization coordination
- Six-dimensional metric suite with formal definitions and normalized composite score
- Hermetic evaluation harness with pluggable adapter interface
- Baseline results for 5 orchestration systems across all tiers
- Public dataset, leaderboard, and harness code

---

## 2. Background and Motivation

### 2.1 The Multi-Agent Adoption Curve

Yegge's 8-stage model: from AI-assisted → AI-augmented → AI-orchestrated.
Gas Town as the current art. The Wasteland as the emerging federated layer.
Gartner data. Anthropic's stated priorities.

### 2.2 The Problems No Current Benchmark Measures

The 50-First-Dates problem (Beads; session memory).
The merge queue problem (Gas Town Refinery; parallel merge conflict storms).
The coordination tax (token efficiency; every `bd update` costs tokens).
The dropout cascade (adversarial; what happens when Agent C dies at 40%?).
The federation trust problem (Wasteland; cross-org stamp validation).

### 2.3 Why Now

All the systems that make this research possible are public and open-source as of Q1 2026.
Gas Town, Beads, The Wasteland, MCP-Atlas infrastructure. The moment is right.

---

## 3. Related Work

### 3.1 Single-Agent Code Benchmarks
SWE-bench, SWE-bench Verified, HumanEval, MBPP, CodeContests.
Limitation: single agent, single session, binary pass/fail.

### 3.2 Tool-Use Benchmarks
MCP-Atlas, MCP-AgentBench, WebArena, WorkArena.
Limitation: single agent, tool invocation only, no orchestration layer.

### 3.3 Multi-Agent Benchmarks
MultiAgentBench (MARBLE), AgentBench.
Limitation: abstract scenarios, no real code, no session persistence, no token tracking.

### 3.4 Context Management Research
ACON, Context-Folding, JetBrains SE study.
Relevance: informs persistence metrics.

### 3.5 Orchestration Systems as Baselines
Gas Town, CrewAI, AutoGen/AG2, LangGraph, OpenHands.

---

## 4. MAO-Bench Design

### 4.1 Design Principles
(1) Measure production-relevant dimensions. (2) Ground truth first, LLM-judge second.
(3) Reproducible by construction. (4) Partial credit, not binary. (5) Open extension.

### 4.2 Task Taxonomy
Six tiers, rationale for each. Task counts.

### 4.3 Metric Suite
All six dimensions defined formally. (Reference docs/METRICS.md.)

### 4.4 Scoring Rubric
Claims-based partial credit. Composite geometric mean. Why geometric mean.

### 4.5 Harness Architecture
Docker sandboxes. Adapter interface. Telemetry pipeline. Oracle design.

### 4.6 Dataset
Sources. Annotation protocol. Contamination controls. Train/test split.

---

## 5. Experiments

### 5.1 Evaluated Systems
Single Claude Code, Gas Town, CrewAI, AutoGen, LangGraph.
Configuration details for each. Fair comparison methodology.

### 5.2 Main Results
Full dimension-by-dimension table. Per-tier table. Composite rankings.

### 5.3 Key Findings
(Placeholder — fill after baselines run.)

### 5.4 Ablations
What if we remove persistence metrics? How do scores change as agent count varies?
Which metric dimension is most discriminating?

### 5.5 Qualitative Analysis
Failure mode analysis. Most common failure types per system. Sample failure traces.

---

## 6. Discussion

### 6.1 What the Results Tell Us About the Field
Where current systems are strong. Where they consistently fail. Saturation risk.

### 6.2 Benchmark Limitations
Not all real engineering work is captured. Contamination risks. Human-in-the-loop tasks
are underrepresented. Federtion tier is early.

### 6.3 Future Directions
More task tiers (design, research, incident response). Dynamic task generation.
Continuous leaderboard with fresh tasks. Integration with The Wasteland's wanted board.

---

## 7. Conclusion

Multi-agent LLM orchestration is arriving fast. We need to measure it rigorously.
MAO-Bench provides the infrastructure. [Call to action: contribute tasks, submit results.]

---

## Appendix

A. Full task schema specification
B. Extended results tables (per-task scores for all systems)
C. Harness implementation notes
D. Contamination audit methodology
E. Inter-annotator agreement analysis
