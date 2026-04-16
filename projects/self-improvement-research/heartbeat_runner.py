#!/usr/bin/env python3
"""
heartbeat_runner.py — ClawMind 自主心跳执行器

每次运行：
1. drive() — 计算健康度 + 读 prev_session
2. 有 next_action → 直接执行
3. 无 next_action → propose() 生成 + 执行最优
4. 更新 state + log
5. 输出摘要
"""
import sys
import os
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = "/home/node/.openclaw/workspace"
sys.path.insert(0, f"{WORKSPACE}/scripts")

# ── 加载 ClawMind ───────────────────────────────────────────────
from self_driver import drive, _load_state, _save_state, _mark_dirty, _prune_log
from state_manager import save_session_context

STATE_FILE = f"{WORKSPACE}/state/current_state.json"


# ── 动作执行器 ─────────────────────────────────────────────────
def execute_action(action: dict, state: dict) -> str:
    """
    执行一个 action dict，返回执行描述。
    action 格式：{"type": "write_code"|"search"|"analyze"|"write_note"|"commit", "detail": {...}}
    """
    action_type = action.get("type", "")
    detail = action.get("detail", {})

    if action_type == "write_code":
        path = detail.get("path", "")
        content = detail.get("content", "")
        if path and content:
            full_path = os.path.join(WORKSPACE, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            return f"写入文件 {path}（{len(content)} chars）"

    elif action_type == "write_note":
        date = datetime.now().strftime("%Y-%m-%d")
        note = detail.get("content", "")
        path = Path(WORKSPACE) / "memory" / f"{date}.md"
        with open(path, "a") as f:
            f.write(f"\n## 心跳记录（{datetime.now().strftime('%H:%M')}）\n")
            f.write(note + "\n")
        return f"写入笔记 {path.name}"

    elif action_type == "analyze":
        target = detail.get("target", "")
        if not target:
            return "analyze: 缺少 target 参数"
        path = os.path.join(WORKSPACE, target)
        if os.path.exists(path):
            size = os.path.getsize(path)
            return f"分析文件 {target}（{size} bytes）"
        return f"analyze: 文件不存在 {target}"

    elif action_type == "commit":
        files = detail.get("files", [])
        msg = detail.get("message", "heartbeat auto-commit")
        if not files:
            return "commit: 缺少 files 参数"
        try:
            os.chdir(WORKSPACE)
            for f in files:
                os.system(f"git add {f} 2>/dev/null")
            os.system(f"git commit -m {repr(msg)} 2>/dev/null")
            return f"git commit: {msg[:50]}"
        except Exception as e:
            return f"commit 失败: {e}"

    elif action_type == "noop":
        return "无操作（暂无任务）"

    return f"未知 action 类型: {action_type}"


# ── 从 next_action 字符串反推 action dict ───────────────────────
def parse_next_action(next_action_str: str, state: dict) -> dict:
    """
    简单解析 next_action 字符串，返回 action dict。
    支持格式：
    - "写入文件 path:content" → write_code
    - "写笔记: xxx" → write_note
    - "分析: path" → analyze
    - "git commit files: msg" → commit
    """
    s = next_action_str.strip()
    if not s or s == "无" or "暂无" in s:
        return {"type": "noop", "detail": {}}

    if s.startswith("写入 ") or ":" in s:
        if ":" in s:
            key, val = s.split(":", 1)
            key = key.strip()
            val = val.strip()
            if "文件" in key or "path" in key.lower():
                return {"type": "write_code", "detail": {"path": val, "content": ""}}
            if "笔记" in key or "note" in key.lower():
                return {"type": "write_note", "detail": {"content": val}}
            if "分析" in key:
                return {"type": "analyze", "detail": {"target": val}}

    return {"type": "noop", "detail": {}}


# ── 将 propose() 提案转换为可执行 action ──────────────────────────
def generate_task_output(desc: str, state: dict) -> dict:
    """
    根据任务描述产生结构化的实际输出（而非写笔记）。
    """
    import re
    step_match = re.match(r"\[(\d+)/(\d+)\]\s*(.+)", desc)

    task = state.get("current_task", {}) or {}
    task_name = task.get("task", "未知任务")
    projects = state.get("projects", [])

    current_note = ""
    for p in reversed(projects):
        if p.get("name", "").startswith("clawmind-v2"):
            current_note = p.get("note", "")
            break

    output_lines = [f"# {task_name}", f"\n## 步骤任务", f"- {desc}", f"\n## 当前状态"]

    if step_match:
        step_num = step_match.group(1)
        total = step_match.group(2)
        step_desc = step_match.group(3)
        output_lines.append(f"- 进度：第 {step_num} 步 / 共 {total} 步")
        output_lines.append(f"- 当前步骤：{step_desc}")

    output_lines.append(f"- v2 规划现状：{current_note or '暂无记录'}")

    if "明确" in desc and "目标" in desc:
        output_lines.extend([
            f"\n## 【分析】ClawMind v2 核心缺失",
            f"当前 v2 规划进度仅 10%，核心问题：",
            f"1. 经验持久化：memory.db 已实现，但未与 drive() 深度集成",
            f"2. 执行器：heartbeat_runner 执行层已修复，但提案执行深度待提升",
            f"3. 研究→行动 pipeline：self_research.py 独立运行，未汇入提案系统",
            f"\n## 【建议下一步】",
            f"- P0：完成 select_best_action 集成（已修复 drive()）",
            f"- P1：补全提案的 action_type，让 task 类提案真正被执行",
            f"- P2：打通 self_research → propose() 的结果汇入",
        ])
    elif "执行" in desc or "核心步骤" in desc:
        output_lines.extend([
            f"\n## 【执行计划】",
            f"待明确具体目标后，按 P0→P1→P2 顺序推进",
        ])
    else:
        output_lines.extend([
            f"\n## 【备注】",
            f"此为自动生成的分析文档",
        ])

    content = "\n".join(output_lines)
    return {
        "type": "write_code",
        "detail": {
            "path": f"projects/clawmind-v2/analysis_{step_match.group(1) if step_match else '01'}.md",
            "content": content
        }
    }


def proposal_to_action(proposal: dict, state: dict) -> dict:
    """
    将 propose() 返回的提案转换为可执行 action dict。
    proposal 格式: {description, expected_delta_health, tags}
    """
    desc = proposal.get("description", "")
    tags = proposal.get("tags", [])

    # 代码审计类提案
    if any(t in tags for t in ["audit", "code"]):
        if "self_driver" in desc:
            return {"type": "write_code", "detail": {
                "path": "projects/clawmind-v2/audit_notes.md",
                "content": f"# 代码审计：self_driver.py\n\n## 审计项\n{desc}\n\n## 建议\n已集成 select_best_action 到 drive()。待验证效果。\n"
            }}
        return {"type": "write_note", "detail": {"content": f"[代码审计] {desc}"}}

    # 任务类提案（含 [n/m] 模式）→ 生成结构化分析输出
    if "task" in tags or re.match(r"\[\d+/\d+\]\s*", desc):
        return generate_task_output(desc, state)

    # 记忆/学习类
    if "memory" in tags or "learning" in tags:
        return {"type": "write_note", "detail": {"content": f"[学习] {desc}"}}

    # 默认
    return {"type": "write_note", "detail": {"content": f"[待办] {desc}"}}


# ── 主循环 ─────────────────────────────────────────────────────
def run():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}")
    print(f"【心跳 {now}】ClawMind 自主执行")

    # 1. drive()
    drive_result = drive()
    state = _load_state()

    action_taken = drive_result.get("action", "continue")
    health = drive_result.get("health", 0.5)
    status_update = drive_result.get("status_update", "")
    prev_session = drive_result.get("prev_session", {})

    print(f"  健康度: {health} | 行动: {action_taken}")
    print(f"  状态: {status_update}")

    # 2. 检查 next_action
    next_action = state.get("next_action", "")
    task = state.get("current_task", {}) or {}
    task_name = task.get("task", "无任务")
    progress = task.get("progress_pct", 0)

    executed_desc = ""

    if next_action and next_action not in ("无", "暂无", "待定"):
        print(f"  解析 next_action: {next_action[:60]}")
        action_dict = parse_next_action(next_action, state)

        # 无法解析为可执行动作 → 调用 propose() 生成具体步骤
        if action_dict.get("type") == "noop":
            print(f"  复杂任务，调用 propose() 生成具体步骤")
            from self_driver import propose, select_best_action
            proposals = propose(state, context=next_action)
            if proposals:
                # VFM 评分：选得分最高的提案（修复：之前总是选 proposals[0]）
                best = select_best_action(proposals, state.get("driver", {}))
                action_dict = proposal_to_action(best, state)
                print(f"  提案: {best.get('description','')[:60]} (score={best.get('score',0)})")
                # 把剩余提案写回 next_action
                remaining = "; ".join(p.get("description","") for p in proposals[1:])
                state["next_action"] = remaining if remaining else "待定"
            else:
                action_dict = {"type": "noop", "detail": {}}

        executed_desc = execute_action(action_dict, state)
        print(f"  执行结果: {executed_desc}")

        # 更新日志
        state["log"].append({
            "time": now,
            "entry": f"{executed_desc} | next: {str(next_action)[:50]}"
        })
        _mark_dirty()

    else:
        print(f"  当前无明确 next_action，进入空闲")
        executed_desc = "无 action（空闲）"

    # 3. 无 next_action → 自主探索
    if not next_action or next_action in ("无", "暂无", "待定"):
        print(f"  自主探索模式（暂无明确任务）")
        executed_desc = "空闲 - 等待新任务"

    # 保存状态
    _save_state(state)

    # 摘要输出
    summary = drive_result.get("summary", {})
    if isinstance(summary, dict):
        completed = summary.get("completed", {})
        if completed:
            print(f"\n  摘要: {completed.get('action', executed_desc)}")
    else:
        print(f"\n  摘要: {executed_desc}")


if __name__ == "__main__":
    run()
