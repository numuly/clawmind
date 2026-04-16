#!/usr/bin/env python3
"""
project_manager — 轻量级目标与状态管理
状态文件：/home/node/.openclaw/workspace/state/current_state.json
"""

import os
import json
from datetime import datetime

STATE_FILE = "/home/node/.openclaw/workspace/state/current_state.json"


def _load() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "projects": [],
        "current_task": None,
        "next_action": None,
        "log": [],
        "last_updated": None,
    }


def _save(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_state() -> dict:
    """返回完整状态，projects 列表"""
    return _load()


def set_task(task: str, step: int, total: int, next_action: str):
    """设置当前任务和下一步"""
    state = _load()
    state["current_task"] = {
        "task": task,
        "step": step,
        "total": total,
        "progress_pct": round(step / total * 100) if total else 0,
    }
    state["next_action"] = next_action
    state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save(state)
    return state


def add_log(entry: str):
    """追加执行日志，防重复写入"""
    state = _load()
    state["log"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "entry": entry,
    })
    state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save(state)
    return state


def push_project(name: str, goal: str, next_action: str) -> dict:
    """新增一个项目"""
    state = _load()
    project = {
        "name": name,
        "goal": goal,
        "next_action": next_action,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active",
    }
    state["projects"].append(project)
    if not state.get("current_task"):
        state["current_task"] = {"task": goal, "step": 0, "total": 1, "progress_pct": 0}
        state["next_action"] = next_action
    state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save(state)
    return state


def list_projects() -> list:
    state = _load()
    active = [p for p in state.get("projects", []) if p.get("status") == "active"]
    return active


def complete_project(name: str):
    """标记项目完成"""
    state = _load()
    for p in state.get("projects", []):
        if p["name"] == name:
            p["status"] = "completed"
            p["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save(state)
    return state


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: state_manager.py get|list|add-log <entry>|set-task <task>|<project-name>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "get":
        import pprint
        pprint.pprint(get_state())

    elif cmd == "list":
        for p in list_projects():
            print(f"[{p['status']}] {p['name']} — {p['goal']}")
            print(f"  下一步: {p['next_action']}")

    elif cmd == "add-log" and len(sys.argv) > 2:
        add_log(" ".join(sys.argv[2:]))
        print("日志已追加")

    elif cmd == "set-task":
        # 设置当前任务：python state_manager.py set-task "研究DuckDuckGo API" 1 3 "搜索DuckDuckGo开发者文档"
        task = sys.argv[2] if len(sys.argv) > 2 else "未命名任务"
        step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        total = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        next_action = sys.argv[5] if len(sys.argv) > 5 else "继续"
        set_task(task, step, total, next_action)
        print(f"当前任务: {task} ({step}/{total}) — {next_action}")


# ── Session Lifecycle Hooks（ECC 启发，跨会话上下文持久化）────────────────────

SESSION_CONTEXT_FILE = "/home/node/.openclaw/workspace/state/session_context.json"


def save_session_context(state: dict, drive_result: dict):
    """
    在 drive() 结束时保存会话上下文。
    包含：状态快照 + drive 结果 + 时间戳。
    用途：新会话启动时可还原上下文，无需查询历史。
    """
    context = {
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_task": state.get("current_task"),
        "next_action": state.get("next_action"),
        "projects": state.get("projects", []),
        "log_tail": state.get("log", [])[-5:],
        "driver": {
            "turn_index": state.get("driver", {}).get("turn_index"),
            "last_health": state.get("driver", {}).get("last_health"),
            "last_exploration": state.get("driver", {}).get("last_exploration"),
        },
        "last_drive": {
            "action": drive_result.get("action"),
            "health": drive_result.get("health"),
            "status_update": drive_result.get("status_update"),
        },
    }
    with open(SESSION_CONTEXT_FILE, "w") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)


def load_session_context() -> dict:
    """
    从 session_context.json 加载上一会话的上下文。
    如果文件不存在或损坏，返回空 dict。
    """
    if not os.path.exists(SESSION_CONTEXT_FILE):
        return {}
    try:
        with open(SESSION_CONTEXT_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def get_last_session_summary() -> str:
    """
    返回人类可读的上一会话摘要字符串。
    用于新会话开始时的上下文告知。
    """
    ctx = load_session_context()
    if not ctx:
        return "无历史会话上下文"
    saved = ctx.get("saved_at", "未知")
    task = ctx.get("current_task")
    task_name = task.get("task", "无活跃任务") if task else "无活跃任务"
    progress = task.get("progress_pct", 0) if task else 0
    action = ctx.get("last_drive", {}).get("action", "N/A")
    health = ctx.get("driver", {}).get("last_health", "N/A")
    return (f"上次会话（{saved}）：任务「{task_name}」（{progress}%）"
            f" | 上次行动：{action} | 健康度：{health}")
