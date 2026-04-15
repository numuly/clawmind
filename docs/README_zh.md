# 🧠 mind

> 你的自主进化 AI 搭档 — 自动驱动、从经验中学习、不再重蹈覆辙。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 特性

| | |
|---|---|
| 🫀 健康度驱动 | 多信号公式：成功率 + 进度 + 势头 − 失败惩罚 |
| ⚖️ VFM 评分 | Value × Feasibility × Momentum，客观可追溯 |
| 🧠 经验记忆 | remember() / recall() 形成学习闭环 |
| 🔧 自动拆解 | 进度卡顿时自动将大任务拆为子任务 |
| ⚡ 零依赖 | 纯 Python 内置库，任何环境均可运行 |

---

## 健康度公式

```
health = 0.4 + success×0.25 + progress×0.2 + momentum×0.1 − fail×0.15 + completion×0.1
```

| 健康度 | 状态 | 行动 |
|--------|------|------|
| ≥ 0.7 | 🟢 良好 | 推进更多挑战 |
| 0.4–0.7 | 🟡 正常 | 专注当前步骤 |
| < 0.4 | 🔴 危险 | 拆解为最小单元 |

---

## 快速开始

```python
from mind.self_driver import drive, calc_health, propose, select_best_action

result = drive()
print(f"行动: {result['action']}, 健康度: {result['health']}")
```

---

## 安装

[下载 mind.skill ↗](https://github.com/numuly/mind/releases/latest) · 通过 [ClawHub](https://clawhub.ai) 安装

```bash
clawhub install mind --registry https://cn.clawhub-mirror.com
```

---

## 协议

[MIT](LICENSE) — 自由使用，引用请注明。
