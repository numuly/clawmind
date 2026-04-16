# ClawMind v2 规划实施

## 步骤任务
- [1/4] 明确「ClawMind v2 规划实施」的具体目标

## 当前状态
- 进度：第 1 步 / 共 4 步
- 当前步骤：明确「ClawMind v2 规划实施」的具体目标
- v2 规划现状：v2 规划进行中：经验持久化 + 执行器 + 研究→行动 pipeline

## 【分析】ClawMind v2 核心缺失
当前 v2 规划进度仅 10%，核心问题：
1. 经验持久化：memory.db 已实现，但未与 drive() 深度集成
2. 执行器：heartbeat_runner 执行层已修复，但提案执行深度待提升
3. 研究→行动 pipeline：self_research.py 独立运行，未汇入提案系统

## 【建议下一步】
- P0：完成 select_best_action 集成（已修复 drive()）
- P1：补全提案的 action_type，让 task 类提案真正被执行
- P2：打通 self_research → propose() 的结果汇入