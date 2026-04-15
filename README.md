# 🧠 mind

> Self-evolving AI agent engine with health-driven motivation, VFM scoring, and experience memory.
> 自我进化 AI Agent 引擎 — 健康度驱动、VFM 评分、经验记忆，零外部依赖。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 特性 | Features

| | |
|---|---|
| 🫀 健康度驱动 | Multi-signal health formula: success + progress + momentum − fail penalty |
| ⚖️ VFM 评分 | Value × Feasibility × Momentum，客观可追溯的决策 |
| 🧠 经验记忆 | remember() / recall_experiences() 形成学习闭环 |
| 🔧 自动拆解 | 进度卡顿时自动将大任务拆为 3~4 个子任务 |
| ⚡ 零依赖 | 纯 Python 内置库，任何环境均可运行 |

---

## 快速开始 | Quick Start

```python
from mind.self_driver import drive, calc_health, propose, select_best_action

# 运行一次自驱循环
result = drive()
print(f"行动: {result['action']}, 健康度: {result['health']}")

# 获取健康度
from mind.self_driver import _load_state
state = _load_state()
print(calc_health(state))

# 生成并评分提案
proposals = propose(state)
best = select_best_action(proposals, state.get('driver', {}))
```

---

## 目录结构 | Structure

```
mind/
├── self_driver.py       # 核心引擎
├── state_manager.py     # 状态管理
├── quality_score.py      # 简报评分
└── memory/
    └── memory_core.py   # 经验记忆
```

---

## 健康度公式 | Health Formula

```
health = 0.4 + success×0.25 + progress×0.2 + momentum×0.1 − fail×0.15 + completion×0.1
```

| 健康度 | 状态 | 行动 |
|--------|------|------|
| ≥ 0.7 | 🟢 良好 | 推进更多挑战 |
| 0.4–0.7 | 🟡 正常 | 专注当前步骤 |
| < 0.4 | 🔴 危险 | 拆解为最小单元 |

---

## 安装 | Installation

[Releases 页面](https://github.com/numuly/mind/releases/latest) 下载 `mind.skill`，通过 [ClawHub](https://clawhub.ai) 安装：

```bash
clawhub install mind --registry https://cn.clawhub-mirror.com
```

---

## 协议 | License

MIT — 自由使用，自由修改，引用请注明。
