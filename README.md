# 🧠 mind

> Your self-evolving AI agent engine — drives itself, learns from experience, never repeats the same mistake.
>
> 你的自主进化 AI 搭档 — 自动驱动、从经验中学习、不再重蹈覆辙。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub Repo](https://img.shields.io/badge/GitHub-numuly/mind-blue?logo=github)](https://github.com/numuly/mind)
[![Release](https://img.shields.io/badge/Release-v1.0.0-blue?logo=github)](https://github.com/numuly/mind/releases/latest)

---

## 特性 | Features

| | |
|---|---|
| 🫀 健康度驱动 | Multi-signal health: success + progress + momentum − fail penalty |
| ⚖️ VFM 评分 | Value × Feasibility × Momentum，客观可追溯 |
| 🧠 经验记忆 | remember() / recall() 形成学习闭环 |
| 🔧 自动拆解 | 进度卡顿时自动将大任务拆为子任务 |
| ⚡ 零依赖 | 纯 Python 内置库，任何环境均可运行 |

---

## 快速开始 | Quick Start

```python
from mind.self_driver import drive, calc_health, propose, select_best_action

result = drive()
print(f"行动: {result['action']}, 健康度: {result['health']}")
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

[mind.skill ↗](https://github.com/numuly/mind/releases/latest) · 通过 [ClawHub](https://clawhub.ai) 安装

```bash
clawhub install mind --registry https://cn.clawhub-mirror.com
```

---

## 协议 | License

[MIT](LICENSE) — 自由使用，引用请注明。
