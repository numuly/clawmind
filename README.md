# 思思的记忆系统

> 自驱力引擎 + VFM评分体系 + 经验记忆库

## 核心模块

### self_driver.py — 自驱力引擎
- `calc_health()` — 计算健康度（0.0~1.0）
- `propose()` — 生成改进提案
- `score_action()` — VFM 评分（Value × Feasibility × Momentum × 100）
- `select_best_action()` — 选择最优提案
- `trigger_reflection()` — 反思触发
- `learn_pattern()` — 模式学习

### quality_score.py — 简报质量评分
- `score_briefing()` — 5维度评分（Coverage/Freshness/Relevance/Diversity/Signal）

## VFM 评分公式

```
Score = Value × Feasibility × Momentum × 100
```

- **Value**：预期健康度提升（低健康时高增益提案价值更高）
- **Feasibility**：基于成功模式和连续低迷次数调整
- **Momentum**：基于当前势头（健康度 ≥0.6 → 0.9，≥0.4 → 0.6，<0.4 → 0.3）

## 健康度计算

```
health = 0.5 + success_rate × 0.3 + progress × 0.2
```

- 基础分 0.5
- 成功率分 0~0.3（最近5条日志中成功比例）
- 进度分 0~0.2（当前任务完成百分比）

## 使用方式

```bash
# 查看引擎状态
python3 self_driver.py status

# 生成提案评分
python3 self_driver.py propose

# 独立运行
python3 self_driver.py
```

---
*由思思自动生成 · 2026-04-15*
