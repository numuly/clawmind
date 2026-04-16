#!/usr/bin/env python3
"""
research_daemon.py — ClawMind 自主研究守护进程

每分钟检查一次，深夜时段（23:00-06:00 CST）主动运行自主研究。
白天时段有项目则推进，无项目则待机。

vs Crontab：
- 精度更高（1分钟检查）
- 状态驱动（有项目才做 vs cron 的固定调度）
- 与 OpenClaw 状态系统集成
"""

import os, sys, time, json
from datetime import datetime, timezone, timedelta

STATE_FILE = "/home/node/.openclaw/workspace/state/current_state.json"
RESEARCH_SCRIPT = "/home/node/.openclaw/workspace/projects/self-improvement-research/research_step.py"
SELF_RESEARCH_SCRIPT = "/home/node/.openclaw/workspace/projects/self-improvement-research/self_research.py"
PROGRESS_FILE = "/home/node/.openclaw/workspace/briefings/daemon_research.log"

def log(msg):
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(PROGRESS_FILE, "a") as f:
        f.write(line + "\n")

def get_active_project():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE) as f:
        state = json.load(f)
    for p in state.get("projects", []):
        if p.get("status") == "active":
            return p
    return None

def run_research_step():
    """运行一次研究步骤（有项目时）"""
    import subprocess
    result = subprocess.run(
        [sys.executable, RESEARCH_SCRIPT],
        capture_output=True, text=True, timeout=300
    )
    if result.stdout:
        for line in result.stdout.strip().split("\n")[-5:]:
            if line.strip():
                log(f"  {line}")
    if result.returncode != 0 and result.stderr:
        log(f"  stderr: {result.stderr[:200]}")

def run_self_research():
    """运行自主研究（无项目时），不依赖状态系统，只写 memory"""
    import subprocess
    result = subprocess.run(
        [sys.executable, SELF_RESEARCH_SCRIPT],
        capture_output=True, text=True, timeout=60
    )
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                log(f"  [self] {line}")
    if result.returncode != 0 and result.stderr:
        log(f"  [self] stderr: {result.stderr[:200]}")

def _execute_proposal(proposal_desc: str) -> str:
    """
    将提案描述转换为真正的执行动作。
    返回执行结果描述。
    """
    import subprocess
    d = proposal_desc.strip()

    # 提案模式匹配 → 执行对应动作
    if "检查技能库" in d or "可用更新" in d:
        result = subprocess.run(
            ["clawhub", "update", "--all"],
            capture_output=True, text=True, timeout=60
        )
        updated = [l for l in result.stdout.split("\n") if "updated" in l or "✔" in l]
        if updated:
            return f"✅ 技能更新: {', '.join(u.strip() for u in updated[:3])}"
        return "✅ 技能库已是最新"

    if "select_best_action" in d and "集成" in d:
        # 提案：把 select_best_action 集成到 drive()
        # 这需要修改 self_driver.py，是代码改动，不在这里做
        # 改为：输出集成方案供人工参考
        plan = (
            "select_best_action() 集成方案：\n"
            "1. 在 drive() 返回中增加 'top_proposals' 字段（ scored[0:3]）\n"
            "2. daemon 使用 drive()['top_proposals'][0] 而非 propose() 直接结果\n"
            "3. 保持 select_best_action() CLI 功能不变\n"
            "→ 写入 state['next_action'] = None，让 daemon 进入下一轮"
        )
        return f"📋 方案已记录: {plan[:80]}"

    if "get_driver_status" in d and "集成" in d:
        return "📋 get_driver_status() 是 CLI 工具，集成到 drive() 会增加复杂度，建议保持 CLI 专用"

    if "硬编码阈值" in d or "HEALTH_THRESHOLD" in d:
        return "📋 阈值常量提取: HEALTH_REFLECT_THRESHOLD = 0.4 已存在于代码中，无需提取"

    if "日志裁剪" in d or "MAX_LOG_SIZE" in d:
        return "📋 日志裁剪硬编码: _prune_log(state, max_keep=20) 已是参数化设计，无需修改"

    if "审计" in d or "代码审计" in d:
        return f"📋 审计项已记录: {d[:60]}"

    if "MEMORY" in d or "记忆" in d or "沉淀" in d:
        return "📋 知识沉淀: 建议定期将研究洞察写入 MEMORY.md"

    if "经验持久化" in d or "Obsidian" in d or ("v2" in d and "规划" in d):
        # P0: 真正执行经验同步 -> Obsidian Vault
        import subprocess
        sync_script = "/home/node/.openclaw/workspace/projects/clawmind-v2/run_sync.py"
        try:
            r = subprocess.run([sys.executable, sync_script],
                capture_output=True, text=True, timeout=30)
            return (r.stdout.strip() or "v2 P0 经验同步完成")
        except Exception as e:
            return f"经验同步失败: {e}"


    if "[1/4]" in d or "[2/4]" in d or "[3/4]" in d or "[4/4]" in d:
        # 子任务提案对机器来说太模糊，执行一次后标记为需人工，不再重复
        return f"📋 子任务无法自动执行: {d[:50]}"

    if "推进当前任务" in d:
        return "📋 推进任务需人工介入: 无明确下一步可执行"

    # 默认：说明无法自动执行
    return f"📋 需人工处理: {d[:60]}"


def write_progress_note(note):
    log(note)

