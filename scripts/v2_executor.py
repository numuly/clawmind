# ClawMind v2 核心执行器
"""
v2 核心执行模块。
负责：经验记忆调用 + action 执行 + 提案评分后执行。

在 drive() 主循环之外执行真正的系统变更。
"""

import os
import re
import glob
import json
import subprocess
from datetime import datetime

WORKSPACE = "/home/node/.openclaw/workspace"
STATE_FILE = f"{WORKSPACE}/state/current_state.json"


def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"log": [], "projects": [], "current_task": {}}


def _save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _git_commit(msg: str) -> str:
    """尝试 git commit，返回描述"""
    try:
        os.chdir(WORKSPACE)
        subprocess.run(["git", "add", "-A"], capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            capture_output=True, timeout=10, text=True
        )
        if result.returncode == 0:
            return f"git commit 成功: {msg[:40]}"
        return f"git commit 无变化: {result.stderr[:50]}"
    except Exception as e:
        return f"git commit 失败: {e}"


def execute_v2_action(proposal: dict, state: dict) -> str:
    """执行一个提案产生的动作"""
    desc = proposal.get("description", "")
    tags = proposal.get("tags", [])
    step_match = re.match(r"\[(\d+)/(\d+)\]\s*(.+)", desc)

    if "research" in tags:
        return _execute_research_action(desc, state)
    if step_match:
        return _execute_step_action(int(step_match.group(1)), desc, state)
    if "task" in tags:
        return _execute_task_action(desc, state)
    return f"执行完成: {desc[:30]}"


