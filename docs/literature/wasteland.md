# The Wasteland — Research Summary

**Source**: Steve Yegge, ["Welcome to the Wasteland: A Thousand Gas Towns"](https://steve-yegge.medium.com/welcome-to-the-wasteland-a-thousand-gas-towns-a5eb9bc8dc1f), Mar 2026
**Community**: https://gastownhall.ai

---

## Overview

The Wasteland is the federated layer on top of Gas Town: a mechanism for linking thousands of independent Gas Towns together into a trust network for collaborative, distributed work. Where Gas Town is a single organization's agent swarm, the Wasteland is the internet of agent swarms — a global coordination protocol for multi-party, multi-organization multi-agent work.

Yegge's framing: "The Wasteland is a way to link thousands of Gas Towns together in a trust network, to build stuff really, really fast."

---

## The Wanted Board

The central coordination primitive is a shared **Wanted Board** — a global issue board where:
- Anyone posts work items (ideas, bugs, features, research tasks)
- Participants browse and claim items using their Gas Town
- Completed work is submitted as a PR
- PRs are validated by Wasteland maintainers
- Accepted PRs earn the contributor a **stamp** (reputation credit)

The workflow is a Git pull-request model applied to any kind of work — not just code. Designs, documentation, research summaries, test suites all count.

---

## Stamps and Reputation

When a PR is accepted in the Wasteland, the validator stamps the contributor's **passbook**. Stamps are:
- **Multi-dimensional**: score Quality, Reliability, and Creativity independently
- **Auditable**: permanent append-only ledger
- **Versioned**: full history in Dolt
- **Cumulative**: stamps aggregate into an overall reputation score

This creates a verifiable, on-chain reputation system for AI-augmented work — solving the problem of "who actually did this, a human or their agent?" by stamping the _Gas Town identity_ rather than just the GitHub handle.

---

## Trust Levels

Trust accretes through demonstrated work:

| Level | Name | Capabilities |
|-------|------|-------------|
| 1 | Registered Participant | Browse, claim, submit completions |
| 2 | Contributor | Elevated access to premium tasks |
| 3 | Maintainer | Validate others' work; issue stamps |

Maintainers are the trust anchors of the Wasteland. Becoming one requires accumulating stamps from existing maintainers — an apprenticeship model. This prevents Sybil attacks where a bad actor creates many fake Gas Towns.

---

## Federation Architecture

The Wasteland uses **Dolt + DoltHub** as the federated data backbone:
- Each Gas Town has a Dolt database
- Work items, stamps, and reputation live in DoltHub-synced tables
- Fork/merge model: Gas Towns fork the wanted board, do work, push PRs
- DoltHub provides the global merge surface and conflict resolution

This is Git's collaboration model applied to structured data (not just files), enabling:
- Conflict-free parallel contributions
- Full audit history of who did what and when
- Offline/async work with eventual sync

---

## The LEGO / Gas City Model

Yegge describes a "Gas City" composition model where individual Gas Towns specialize and compose:
- One Gas Town does frontend work
- Another does API development
- Another does testing
- A "LEGO" layer assembles their outputs into a coherent product

The Wasteland provides the coordination substrate for this — work items flow between Gas Towns via the wanted board, and stamps track cross-Town contributions.

---

## Gamification Layer

The Wasteland includes an RPG-style gamification layer:
- **Character sheets**: each Gas Town has a profile showing stats, stamps, specialties
- **Leaderboards**: global and per-domain rankings
- **Quest progression**: task chains that build on each other

This is not just cosmetic. Gamification drives contribution incentives and surfaces the healthiest Gas Towns for high-value work assignment.

---

## Implications for MAO-Bench

The Wasteland introduces the **federated coordination tier** — a set of problems that don't appear in single-Gas-Town evaluations:

| Wasteland Concept | MAO-Bench Metric |
|------------------|-----------------|
| Cross-Gas-Town PR submission | Federated task completion rate |
| Stamp validation latency | Cross-org coordination overhead |
| Trust level assignment | Trust protocol correctness |
| Wanted board contention | Duplicate work prevention under competition |
| Dolt merge across organizations | Cross-repo merge conflict rate |
| Reputation system accuracy | Quality-of-work attribution correctness |

The **federated task set** (25 tasks, 6% of the full benchmark) exercises these dimensions. These tasks are the hardest in MAO-Bench — they require not just multi-agent coordination within one system but cross-system trust protocols.

---

## Why This Matters Now (March 2026)

The Wasteland dropped this month. Gas Town has 2,400 PRs in two months. The infrastructure for federated multi-agent work exists and is being actively used. The question is not "will this exist?" but "how do we measure whether it works well?"

That's the gap MAO-Bench fills: the Wasteland needs an evaluation framework as much as it needs contributors.

---

## References

- [Welcome to the Wasteland (Medium)](https://steve-yegge.medium.com/welcome-to-the-wasteland-a-thousand-gas-towns-a5eb9bc8dc1f)
- [Hacker News discussion](https://news.ycombinator.com/item?id=47250133)
- [gastownhall.ai](https://gastownhall.ai)
- [Steve Yegge on X](https://x.com/Steve_Yegge/status/2029096297140310200)
