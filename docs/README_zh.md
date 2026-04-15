# mind

> 你的自主进化 AI 搭档 — 自动驱动、从经验中学习、不再重蹈覆辙。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 这是什么

**mind** 为你的 AI Agent 提供一套自我驱动力引擎。它持续监控任务健康度，对所有候选行动进行客观评分，从过去的成功与失败中学习，并在任务卡顿时自动拆解为可测试的小步骤——全程零外部依赖。

相当于给 AI 装上了一个可量化、可追溯的"内驱力"，而不是靠随机应变。

---

## 核心能力

**健康度驱动**

引擎通过多路信号实时计算健康度（0.0–1.0）：近期成功率、当前进度、势头方向、连续失败惩罚。健康度下降时，引擎自动调整策略——要么强制触发反思，要么将当前任务拆解为可测试的小单元。

**VFM 行动评分**

每个候选行动都通过 `Value × Feasibility × Momentum × 100` 评分。分数最高的行动获胜。评分策略随健康度动态调整：低迷时优先高回报行动，健康时敢于挑战更大目标。

**经验记忆**

执行结果以结构化经验存储（意图 + 路径 + 关键洞察），遇到相似场景时自动检索调用，形成真正的学习闭环，而非简单的状态记录。

**自动任务拆解**

当进度卡在 30% 以下时，引擎根据关键词模式将大任务自动拆分为 3~4 个子任务（发布类 → 准备/执行/验证/完成，研究类 → 调研/分析/总结/归档，修复类 → 定位/修复/验证/沉淀教训等）。

**零依赖**

纯 Python 标准库。无需 `pip install`，无需 API Key，任何 Python 环境直接运行。

---

## 健康度公式

```
health = 0.4 + success_rate×0.25 + progress×0.2 + momentum×0.1 − fail_penalty×0.15 + completion×0.1
```

| 分数 | 状态 | 建议行动 |
|------|------|---------|
| ≥ 0.7 | 良好 | 推进更多挑战 |
| 0.4–0.7 | 正常 | 专注当前步骤 |
| < 0.4 | 危险 | 拆解为最小可测试单元 |

---

## 快速开始

```python
from mind.self_driver import drive, calc_health, propose, select_best_action
from mind.self_driver import _load_state  # 读取当前状态

# 运行一次自驱循环（读取状态 → 评分提案 → 决策行动）
result = drive()
print(f"行动: {result['action']}, 健康度: {result['health']}")

# 手动检查健康度
state = _load_state()
print(f"健康度: {calc_health(state):.2f}")

# 生成并评分提案
proposals = propose(state)
best = select_best_action(proposals, state.get('driver', {}))
print(f"推荐: {best['description']} (得分={best['score']:.1f})")
```

---

## 项目结构

```
mind/
├── self_driver.py          # 核心：健康度计算、VFM评分、自驱循环
├── state_manager.py        # 状态：项目、任务、活动日志
├── quality_score.py         # 简报质量评分（5维度）
└── memory/
    └── memory_core.py      # remember() / recall_experiences() API
```

---

## 适用场景

- 构建无需人工持续盯守的自主 Agent
- 为长时间运行的 AI 任务添加自我修正机制
- 创建能从历史失败中学习的 Agent（经验持久化至 SQLite）
- 需要可量化健康度监控的 AI 任务流水线

---

## 安装

从 [最新发行版](https://github.com/numuly/mind/releases/latest) 下载 `mind.skill`，通过 ClawHub 安装：

```bash
clawhub install mind --registry https://cn.clawhub-mirror.com
```

或直接将 `mind/` 文件夹复制到你的 skills 目录下。

---

## 协议

MIT — 可自由使用、修改和分发。引用请注明，但非强制要求。
