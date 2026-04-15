---
name: brain
description: 思思的自我进化核心引擎。赋予 AI agent 自驱力、目标追踪、经验记忆、提案评分能力。当需要"自我驱动"、"主动规划"、"健康度追踪"、"VFM评分决策"、"经验记忆管理"时触发此 skill。
---

# brain — 自我进化引擎

思思的"大脑"：由自驱力引擎（self_driver）、状态管理（state_manager）、简报质量评分（quality_score）组成。与 memory-skill 协同工作。

## 系统架构

```
brain (自驱力)
  ├─ self_driver.py    ← 动力：健康度计算、VFM 提案评分、反思触发
  ├─ state_manager.py  ← 状态：项目/任务/日志管理
  └─ quality_score.py  ← 评分：简报质量 5 维度评估

memory-skill (记忆)
  └─ memory_core.py    ← 记忆：经验存取、recall/remember

协同方式：
  drive() → 提出提案 → score_action() 评分 → 执行 → remember() 沉淀
```

## 健康度系统

### calc_health(state) → float

```
health = 0.5 + success_rate × 0.3 + progress × 0.2
```

| 分量 | 范围 | 说明 |
|------|------|------|
| 基础分 | 0.5 | 默认健康 |
| 成功率分 | 0~0.3 | 最近5条日志含"完成/成功"的比例 |
| 进度分 | 0~0.2 | 当前任务完成百分比 |

### 健康度阈值

| 健康度 | 状态 | 行动 |
|--------|------|------|
| < 0.3 | 危险 | 降低目标，拆解任务 |
| 0.3~0.4 | 偏低 | 减少每次工作量 |
| 0.4~0.7 | 尚可 | 保持节奏 |
| ≥ 0.7 | 良好 | 挑战更多 |

## VFM 提案评分

### propose(state, context) → list[dict]

根据当前状态生成改进提案列表：

| 提案类型 | 触发条件 | expected_delta |
|----------|----------|----------------|
| 推进当前任务 | 有任务进行中 | 0.1 |
| 从经验学习 | 最近有成功日志 | 0.05 |
| 拆解任务 | 进度 < 30% | 0.08 |
| 技能检查 | 总是包含 | 0.03 |
| 知识沉淀 | 最近有核心发现 | 0.04 |

### score_action(proposal, driver) → float

**VFM 公式**：`Value × Feasibility × Momentum × 100`

| 维度 | 计算方式 |
|------|----------|
| Value | expected_delta × 系数（低健康时系数更大）|
| Feasibility | 0.7基础分，成功模式多时提升，连续低迷时降低 |
| Momentum | 健康度≥0.6→0.9，≥0.4→0.6，<0.4→0.3 |

### select_best_action(proposals, driver) → dict

对所有提案评分，返回得分最高者和完整评分列表。

## 状态管理（state_manager）

```python
from state_manager import push_project, set_task, add_log

push_project(name, goal, status)  # 创建/更新项目
set_task(task, step, total, next_action)  # 设置当前任务进度
add_log(entry)  # 追加日志
```

详细接口见 [references/state-manager.md](references/state-manager.md)

## 经验记忆协同

brain 执行结果自动交给 memory-skill 沉淀：

```python
# 执行后记住经验
remember(f"任务完成。关键认知：...", source="brain")

# 遇到新任务前检索
results = recall_experiences("相关关键词")
```

详见 `memory-skill` skill。

## CLI 用法

```bash
# 主循环
python3 self_driver.py              # → {action, health, reflect}

# 查看引擎状态
python3 self_driver.py status      # → {health, patterns, ...}

# 提案评分报告
python3 self_driver.py propose     # → 完整评分表格
```

## 文件索引

| 文件 | 作用 |
|------|------|
| `scripts/self_driver.py` | 自驱力引擎核心 |
| `scripts/state_manager.py` | 状态管理 |
| `scripts/quality_score.py` | 简报质量评分 |
| `references/state-manager.md` | state_manager 完整接口文档 |
| `references/vfm-design.md` | VFM 评分设计笔记 |