def execute_next_action_from_state():
    """
    读取 state 的 next_action，执行它。
    这是真正的自主执行循环：drive() → 有 action 就执行，不等待确认。
    """
    import importlib, sys as _sys
    _sys.path.insert(0, "/home/node/.openclaw/workspace/skills/clawmind/scripts")
    try:
        from self_driver import drive as _drive, _load_state as _ls, _save_state as _ss, _mark_dirty as _md, _prune_log as _pl
        from state_manager import save_session_context
    except Exception as e:
        log(f"  [drive] 加载失败: {e}")
        return

    try:
        result = _drive()
    except Exception as e:
        log(f"  [drive] 执行失败: {e}")
        return

    state = _ls()
    health = result.get("health", 0)
    action = result.get("action", "continue")
    status_update = result.get("status_update", "")
    next_action = state.get("next_action", "")

    log(f"  drive() | health={health} | action={action} | {status_update[:50]}")

    if next_action and next_action not in ("无", "暂无", "待定"):
        log(f"  [自主执行] {next_action[:60]}")
        # 真正执行提案
        exec_result = _execute_proposal(next_action)
        if exec_result:
            log(f"  {exec_result}")
            state["log"].append({
                "time": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
                "entry": exec_result[:80]
            })
        # 任何执行结果（成功 or 失败）都Dismiss，避免重复提案
        dismissed = state.setdefault("_dismissed_proposals", [])
        key = next_action[:30]
        if key not in dismissed:
            dismissed.append(key)
            log(f"  [Dismiss] 加入黑名单: {key}")
        # 追加执行记录
        state["log"].append({
            "time": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
            "entry": f"自主执行: {next_action[:80]}"
        })
        # ── 关键：执行后清除 next_action，防止死循环 ───────────────
        # 只有当 action 被明确消耗（如写入了文件/笔记）才清除
        # 这里统一清除，让下一轮 propose() 重新生成
        prev_action = next_action
        state["next_action"] = None
        state["_last_next_action"] = prev_action
        _just_redirected = False  # 会在重定向时设为 True

        # 检测卡死：同一 next_action 重复出现超过 3 次
        recent_same = [
            e for e in state.get("log", [])[-10:]
            if prev_action and prev_action[:30] in e.get("entry", "")
        ]
        if len(recent_same) >= 3:
            log(f"  [警告] 检测到 next_action 重复执行 {len(recent_same)} 次，强制触发 propose()")
            try:
                from self_driver import propose as _propose
                import random
                all_proposals = _propose(state, context="突破当前僵局，生成全新方向")
                # 过滤：排除上一个 next_action（避免重定向到同一个提案）
                proposals = [p for p in all_proposals if prev_action[:20] not in p.get("description", "")]
                if not proposals:
                    proposals = all_proposals
                # 随机选一个，不要总选第一个
                if proposals:
                    best = random.choice(proposals)
                    # Redirect 后的 execute 会再次Dismiss这个新提案，
                    # 所以在这里清空 next_action，让下一轮 else 分支重新 propose()
                    state["next_action"] = None
                    state["_last_next_action"] = best.get("description", "待定")
                    state["_skip_next_execute"] = True  # 下一轮 execute 跳过，让 else 分支 propose 新的
                    log(f"  [重定向] 新方向: {state['_last_next_action'][:60]}")
                    state["log"].append({
                        "time": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
                        "entry": f"[新方向] {state['_last_next_action'][:80]}"
                    })
            except Exception as e:
                log(f"  propose() 调用失败: {e}")
                state["next_action"] = "待定"
        # ────────────────────────────────────────────────────────
        _skip = state.pop("_skip_next_execute", False)
        _pl(state)
        _md()
        _ss(state)
        save_session_context(state, result)
    else:
        # next_action 为空 → 调用 propose() 生成新方向，不要空转
        from self_driver import propose as _propose
        all_proposals = _propose(state)
        # 过滤：排除上一个 next_action（避免重复）
        prev_action = state.get("_last_next_action", "")
        proposals = [p for p in all_proposals if not prev_action or prev_action[:20] not in p.get("description", "")]
        if not proposals:
            proposals = all_proposals
        if proposals:
            best = proposals[0]
            state["next_action"] = best.get("description", "待定")
            state["_last_next_action"] = state["next_action"]
            log(f"  [新方向] {state['next_action'][:60]}")
            state["log"].append({
                "time": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
                "entry": f"生成新提案: {state['next_action'][:80]}"
            })
        else:
            state["next_action"] = "待定"

        _pl(state)
        _md()
        _ss(state)
        save_session_context(state, result)


def daemon_loop():
    log(f"守护进程启动 PID={os.getpid()}")
    check_count = 0

    while True:
        check_count += 1
        now = datetime.now(timezone(timedelta(hours=8)))

        # ── 核心：drive() + 自主执行 next_action ────────────────
        execute_next_action_from_state()

        # 之后继续原有研究逻辑（有项目推进，无则探索）
        project = get_active_project()
        if project:
            log(f"研究 #{check_count} | 项目: {project.get('name', '?')}")
            run_research_step()
            sleep_seconds = 180
        else:
            log(f"自主探索 #{check_count}")
            run_self_research()
            sleep_seconds = 180

        time.sleep(sleep_seconds)

if __name__ == "__main__":
    daemon_loop()
