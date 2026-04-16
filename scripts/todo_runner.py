#!/usr/bin/env python3
"""
todo_runner.py — ClawMind 任务执行器
基于 Todo List + 时间超时的自主执行引擎。

核心循环（每15分钟心跳触发一次）：
1. 读取当前 todo 列表
2. 检查当前任务状态
3. 超时 → 排查原因 → 继续/跳过/改变方案
4. 完成 → 移到下一项
5. 保存状态
"""

import sys
import os
import json
import uuid
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/home/node/.openclaw/workspace"
STATE_FILE = f"{WORKSPACE}/state/current_state.json"
TODO_KEY = "todo_list"
STALLED_THRESHOLD = 3  # 连续 N 次心跳无进展 = 停滞


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"log": [], "projects": [], "current_task": {}}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_todo(state):
    return state.get(TODO_KEY, {"items": [], "index": 0, "stalled_count": {}})


def save_todo(state, todo):
    state[TODO_KEY] = todo
    save_state(state)


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def now_minutes():
    return datetime.now()


def elapsed_minutes(started_at: str) -> float:
    """返回从 started_at 到现在经过的分钟数"""
    try:
        start = datetime.fromisoformat(started_at)
        return (now_minutes() - start).total_seconds() / 60
    except Exception:
        return 0


def get_current_item(todo: dict):
    """获取当前运行中的任务"""
    items = todo.get("items", [])
    index = todo.get("index", 0)
    if 0 <= index < len(items):
        item = items[index]
        if item.get("status") in ("pending", "running"):
            return item
    return None


def get_next_pending(todo: dict):
    """获取下一个待处理任务"""
    for item in todo.get("items", []):
        if item.get("status") == "pending":
            return item
    return None


def start_item(item: dict) -> dict:
    """启动一个任务"""
    item["status"] = "running"
    item["started_at"] = now_iso()
    item["attempts"] = item.get("attempts", 0) + 1
    return item


