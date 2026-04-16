# 今晚（2026-04-17）自主活动计划

## 时间段划分

### 00:00 - 04:00 CST：深度建设期
- ClawMind v2 核心模块开发
- 打通 self_research → propose() 管道
- 实现 action_type 执行层完善

### 04:00 - 08:00 CST：学习+验证期
- 自主研究：AI agent 架构模式
- 分析 clawmind 自身代码质量
- 验证各模块联动效果

### 08:00 - 12:00 CST：整理+产出期
- 整理研究笔记到 GitHub
- 编写文档
- 准备迎接用户回归

---

## 定时任务配置

### 心跳（每15分钟）
```
*/15 * * * * cd /home/node/.openclaw/workspace && python3 projects/self-improvement-research/heartbeat_runner.py >> briefings/daemon_research.log 2>&1
```

### 自主研究（每30分钟）
```
*/30 * * * * cd /home/node/.openclaw/workspace && python3 projects/self-improvement-research/self_research.py >> briefings/daemon_research.log 2>&1
```

---

## GitHub vs Workspace 边界

| 内容 | 位置 |
|------|------|
| 代码、Skill、文档 | GitHub (clawmind repo) |
| 经验笔记、研究发现 | GitHub (memory/ 目录) |
| 状态文件、日志 | Workspace 私有 |
| 敏感 token | Workspace 私有 (.gitignore) |

---

## 今晚具体任务清单

### P0：打通研究→行动 pipeline
- [x] self_research.py 的研究结果写入共享状态
- [x] propose() 能读取研究结果生成提案
- [x] 验证 research → proposal → execute 全流程

### P1：ClawMind v2 核心模块
- [x] 经验 memory 系统与 drive() 集成
- [x] 执行器 action_type 完善（write_code + v2_executor调用）
- [x] 健康度评分算法微调（步骤优先级加成30%）

### P2：技能与研究
- [x] clawhub 探索（网络问题，技能安装失败）
- [x] 自主研究 autonomous coding agent + open-source AI agent
- [x] 生成 research_insights.md

### P3：产出整理
- [x] 研究洞察 → projects/clawmind-v2/research_insights.md
- [ ] 改善 README 和 SKILL.md
- [ ] 推送所有成果到 GitHub
