#!/bin/bash
# 设置今晚的定时任务

# ClawMind 自主心跳（每15分钟）
(grep -q "heartbeat_runner" /proc/1/cgroup 2>/dev/null || echo "checking env") && echo "env ok"

cat << 'CRONEOF' | crontab -
# ClawMind 自主心跳（每15分钟）
*/15 * * * * cd /home/node/.openclaw/workspace && /usr/bin/python3 projects/self-improvement-research/heartbeat_runner.py >> briefings/daemon_research.log 2>&1

# 自主研究（每30分钟）
*/30 * * * * cd /home/node/.openclaw/workspace && /usr/bin/python3 projects/self-improvement-research/self_research.py >> briefings/daemon_research.log 2>&1
CRONEOF

echo "done"
