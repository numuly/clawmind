# 🧠 mind — Self-Evolving Agent Engine

> A lightweight self-motivation engine for AI agents. No external dependencies — pure Python.

**mind** gives your AI agent a "mind" — the unified system of memory and self-motivation. It learns from past mistakes, drives itself forward autonomously, and continuously improves through experience.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

### 🫀 Health-Driven Motivation

Self-correcting motivation that adapts based on task success rate, momentum, and progress:

```
health = 0.4 + success×0.25 + progress×0.2 + momentum×0.1 − fail_penalty×0.15 + completion×0.1
```

| Health Range | Status | Action |
|--------------|--------|--------|
| ≥ 0.7 | 🟢 Good | Push forward, take on more |
| 0.4–0.7 | 🟡 Okay | Keep节奏，专注完成当前步骤 |
| 0.3–0.4 | 🟠 Low | Reduce scope, ensure delivery |
| < 0.3 | 🔴 Danger | Break into smallest testable units |

### ⚖️ VFM Proposal Scoring

Every action is objectively scored using **Value × Feasibility × Momentum × 100**. No more gut feelings — just measurable, traceable decisions.

### 🧠 Experience Memory

Closed-loop learning: store successes and failures as structured experiences, retrieve them when similar situations arise.

```
drive() → propose() → execute → remember() ↔ recall()
```

### 🔧 Auto Task Decomposition

Large stuck tasks are automatically broken into 3–4 testable sub-tasks by keyword pattern matching.

---

## 📦 Quick Start

```python
from mind.self_driver import drive, calc_health, propose, select_best_action

# Run one self-drive cycle
result = drive()
print(f"Action: {result['action']}, Health: {result['health']}")

# Get current health
state = _load_state()  # from self_driver
health = calc_health(state)

# Get ranked proposals
proposals = propose(state)
best = select_best_action(proposals, driver)
```

---

## 📁 Project Structure

```
mind/
├── self_driver.py          # Core engine: health + VFM + reflection
├── state_manager.py        # State: projects / tasks / logs
├── quality_score.py        # Briefing quality scorer (5-dim)
├── memory/
│   └── memory_core.py      # Experience recall & remember
└── references/
    ├── state-manager.md    # Full state_manager API
    └── vfm-design.md       # VFM scoring design doc
```

---

## 🧮 VFM Formula

```
Score = Value × Feasibility × Momentum × 100
```

- **Value** — Expected health delta; higher when agent is struggling
- **Feasibility** — Boosted by past successes, reduced during slump
- **Momentum** — 0.9 (health ≥ 0.6), 0.6 (≥ 0.4), 0.3 (< 0.4)

---

## 📊 Health Thresholds & Reflection Questions

When health drops below 0.4, the agent triggers self-reflection:

1. Where exactly is the task stuck — mindset or execution?
2. Can past experience apply here?
3. Is this step worth doing, or avoiding a more core problem?
4. What's the minimum viable step to complete today?
5. Is this problem broken down small enough?

---

## 📥 Installation

Download the latest `.skill` file from the [Releases page](https://github.com/numuly/mind/releases/download/v1.0.0/mind.skill) and install via [ClawHub](https://clawhub.ai):

```bash
clawhub install mind --registry https://cn.clawhub-mirror.com
```

Or install directly from source:

```bash
git clone https://github.com/numuly/mind.git
cp -r mind ~/.../skills/mind
```

---

## 📝 License

MIT — Use freely, modify freely, credit appreciated.
