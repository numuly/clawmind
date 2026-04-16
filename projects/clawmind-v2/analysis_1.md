# ClawMind 多智能体架构

## 步骤任务
- [1/4] 明确「ClawMind 多智能体架构」的具体目标

## 当前状态
- 进度：第 1 步 / 共 4 步
- 当前步骤：明确「ClawMind 多智能体架构」的具体目标
- v2 规划现状：v2 核心完成：执行器+研究pipeline+提案系统

## 【分析】ClawMind v2 核心缺失
当前 v2 规划进度仅 10%，核心问题：
1. 经验持久化：memory.db 已实现，但未与 drive() 深度集成
2. 执行器：heartbeat_runner 执行层已修复，但提案执行深度待提升
3. 研究→行动 pipeline：self_research.py 独立运行，已修复汇入

## 【建议下一步】
- P0：select_best_action 集成 ✓（已修复 drive()）
- P1：提案执行层完善（进行中）
- P2：self_research → propose() 汇入 ✓（已完成）