def check_progress(item: dict, state: dict) -> tuple[bool, str]:
    """
    检查任务是否完成。
    返回 (is_done, reason)
    """
    task_name = item.get("task", "")
    
    # 1. 检查 current_task 进度
    current_task = state.get("current_task", {})
    if current_task.get("task", "").replace(" ", "") in task_name.replace(" ", ""):
        progress = current_task.get("progress_pct", 0)
        if progress >= 100:
            return True, f"进度达到 100%"
        # 有进展
        if progress > (item.get("last_progress", 0)):
            item["last_progress"] = progress
            item["stalled_count"] = 0
            return False, f"进度 {progress}%"
    
    # 2. 检查 recent commits（任务相关提交）
    try:
        result = subprocess.run(
            ["git", "-C", WORKSPACE, "log", "--oneline", "-10"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n")[:3]:
                if any(k in line.lower() for k in task_name.lower().split()[:2]):
                    return True, f"Git commit: {line[:50]}"
    except Exception:
        pass
    
    return False, "未完成"


def handle_timeout(item: dict, reason: str) -> str:
    """
    超时处理：排查原因，决定下一步。
    返回决策: "continue" / "skip" / "change"
    """
    suggestions = []
    
    # 常见超时原因 + 建议
    if "网络" in reason or "超时" in reason:
        suggestions.append(("skip", "网络问题，跳过"))
    elif "阻塞" in reason or "无进展" in reason:
        suggestions.append(("change", "方案受阻，尝试改变方案"))
    elif item.get("attempts", 0) >= 3:
        suggestions.append(("skip", "已达3次尝试上限，跳过"))
    else:
        suggestions.append(("continue", "延长时限继续"))
    
    # 取第一个建议执行
    decision, msg = suggestions[0]
    return msg


def tick() -> str:
    """
    执行一次心跳 tick。
    返回执行结果描述。
    """
    state = load_state()
    todo = get_todo(state)
    items = todo.get("items", [])
    
    # 无任务
    if not items:
        return "Todo list 为空，无任务执行"
    
    current = get_current_item(todo)
    
    if current is None:
        # 尝试获取下一个
        current = get_next_pending(todo)
        if current:
            start_item(current)
            todo["index"] = items.index(current)
            save_todo(state, todo)
            return f"开始新任务: {current.get('task', '')[:50]}"
        return "所有任务已完成"
    
    # 检查超时
    limit = current.get("limit_minutes", 60)
    elapsed = elapsed_minutes(current.get("started_at", now_iso()))
    
    # 检查是否停滞（连续心跳无进展）
    stalled = todo.get("stalled_count", {}).get(current.get("id", ""), 0)
    is_done, reason = check_progress(current, state)
    
    if is_done:
        # 标记完成
        current["status"] = "done"
        current["completed_at"] = now_iso()
        todo["index"] = items.index(current) + 1
        todo["stalled_count"][current.get("id", "")] = 0
        save_todo(state, todo)
        return f"完成: {current.get('task', '')[:50]} | {reason}"
    
    # 更新停滞计数
    if not is_done and elapsed > 5:  # 超过5分钟仍无进展
        stalled += 1
        todo.setdefault("stalled_count", {})[current.get("id", "")] = stalled
    
    # 超时判断
    if elapsed > limit or stalled >= STALLED_THRESHOLD:
        current["status"] = "timeout"
        decision_msg = handle_timeout(current, reason)
        
        if "跳过" in decision_msg:
            current["status"] = "skipped"
            current["skip_reason"] = decision_msg
            todo["index"] = items.index(current) + 1
            todo["stalled_count"][current.get("id", "")] = 0
            save_todo(state, todo)
            return f"跳过: {current.get('task', '')[:50]} | {decision_msg}"
        elif "继续" in decision_msg:
            # 延长时限，继续
            current["limit_minutes"] = limit * 1.5
            current["started_at"] = now_iso()
            todo["stalled_count"][current.get("id", "")] = 0
            save_todo(state, todo)
            return f"继续: {current.get('task', '')[:50]} | 延长时限至 {int(limit*1.5)}min"
        else:
            # 改变方案：重新标记为 pending，更新描述
            current["status"] = "pending"
            current["task"] = f"[重试] {current.get('task', '')}"
            current["started_at"] = now_iso()
            todo["stalled_count"][current.get("id", "")] = 0
            save_todo(state, todo)
            return f"改变方案: {current.get('task', '')[:50]}"
    
    save_todo(state, todo)
    return f"进行中: {current.get('task', '')[:50]} | {int(elapsed)}/{limit}min | 停滞{stalled}次"


def add_task(task: str, limit_minutes: int = 60) -> str:
    """向 todo 列表添加新任务"""
    state = load_state()
    todo = get_todo(state)
    item = {
        "id": str(uuid.uuid4())[:8],
        "task": task,
        "limit_minutes": limit_minutes,
        "status": "pending",
        "created_at": now_iso(),
        "attempts": 0,
    }
    todo.setdefault("items", []).append(item)
    save_todo(state, todo)
    return f"添加任务: {task[:50]} (限时 {limit_minutes}min)"


def list_tasks() -> str:
    """列出所有任务"""
    state = load_state()
    todo = get_todo(state)
    items = todo.get("items", [])
    if not items:
        return "Todo list 为空"
    
    lines = []
    for i, item in enumerate(items):
        marker = "→" if i == todo.get("index", 0) else " "
        status = item.get("status", "?")
        lines.append(f"{marker} [{status}] {item.get('task', '')[:50]}")
    return "\n".join(lines)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tick"
    
    if cmd == "tick":
        result = tick()
        print(result)
    elif cmd == "add":
        task = " ".join(sys.argv[2:])
        print(add_task(task))
    elif cmd == "list":
        print(list_tasks())
    elif cmd == "clear":
        state = load_state()
        if TODO_KEY in state:
            del state[TODO_KEY]
            save_state(state)
        print("Todo list 已清空")
    else:
        print(f"未知命令: {cmd}")
        print("用法: python todo_runner.py [tick|add|list|clear]")
