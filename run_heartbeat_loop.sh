#!/bin/bash
# 心跳循环：每15分钟运行一次，永久运行
WORKSPACE="/home/node/.openclaw/workspace"
cd "$WORKSPACE"

echo "[$(date)] 心跳循环启动"

while true; do
    echo "[$(date)] 运行 heartbeat_runner..."
    python3 projects/self-improvement-research/heartbeat_runner.py >> briefings/daemon_research.log 2>&1
    
    echo "[$(date)] 运行 self_research..."
    python3 projects/self-improvement-research/self_research.py >> briefings/daemon_research.log 2>&1
    
    echo "[$(date)] 睡眠15分钟..."
    sleep 900  # 15分钟
done
