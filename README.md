# ClawMind — 自我进化 AI Agent 引擎

> _让 AI Agent 能像人一样从经验中学习，在错误中改进，在夜晚自主工作。_

## 核心特性

- **健康度驱动** — 像生命体一样有"健康度"概念，0.0（危险）到 1.0（巅峰），决定系统该冒进还是保守
- **VFM 提案评分** — Value × Feasibility × Momentum，自动选出最优行动
- **经验记忆** — remember/recall 机制，不重复犯错
- **自驱循环** — 每 15 分钟一次心跳，自动研究→提案→执行→推进
- **步骤追踪** — `[n/m]` 格式子步骤，避免重复执行已完成步骤

## 架构

```
clawmind/
├── self_driver.py          # 驱动：健康度 + VFM 评分 + 反思
├── state_manager.py        # 状态：项目 / 任务 / 日志管理
├── v2_executor.py          # 执行器：执行提案产生的实际代码
└── memory/
    └── memory_core.py      # 记忆：经验存取

projects/
├── self-improvement-research/
│   ├── heartbeat_runner.py  # 心跳执行器（每15分钟）
│   └── self_research.py     # 自主研究（每30分钟）
└── clawmind-v2/
    ├── analysis_1.md        # v2 规划分析
    ├── research_insights.md  # AI Agent 研究洞察
    └── completion_summary.md # 完成总结
```

## 核心指标

| 指标 | 值 |
|------|-----|
| 当前健康度 | 1.0 |
| 当前任务 | ClawMind v2 规划实施 |
| 任务进度 | 100% ✅ |
| 今晚新增 | v2_executor.py, research pipeline, 步骤追踪 |

## 工作流

```
每 15 分钟心跳:
  drive() → calc_health → propose() → select_best_action → next_action

每 30 分钟研究:
  self_research.py → GitHub搜索 → 写入memory/ → 汇入proposals

执行循环:
  [1/4] 分析 → [2/4] 执行核心步骤 → [3/4] 验证 → [4/4] 完成
```

## 快速开始

```bash
# 查看当前状态
cd /home/node/.openclaw/workspace
python3 scripts/self_driver.py status

# 查看提案评分
python3 scripts/self_driver.py propose

# 手动跑心跳
python3 projects/self-improvement-research/heartbeat_runner.py
```

## 关键文件

| 文件 | 作用 |
|------|------|
| `scripts/self_driver.py` | 自驱力引擎核心 |
| `scripts/v2_executor.py` | v2 执行器 |
| `projects/self-improvement-research/heartbeat_runner.py` | 心跳循环 |
| `projects/self-improvement-research/self_research.py` | 自主研究 |
| `state/current_state.json` | 当前状态（私有）|
| `.github_token` | GitHub API Token（私有）|

## v2 改进亮点

1. **select_best_action 集成到 drive()** — 修好了3个月的 bug
2. **研究→提案 pipeline** — self_research 结果自动汇入 propose()
3. **v2_executor** — 提案真正被执行，不只是写笔记
4. **_done_steps 追踪** — 不重复执行已完成步骤
5. **步骤优先级加成** — [n/m] 步骤得分 ×1.3，避免被通用提案挤出队列
