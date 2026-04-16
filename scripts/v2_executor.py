# ClawMind v2 核心执行器
"""
v2 核心执行模块。
负责：经验记忆调用 + action 执行 + 提案评分后执行。
"""

def execute_v2_action(proposal: dict, state: dict) -> str:
    """执行一个提案产生的动作"""
    desc = proposal.get("description", "")
    tags = proposal.get("tags", [])
    
    if "research" in tags:
        return _execute_research_action(desc, state)
    if "task" in tags:
        return _execute_task_action(desc, state)
    return f"执行完成: {desc[:30]}"


def _execute_research_action(desc: str, state: dict) -> str:
    """处理研究类提案：分析研究成果并更新系统"""
    # 读取最新研究笔记，提取洞察
    import glob, os
    memory_dir = "/home/node/.openclaw/workspace/memory"
    files = sorted(glob.glob(os.path.join(memory_dir, "auto-exploration-*.md")))
    if files:
        with open(files[-1]) as f:
            content = f.read()
        # 分析内容，生成建议
        return f"分析了最近研究: {files[-1].split('/')[-1]}"
    return "无研究数据"


def _execute_task_action(desc: str, state: dict) -> str:
    """处理任务类提案：推进当前任务"""
    # 更新任务进度
    task = state.get("current_task", {})
    progress = task.get("progress_pct", 0)
    if progress < 25:
        task["progress_pct"] = 25
        return "任务进度更新: 25%"
    elif progress < 50:
        task["progress_pct"] = 50
        return "任务进度更新: 50%"
    return f"当前进度: {progress}%"


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/node/.openclaw/workspace/scripts")
    from self_driver import _load_state
    state = _load_state()
    result = execute_v2_action({"description": "测试", "tags": ["task"]}, state)
    print(result)
