#!/usr/bin/env python3
"""
mini_self_driver — 轻量自驱力引擎
无外部依赖，纯 Python + 内置库
追踪任务成功率，自动触发反思，记录学习模式
"""

import os
import json
import time
from datetime import datetime
from typing import Optional

STATE_FILE = "/home/node/.openclaw/workspace/state/current_state.json"
DRIVER_FILE = "/home/node/.openclaw/workspace/state/self_driver.json"

# ----------------- 状态读写 -----------------

def _load(path: str) -> dict:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def _save(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------- 健康度计算 -----------------

def calc_health(state: dict) -> float:
    """
    计算当前任务执行健康度（0.0 ~ 1.0）
    公式：基础分(0.5) + 成功率分(0~0.3) + 进度分(0~0.2)
    """
    log = state.get("log", [])
    if not log:
        return 0.5  # 无日志，默认健康

    # 最近 5 条日志中成功的比例
    recent = log[-5:]
    successes = sum(1 for e in recent if any(
        kw in e.get("entry", "") for kw in ["完成", "成功", "done", "ok"]
    ))
    success_rate = successes / len(recent)

    # 进度
    task = state.get("current_task")
    progress = task.get("progress_pct", 0) / 100 if task else 0

    health = 0.5 + success_rate * 0.3 + progress * 0.2
    return min(1.0, max(0.0, health))


def should_reflect(health: float, threshold: float = 0.4) -> bool:
    """健康度低于阈值时触发深度反思"""
    return health < threshold


# ----------------- 反思触发器 -----------------

REFLECT_QUESTIONS = [
    "当前任务卡在哪里？是思路问题还是执行问题？",
    "有没有之前学过的经验可以用到这里？",
    "这一步是否真的值得做，还是在逃避更核心的问题？",
    "如果这个问题明天还要做，今天最少要完成哪一步？",
    "有没有把一个复杂问题拆得足够小？",
]


def trigger_reflection(driver: dict) -> dict:
    """生成一轮反思，返回建议"""
    health = driver.get("last_health", 0.5)
    consecutive_low = driver.get("consecutive_low", 0)

    # 选择反思问题（轮换）
    q_index = consecutive_low % len(REFLECT_QUESTIONS)
    question = REFLECT_QUESTIONS[q_index]

    driver["consecutive_low"] = consecutive_low + 1
    driver["last_reflect_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "question": question,
        "health": health,
        "consecutive_low": consecutive_low + 1,
        "advice": _advice_for_health(health),
    }


def _advice_for_health(health: float) -> str:
    if health < 0.3:
        return "【危险】健康度过低，建议：降低目标难度，先完成最小可测试单元"
    elif health < 0.5:
        return "【偏低】建议：拆解任务，减少每次心跳的工作量，确保有可交付的进展"
    elif health < 0.7:
        return "【尚可】保持当前节奏，专注于完成当前步骤而非完美"
    else:
        return "【良好】状态不错，可以适当挑战稍难一点的目标"


# ----------------- 经验模式记录 -----------------

def learn_pattern(success: bool, context: str, driver: dict):
    """从一次执行中学习，更新模式库"""
    patterns = driver.get("patterns", [])
    pattern = {
        "type": "success" if success else "failure",
        "context": context[:50],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    patterns.append(pattern)
    # 只保留最近 20 条
    driver["patterns"] = patterns[-20:]


# ----------------- 主循环 -----------------

def drive():
    """
    心跳自驱力主循环。
    返回 (action: str, health: float, reflect_result: dict or None)
    """
    state = _load(STATE_FILE)
    driver = _load(DRIVER_FILE)

    # 初始化
    if "patterns" not in driver:
        driver["patterns"] = []
    if "consecutive_low" not in driver:
        driver["consecutive_low"] = 0

    health = calc_health(state)
    driver["last_health"] = health
    driver["last_check_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    reflect_result = None
    action = "continue"

    if should_reflect(health):
        reflect_result = trigger_reflection(driver)
        action = "reflect"
    elif health >= 0.7:
        action = "push_forward"  # 状态好，可以挑战更多
        driver["consecutive_low"] = 0  # 重置低健康计数器

    _save(DRIVER_FILE, driver)

    return {
        "action": action,
        "health": round(health, 3),
        "reflect": reflect_result,
        "current_task": state.get("current_task", {}).get("task"),
        "next_action": state.get("next_action"),
    }


def get_driver_status() -> dict:
    driver = _load(DRIVER_FILE)
    return {
        "health": driver.get("last_health", None),
        "consecutive_low": driver.get("consecutive_low", 0),
        "last_check": driver.get("last_check_time", "从未"),
        "last_reflect": driver.get("last_reflect_time", "从未"),
        "pattern_count": len(driver.get("patterns", [])),
    }


def get_driver_status() -> dict:
    driver = _load(DRIVER_FILE)
    return {
        "health": driver.get("last_health", None),
        "consecutive_low": driver.get("consecutive_low", 0),
        "last_check": driver.get("last_check_time", "从未"),
        "last_reflect": driver.get("last_reflect_time", "从未"),
        "pattern_count": len(driver.get("patterns", [])),
    }


# ==================== VFM 评分体系 ====================

def propose(state: dict, context: str = "") -> list[dict]:
    """
    根据当前状态和上下文生成改进提案列表。
    每个提案包含: description, expected_delta_health, tags
    """
    proposals = []
    task = state.get("current_task", {})
    task_name = task.get("task", "无任务")
    progress = task.get("progress_pct", 0)
    log = state.get("log", [])

    # 1. 进度推进提案（如果当前任务进行中）
    if task_name and progress > 0 and progress < 100:
        proposals.append({
            "description": f"推进当前任务「{task_name}」下一步",
            "expected_delta_health": 0.1,
            "tags": ["continue", "task"]
        })

    # 2. 状态更新提案（如果日志有进展）
    if log:
        last_entry = log[-1].get("entry", "")
        if "完成" in last_entry or "成功" in last_entry:
            proposals.append({
                "description": "从成功经验中提取模式，存入记忆",
                "expected_delta_health": 0.05,
                "tags": ["memory", "learning"]
            })

    # 3. 拆解提案（如果进度卡住）
    if progress < 30:
        proposals.append({
            "description": "拆解当前任务为更小的可测试单元",
            "expected_delta_health": 0.08,
            "tags": ["planning", "task"]
        })

    # 4. 技能检查提案（周期性）
    proposals.append({
        "description": "检查技能库是否有可用更新或新技能",
        "expected_delta_health": 0.03,
        "tags": ["skill", "maintenance"]
    })

    # 5. 知识沉淀提案（如果最近有重大发现）
    if any("核心" in e.get("entry", "") for e in log[-3:]):
        proposals.append({
            "description": "将核心发现写入 MEMORY.md 和 Obsidian",
            "expected_delta_health": 0.04,
            "tags": ["memory", "knowledge"]
        })

    return proposals


def score_action(proposal: dict, driver: dict) -> float:
    """
    VFM 评分：Value × Feasibility × Momentum × 100
    返回 0~100 的评分。
    """
    health = driver.get("last_health", 0.5)
    consecutive_low = driver.get("consecutive_low", 0)
    patterns = driver.get("patterns", [])
    tags = proposal.get("tags", [])

    # Value: 基于 expected_delta_health 和当前健康度
    # 健康度低时，高 delta 的提案价值更高
    delta = proposal.get("expected_delta_health", 0.05)
    if health < 0.4:
        value = min(1.0, delta * 5)  # 低健康时，给高增益提案更高价值
    else:
        value = min(1.0, delta * 3)

    # Feasibility: 基于当前状态
    # 有成功模式时可行性更高，连续低迷时降低
    feasibility = 0.7
    if "task" in tags:
        feasibility = 0.8  # 任务类提案通常可行
    if consecutive_low > 2:
        feasibility *= 0.7  # 连续低迷时降低预期
    if len([p for p in patterns if p["type"] == "success"]) > 3:
        feasibility = min(1.0, feasibility * 1.2)  # 成功经验多则提升

    # Momentum: 基于当前势头
    # 健康度高于 0.6 时势头好，低于 0.3 时势头差
    if health >= 0.6:
        momentum = 0.9
    elif health >= 0.4:
        momentum = 0.6
    else:
        momentum = 0.3

    score = value * feasibility * momentum * 100
    return round(score, 1)


def select_best_action(proposals: list[dict], driver: dict) -> dict:
    """对提案列表评分，返回得分最高的提案"""
    if not proposals:
        return {"description": "无事可做，保持当前状态", "score": 0}

    scored = [{"proposal": p, "score": score_action(p, driver)} for p in proposals]
    scored.sort(key=lambda x: x["score"], reverse=True)
    best = scored[0]
    return {
        **best["proposal"],
        "score": best["score"],
        "all_scores": [(s["proposal"]["description"][:30], s["score"]) for s in scored]
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        import pprint
        pprint.pprint(get_driver_status())
    elif len(sys.argv) > 1 and sys.argv[1] == "propose":
        state = _load(STATE_FILE)
        driver = _load(DRIVER_FILE)
        proposals = propose(state)
        best = select_best_action(proposals, driver)
        print("=== 提案评分 ===")
        for desc, score in best["all_scores"]:
            print(f"  [{score:.1f}] {desc}")
        print(f"\n推荐: {best['description']} (score={best['score']})")
    else:
        result = drive()
        import pprint
        pprint.pprint(result)