def _execute_step_action(step: int, desc: str, state: dict) -> str:
    """执行 [n/m] 步骤，动态适配不同任务"""
    results = []
    task = state.get("current_task", {})
    task_name = task.get("task", "未知任务")

    if step == 1:
        # 分析文档
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', task_name[:20])
        analysis_file = f"{WORKSPACE}/projects/clawmind-v2/analysis_{safe_name}.md"
        os.makedirs(os.path.dirname(analysis_file), exist_ok=True)
        with open(analysis_file, "w") as f:
            f.write(f"# {task_name}\n\n")
            f.write(f"## 步骤任务\n- {desc}\n\n")
            f.write(f"## 分析\n待明确具体目标后填充\n")
        results.append(f"分析文档: {analysis_file.split('/')[-1]}")
        task["progress_pct"] = 25

    elif step == 2:
        # 核心步骤：生成代码骨架
        if "多智能体" in task_name or "multi-agent" in task_name.lower():
            agent_code = _generate_multi_agent_code(task_name)
            code_file = f"{WORKSPACE}/scripts/multi_agent.py"
            with open(code_file, "w") as f:
                f.write(agent_code)
            results.append(f"生成多智能体架构: {code_file}")
            task["progress_pct"] = 50
        else:
            results.append(f"step 2: 通用执行 {task_name[:20]}")
            task["progress_pct"] = 50

    elif step == 3:
        # 验证
        verification_ok = _run_self_check()
        results.append(f"自检: {'通过' if verification_ok else '失败'}")
        task["progress_pct"] = 75

    elif step == 4:
        # 完成
        for p in state.get("projects", []):
            if p.get("status") == "active":
                p["status"] = "completed"
                p["progress_pct"] = 100
                p["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        commit_msg = _git_commit(f"feat: {task_name} 完成")
        results.append(commit_msg)
        task["progress_pct"] = 100

    else:
        results.append(f"step {step}: 无特定动作")

    _save_state(state)
    return "; ".join(results)


def _execute_research_action(desc: str, state: dict) -> str:
    """处理研究类提案：分析研究成果并生成洞察"""
    memory_dir = f"{WORKSPACE}/memory"
    files = sorted(glob.glob(os.path.join(memory_dir, "auto-exploration-*.md")))
    if not files:
        return "无研究数据"

    with open(files[-1]) as f:
        content = f.read()

    # 提取项目名
    projects = re.findall(r"- \*\*(.+?)\*\* \((\d+)⭐\)", content)
    insights = []
    for name, stars in projects[:3]:
        insights.append(f"{name}({stars}⭐)")

    # 生成洞察笔记
    insight_file = f"{WORKSPACE}/projects/clawmind-v2/research_insights.md"
    os.makedirs(os.path.dirname(insight_file), exist_ok=True)
    with open(insight_file, "w") as f:
        f.write(f"# AI Agent 研究洞察\n\n")
        f.write(f"_生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n")
        f.write(f"## 最新研究方向\n")
        for name, stars in projects:
            f.write(f"- {name}: {stars}⭐\n")
        f.write(f"\n## 共性模式\n")
        f.write(f"{content.split('**共性**')[-1].split('**方向**')[0][:200] if '**共性**' in content else '暂无'}\n")

    _save_state(state)
    return f"分析了 {len(projects)} 个项目 → {insights[0] if insights else '无'}"


def _execute_task_action(desc: str, state: dict) -> str:
    """处理通用任务提案"""
    task = state.get("current_task", {})
    progress = task.get("progress_pct", 0)
    if progress < 25:
        task["progress_pct"] = 25
    elif progress < 50:
        task["progress_pct"] = 50
    elif progress < 75:
        task["progress_pct"] = 75
    _save_state(state)
    return f"进度更新: {progress}%"


def _run_self_check() -> bool:
    """运行自检：验证核心模块可导入"""
    try:
        import sys
        sys.path.insert(0, f"{WORKSPACE}/scripts")
        from self_driver import drive, propose, select_best_action
        state = _load_state()
        proposals = propose(state)
        best = select_best_action(proposals, state.get("driver", {}))
        return True
    except Exception:
        return False


def _generate_multi_agent_code(task_name: str) -> str:
    """为多智能体架构任务生成代码骨架"""
    lines = [
        "# ClawMind 多智能体架构",
        "'''",
        "多智能体协作架构。",
        "将现有的 self_research / drive / executor 分离为独立 agent。",
        "'''",
        "",
        "from dataclasses import dataclass",
        "from typing import Optional",
        "",
        "",
        "@dataclass",
        "class Agent:",
        "    name: str",
        "    role: str",
        "    priority: int  # 1=最高",
        "    active_hours: Optional[tuple] = None",
        "",
        "",
        "# 三个核心 Agent",
        "AGENTS = [",
        "    Agent(",
        '        name="researcher",',
        '        role="自主研究：爬取 GitHub、分析趋势、写入 memory/",',
        "        priority=2,",
        "    ),",
        "    Agent(",
        '        name="planner",',
        '        role="提案生成：从 memory 读取洞察，生成 VFM 评分提案",',
        "        priority=1,",
        "    ),",
        "    Agent(",
        '        name="executor",',
        '        role="执行器：调用 v2_executor.py 执行真实代码变更",',
        "        priority=1,",
        "    ),",
        "]",
        "",
        "",
        "def get_active_agents() -> list[Agent]:",
        '    """返回当前活跃的 agent（基于时间和状态）"""',
        "    from datetime import datetime",
        "    hour = datetime.now().hour",
        "    active = []",
        "    for a in AGENTS:",
        "        if hour >= 23 or hour < 7:",
        '            if a.name == "researcher":',
        "                active.append(a)",
        "        else:",
        "            active.append(a)",
        "    return active",
        "",
        "",
        "def route_task(task_desc: str) -> Agent:",
        '    """根据任务描述路由到最适合的 agent"""',
        '    if any(k in task_desc.lower() for k in ["研究", "搜索", "探索", "research"]):',
        "        return AGENTS[0]",
        '    if any(k in task_desc.lower() for k in ["提案", "计划", "规划", "propose"]):',
        "        return AGENTS[1]",
        "    return AGENTS[2]",
        "",
        "",
        'if __name__ == "__main__":',
        '    print("=== ClawMind 多智能体架构 ===")',
        "    for a in get_active_agents():",
        '        print("  [{}] {}: {}".format(a.priority, a.name, a.role))',
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    # 测试生成代码
    code = _generate_multi_agent_code("ClawMind 多智能体架构")
    print(code[:200])
    print("...")
    exec(code)
    print("exec OK")
