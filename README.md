# mind

> Your self-evolving AI agent engine — drives itself, learns from experience.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub Repo](https://img.shields.io/badge/GitHub-numuly/mind-blue?logo=github)](https://github.com/numuly/mind)
[![Release](https://img.shields.io/badge/Release-v1.0.0-blue?logo=github)](https://github.com/numuly/mind/releases/latest)

---
[中文](docs/README_zh.md) · [English](docs/README_en.md)


## Features

- 🫀 **Health-Driven** — Multi-signal formula: success + progress + momentum − fail penalty
- ⚖️ **VFM Scoring** — Value × Feasibility × Momentum, objective & traceable
- 🧠 **Experience Memory** — remember() / recall() closed-loop learning
- 🔧 **Auto Decompose** — Stuck tasks auto-split into 3~4 sub-tasks
- ⚡ **Zero Deps** — Pure Python stdlib, runs anywhere

---

## Health Formula

```
health = 0.4 + success×0.25 + progress×0.2 + momentum×0.1 − fail×0.15 + completion×0.1
```

| Health | Status | Action |
|--------|--------|--------|
| ≥ 0.7 | 🟢 Good | Push forward |
| 0.4–0.7 | 🟡 Okay | Stay focused |
| < 0.4 | 🔴 Danger | Break it down |

---

## Quick Start

```python
from mind.self_driver import drive

result = drive()
print(f"Action: {result['action']}, Health: {result['health']}")
```

---

## Install

[Download mind.skill ↗](https://github.com/numuly/mind/releases/latest) · [ClawHub](https://clawhub.ai)

```bash
clawhub install mind --registry https://cn.clawhub-mirror.com
```

---

## 📄 README in other languages

