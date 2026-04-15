# mind

> Your self-evolving AI agent engine — drives itself forward, learns from experience, never repeats the same mistake.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub Repo](https://img.shields.io/badge/GitHub-numuly/mind-blue?logo=github)](https://github.com/numuly/mind)
[![Release](https://img.shields.io/badge/Release-v1.0.0-blue?logo=github)](https://github.com/numuly/mind/releases/latest)

---
[中文](docs/README_zh.md) · [English](docs/README_en.md)

---

## What is it

**mind** gives your AI agent a self-motivation engine. It continuously monitors task health, scores proposed actions objectively, learns from past successes and failures, and breaks stuck tasks into smaller steps — all without any external dependencies.

Think of it as the "gut feeling" of your agent, except measurable and traceable.

---

## Features

**Health-Driven Motivation**

The engine calculates a health score (0.0–1.0) from multiple live signals: recent success rate, current progress, momentum direction, and consecutive failure penalty. When health drops, the engine adapts — either by forcing reflection or by breaking the current task into testable sub-tasks.

**VFM Proposal Scoring**

Every possible next action is scored using: `Value × Feasibility × Momentum × 100`. No guesswork — the highest-scoring proposal wins. The scoring adapts to the agent's current state: desperate agents favor high-reward actions, healthy agents take bigger swings.

**Experience Memory**

Results are stored as structured experiences (intent + path + key insight) and retrieved when similar situations arise. This creates a genuine learning loop — not just state tracking.

**Auto Task Decomposition**

When progress stalls below 30%, the engine automatically splits the current task into 3–4 smaller sub-tasks based on keyword patterns (publish → prepare/execute/verify/complete, research → research/analyze/summarize/归档, etc.).

**Zero Dependencies**

Pure Python stdlib. No `pip install`, no API keys, no external services. Drop it into any Python environment and it works.

---

## Health Formula

```
health = 0.4 + success_rate×0.25 + progress×0.2 + momentum×0.1 − fail_penalty×0.15 + completion×0.1
```

| Score | Status | Recommended Action |
|-------|--------|--------------------|
| ≥ 0.7 | Good | Push forward, take on more |
| 0.4–0.7 | Okay | Stay focused on current step |
| < 0.4 | Danger | Break into smallest testable units |

---

## Quick Start

```python
from mind.self_driver import drive, calc_health, propose, select_best_action
from mind.self_driver import _load_state  # read current state

# Run one self-drive cycle (reads state, scores proposals, decides action)
result = drive()
print(f"Action: {result['action']}, Health: {result['health']}")

# Check health manually
state = _load_state()
print(f"Health: {calc_health(state):.2f}")

# Generate and score proposals
proposals = propose(state)
best = select_best_action(proposals, state.get('driver', {}))
print(f"Recommended: {best['description']} (score={best['score']:.1f})")
```

---

## Project Structure

```
mind/
├── self_driver.py          # Core: health calculation, VFM scoring, drive loop
├── state_manager.py        # State: projects, tasks, activity logs
├── quality_score.py         # Briefing quality scorer (5 dimensions)
└── memory/
    └── memory_core.py      # remember() / recall_experiences() API
```

---

## When to Use

- Build autonomous agents that don't need constant human supervision
- Add self-correction to long-running AI tasks
- Create agents that learn from past failures (stored in SQLite)
- Run AI task pipelines that need measurable health monitoring

---

## Install

Download `mind.skill` from the [latest release](https://github.com/numuly/mind/releases/latest) and install via ClawHub:

```bash
clawhub install mind --registry https://cn.clawhub-mirror.com
```

Or copy the `mind/` folder directly into your skills directory.

---

## License

MIT — free to use, modify, and distribute. Credit is appreciated but not required.
