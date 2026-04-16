#!/usr/bin/env python3
"""
mini_self_driver — 轻量自驱力引擎
无外部依赖，纯 Python + 内置库
追踪任务成功率，自动触发反思，记录学习模式
"""

import os
import re
import json
import time
from datetime import datetime
from typing import Optional

STATE_FILE = "/home/node/.openclaw/workspace/state/current_state.json"

try:
    from state_manager import save_session_context, load_session_context
except ImportError:
    # 内联降级（standalone 模式）
    _ctx_file = "/home/node/.openclaw/workspace/state/session_context.json"
    def save_session_context(state, drive_result):
        import json
        from datetime import datetime
        ctx = {
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_task": state.get("current_task"),
            "next_action": state.get("next_action"),
            "driver": {"turn_index": state.get("driver", {}).get("turn_index"),
                       "last_health": state.get("driver", {}).get("last_health")},
            "last_drive": {"action": drive_result.get("action"),
                           "health": drive_result.get("health"),
                           "status_update": drive_result.get("status_update")},
        }
        with open(_ctx_file, "w") as f:
            json.dump(ctx, f, ensure_ascii=False, indent=2)
    def load_session_context():
        import json
        if not os.path.exists(_ctx_file):
            return {}
        try:
            with open(_ctx_file) as f:
                return json.load(f)
        except Exception:
            return {}

# ── 健康度阈值常量（代码审计发现，v1.0.13 提取）───────────────────
HEALTH_REFLECT_THRESHOLD = 0.4   # 健康度低于此值触发反思
HEALTH_PUSH_THRESHOLD = 0.7      # 健康度高于此值可挑战更多
HEALTH_DANGER_THRESHOLD = 0.3     # 健康度过低危险线
HEALTH_MAX_LOG = 20              # 日志最大保留条数

# ----------------- 状态读写 -----------------


# ----------------- 优化状态管理（单文件 + 脏标记）-----------------
STATE_FILE = "/home/node/.openclaw/workspace/state/current_state.json"
_dirty = False

def _mark_dirty():
    global _dirty
    _dirty = True

def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"log": [], "projects": [], "current_task": {}, "driver": {}}

def _save_state(state: dict):
    global _dirty
    if not _dirty:
        return
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    _dirty = False

# ----------------- 健康度计算 -----------------

def _parse_progress(entry: str) -> int:
    """从日志条目中提取进度数字（0~100），提取失败返回 -1"""
    m = re.search(r'(\d+)%', entry)
    if m:
        return int(m.group(1))
    if any(kw in entry for kw in ['完成', 'done', '成功', '✅', 'completed']):
        return 100
    return -1


def _is_success(entry: str) -> bool:
    """判断日志条目是否为成功。正向词存在且无负向词才算成功。"""
    neg_kw = ['失败', '卡住', '❌', 'error', 'err', 'failed', 'stuck']
    if any(kw in entry for kw in neg_kw):
        return False
    # 英文词用词边界匹配，避免 ClawHub → ok 这类误匹配
    for kw in ['done', 'completed', 'pass']:
        if re.search(r'(?<![a-zA-Z])' + kw + r'(?![a-zA-Z])', entry, re.IGNORECASE):
            return True
    # 中文词：排除"未完成""无完成"等否定上下文
    for kw in ['完成', '成功', '✅']:
        if kw in entry and not re.search(r'(未|无|没有|尚未|还未)\s*' + kw, entry):
            return True
    return False


def _probe_blindspots(state: dict) -> list:
    """
    主动探测系统潜在盲点。在没有任何外部反馈的情况下，
    通过分析状态内部数据发现可能存在的问题。
    这是 L3（主动发现层）的核心实现。
    """
    issues = []

    # 1. 检查成功率是否虚高（全部成功 = 可能是评估标准太宽松）
    patterns = state.get("driver", {}).get("patterns", [])
    recent = patterns[-10:] if patterns else []
    if recent:
        success_count = sum(1 for p in recent if p.get("type") == "success")
        if success_count == len(recent) and len(recent) >= 5:
            issues.append({
                "type": "blindspot",
                "detail": "近期5次以上全部成功，可能是评估标准太宽松，或只记录了顺利的情况",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    # 2. 检查是否有长期无进展的活跃项目
    for proj in state.get("projects", []):
        if proj.get("status") != "active":
            continue
        last_log = proj.get("last_log_time", "")
        if last_log:
            try:
                from datetime import timedelta
                last_dt = datetime.strptime(last_log, "%Y-%m-%d %H:%M:%S")
                days_ago = (datetime.now() - last_dt).days
                if days_ago >= 7:
                    issues.append({
                        "type": "blindspot",
                        "detail": f"项目「{proj.get('name', '未知')}」已有{days_ago}天无进展，可能遇到隐性障碍",
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
            except:
                pass

    # 3. 检查是否有重复失败模式（相同关键词反复出现）
    if len(patterns) >= 5:
        fail_patterns = [p for p in patterns if p.get("type") == "failure"]
        if len(fail_patterns) >= 3:
            fail_contexts = [p.get("context", "") for p in fail_patterns[-5:]]
            # 检查是否每次失败都包含相同的关键词
            keywords = ["失败", "错误", "无法完成", "没有进展"]
            matched = [kw for kw in keywords if any(kw in ctx for ctx in fail_contexts)]
            if len(matched) >= 2:
                issues.append({
                    "type": "blindspot",
                    "detail": f"多次失败出现相同类型错误：{', '.join(matched)}，可能是系统性缺陷而非偶发问题",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

    # 4. 检查是否有未完成的心跳任务长期悬空
    task = state.get("current_task") or {}
    if task.get("task") and task.get("progress_pct", 0) < 100:
        updated = task.get("updated_at", "")
        if updated:
            try:
                from datetime import timedelta
                updated_dt = datetime.strptime(updated, "%Y-%m-%d %H:%M:%S")
                days_ago = (datetime.now() - updated_dt).days
                if days_ago >= 3 and task.get("progress_pct", 0) == 0:
                    issues.append({
                        "type": "blindspot",
                        "detail": f"当前任务「{task.get('task', '未知')}」3天以上无进展，可能遇到障碍或目标已失效",
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
            except:
                pass

    return issues


def calc_health(state: dict) -> float:
    """
    计算当前任务执行健康度（0.0 ~ 1.0）
    多信号加权：基础分 + 成功率 + 进度 + 势头 + 连续失败惩罚
    
    公式：0.4 + success*0.25 + progress*0.2 + momentum*0.1
          - consecutive_failure*0.15 + completion*0.1
    """
    log = state.get("log", [])
    task = state.get("current_task") or {}
    
    if not log:
        return 0.5

    recent = log[-5:]
    
    # 1. 成功率分（0~0.25）
    successes = sum(1 for e in recent if _is_success(e.get("entry", "")))
    total_checked = sum(1 for e in recent if _parse_progress(e.get("entry", "")) >= 0)
    success_rate = successes / max(total_checked, 1)
    success_score = success_rate * 0.25
    
    # 2. 进度分（0~0.2）
    current_progress = task.get("progress_pct", 0)
    progress_score = (current_progress / 100) * 0.2
    
    # 3. 势头分（0~0.1）：progress 是否在上升
    momentum_score = 0.05  # 默认中等势头
    progress_values = []
    for e in recent:
        pv = _parse_progress(e.get("entry", ""))
        if pv >= 0:
            progress_values.append(pv)
    if len(progress_values) >= 3:
        # 最近3条是否递增
        if progress_values[-1] > progress_values[-2] > progress_values[-3]:
            momentum_score = 0.1  # 上升势头
        elif progress_values[-1] < progress_values[-2]:
            momentum_score = 0.0  # 下降势头
    
    # 4. 连续失败惩罚（0 或 -0.15）：只看明确的负向关键词
    fail_kw = ['失败', '❌', 'error', 'err', 'failed', 'stuck']
    last_3_entries = [e.get("entry", "") for e in recent[-3:]]
    failure_count = sum(1 for e in last_3_entries if any(kw in e for kw in fail_kw))
    fail_penalty = 0.15 if failure_count == 3 else 0.0
    
    # 5. 完成奖励（+0.1）：任何条目达到 100%
    completion_bonus = 0.1 if any(_parse_progress(e.get("entry", "")) == 100 for e in recent) else 0.0
    
    health = 0.4 + success_score + progress_score + momentum_score - fail_penalty + completion_bonus
    return min(1.0, max(0.0, round(health, 3)))


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
    _mark_dirty()

    return {
        "question": question,
        "health": health,
        "consecutive_low": consecutive_low + 1,
        "advice": _advice_for_health(health),
    }


def _advice_for_health(health: float) -> str:
    if health < HEALTH_DANGER_THRESHOLD:
        return "【危险】健康度过低，建议：降低目标难度，先完成最小可测试单元"
    elif health < 0.5:
        return "【偏低】建议：拆解任务，减少每次心跳的工作量，确保有可交付的进展"
    elif health < HEALTH_PUSH_THRESHOLD:
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


def _prune_log(state: dict):
    """日志裁剪到最近20条，防止文件膨胀"""
    if len(state.get("log", [])) > 20:
        state["log"] = state["log"][-20:]
        _mark_dirty()

def _dedup_projects(state: dict):
    """项目列表写入时去重（按名称）"""
    seen = set()
    result = []
    for p in state.get("projects", []):
        if p["name"] not in seen:
            seen.add(p["name"])
            result.append(p)
    if len(result) < len(state.get("projects", [])):
        state["projects"] = result
        _mark_dirty()

def _build_status_update(state: dict, health: float, action: str, blindspots: list, driver: dict) -> str:
    """
    生成人类可读的状态叙述（借鉴 Cursor Agent Status Update Spec）。
    格式：[态势] 背景 + 关键信号
    """
    task = state.get("current_task") or {}
    task_name = task.get("task", "无活跃任务")
    progress = task.get("progress_pct", 0)
    turn = driver.get("turn_index", 0)
    blindspot_count = len(blindspots)
    last_interval = driver.get("rhythm", {}).get("last_interval_minutes")

    if action == "reflect":
        if health < 0.3:
            reason = "健康度过低（<0.3），连续遇阻"
        elif blindspot_count > 0:
            reason = f"发现 {blindspot_count} 个潜在盲点"
        else:
            reason = "健康度低迷，进入反思"
        return f"[反思] {reason}。任务「{task_name}」（进度 {progress}%）"

    elif action == "push_forward":
        bs_note = f" | 盲点 {blindspot_count} 个待查" if blindspot_count > 0 else ""
        return f"[推进] 健康度 {health:.2f}，状态良好，可挑战更多。任务「{task_name}」（{progress}%）{bs_note} | 第 {turn} 轮"

    else:  # continue
        bs_note = f" | 盲点 {blindspot_count} 个" if blindspot_count > 0 else ""
        interval_note = f" | 间隔 {last_interval:.1f}min" if last_interval else ""
        return f"[继续] 健康度 {health:.2f}。任务「{task_name}」（{progress}%）{bs_note}{interval_note} | 第 {turn} 轮"


def _build_drive_summary(state: dict, health: float, action: str, blindspots: list, driver: dict) -> dict:
    """
    生成结构化摘要（借鉴 Cursor Agent Summary Spec）。
    包含：本次完成、推测、待确认、健康分项指标。
    """
    task = state.get("current_task") or {}
    log = state.get("log", [])[-3:]
    patterns = driver.get("patterns", [])[-5:]
    blindspot_details = [b.get("detail", "") for b in blindspots[:3]] if blindspots else []

    # 推测：分析最近日志
    inferred = []
    if log:
        for entry_dict in reversed(list(log)):
            entry = entry_dict.get("entry", "")
            if any(kw in entry for kw in ["完成", "✅", "success", "done"]):
                inferred.append(f"正向进展：{entry[:40]}")
                break
        for entry_dict in reversed(list(log)):
            entry = entry_dict.get("entry", "")
            if any(kw in entry for kw in ["失败", "❌", "error", "stuck"]):
                inferred.append(f"阻力信号：{entry[:40]}")
                break

    # 待确认：盲点 + 低进度项目
    pending = []
    for bs in blindspot_details:
        pending.append(f"盲点待查：{bs[:50]}")
    for proj in state.get("projects", []):
        if proj.get("status") == "active" and proj.get("progress_pct", 0) < 20:
            pending.append(f"项目「{proj.get('name','?')}」刚启动（{proj.get('progress_pct')}%）")

    return {
        "completed": {
            "action": action,
            "health": round(health, 3),
            "turn": driver.get("turn_index", 0),
            "current_task": task.get("task"),
            "progress_pct": task.get("progress_pct", 0),
        },
        "inferred": inferred if inferred else ["状态平稳，无明显异常"],
        "pending_confirmation": pending if pending else ["无需待确认事项"],
        "health_breakdown": {
            "turn_index": driver.get("turn_index", 0),
            "patterns_count": len(patterns),
            "blindspots_count": len(blindspots),
            "last_interval_minutes": driver.get("rhythm", {}).get("last_interval_minutes"),
        },
    }


def drive():
    """
    心跳自驱力主循环（v2）。
    新增：status_update（人类可读进度叙述）+ summary（结构化摘要）。
    返回 dict（含向后兼容字段 + v2 新字段）。
    """
    state = _load_state()

    # ── Lifecycle Hook: 加载上一会话上下文 ──────────────────────
    prev_context = load_session_context()

    # 初始化 driver 子状态
    if "patterns" not in state.get("driver", {}):
        state.setdefault("driver", {})["patterns"] = []
    if "consecutive_low" not in state.get("driver", {}):
        state.setdefault("driver", {})["consecutive_low"] = 0

    # 轮次计数器（来自 Honcho capture hook 启发）
    driver = state.setdefault("driver", {})
    driver["turn_index"] = driver.get("turn_index", 0) + 1
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    driver["last_turn_time"] = now_str

    # EMA 工作节奏追踪（来自 AgentHandover 启发）
    last_drive_time = driver.get("last_drive_time")
    if last_drive_time:
        try:
            last_dt = datetime.strptime(last_drive_time, "%Y-%m-%d %H:%M:%S")
            now_dt = datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")
            interval_minutes = (now_dt - last_dt).total_seconds() / 60.0
            rhythm = driver.setdefault("rhythm", {})
            prev_avg = rhythm.get("avg_interval_minutes")
            if prev_avg is not None:
                rhythm["avg_interval_minutes"] = round(prev_avg * 0.7 + interval_minutes * 0.3, 2)
            else:
                rhythm["avg_interval_minutes"] = round(interval_minutes, 2)
            rhythm["last_interval_minutes"] = round(interval_minutes, 2)
            _mark_dirty()
        except Exception:
            pass
    driver["last_drive_time"] = now_str

    _mark_dirty()

    health = calc_health(state)
    state["driver"]["last_health"] = health
    state["driver"]["last_check_time"] = now_str

    reflect_result = None
    action = "continue"

    if should_reflect(health):
        reflect_result = trigger_reflection(state.get("driver", {}))
        action = "reflect"
    elif health >= HEALTH_PUSH_THRESHOLD:
        action = "push_forward"
        state["driver"]["consecutive_low"] = 0

    # 自动记录学习模式（用 _is_success 严格判断，防重复）
    log = state.get("log", [])
    if log:
        last_entry = log[-1].get("entry", "")
        last_entry_hash = hash(last_entry)
        prev_hash = driver.get("last_log_entry_hash")
        if last_entry_hash != prev_hash:
            is_ok = _is_success(last_entry)
            driver.setdefault("patterns", []).append({
                "type": "success" if is_ok else "failure",
                "context": last_entry[:50],
                "time": now_str
            })
            driver["patterns"] = driver["patterns"][-20:]
            driver["last_log_entry_hash"] = last_entry_hash
            _mark_dirty()

    # 主动探测盲点（无外部反馈时的自我发现问题）
    blindspots = _probe_blindspots(state)
    if blindspots:
        state["driver"]["blindspots"] = blindspots
        state["driver"]["last_blindspot_check"] = now_str

    _prune_log(state)
    _dedup_projects(state)

    # WAL Protocol: 记录本次探索摘要
    state["driver"]["last_exploration"] = {
        "action": action,
        "health": round(health, 3),
        "time": now_str,
    }

    # ── 提案评分 + 选择最优动作（原只在 CLI 调用，现集成到 drive） ───────
    if action != "reflect":
        proposals = propose(state)
        best = select_best_action(proposals, driver)
        state["next_action"] = best.get("description", "待定")
        # 存储完整提案供执行层使用（包含 tags、score 等元数据）
        state["_best_proposal"] = best
        _mark_dirty()

    _save_state(state)

    # ── v2 新增 ──────────────────────────────────────
    status_update = _build_status_update(state, health, action, blindspots, driver)
    summary = _build_drive_summary(state, health, action, blindspots, driver)

    result = {
        # 向后兼容字段
        "action": action,
        "health": round(health, 3),
        "reflect": reflect_result,
        "turn_index": driver.get("turn_index", 0),
        "current_task": (state.get("current_task") or {}).get("task"),
        "next_action": state.get("next_action"),
        # v2 新字段
        "status_update": status_update,
        "summary": summary,
        # Lifecycle Hook: 加载的上一会话上下文
        "prev_session": prev_context,
    }
    # 在返回前保存会话上下文（跨会话持久化）
    save_session_context(state, result)
    return result


def get_driver_status() -> dict:
    s = _load_state()
    d = s.get("driver", {})
    return {
        "health": d.get("last_health", None),
        "consecutive_low": d.get("consecutive_low", 0),
        "last_check": d.get("last_check_time", "从未"),
        "last_reflect": d.get("last_reflect_time", "从未"),
        "pattern_count": len(d.get("patterns", [])),
        "last_blindspot_check": d.get("last_blindspot_check", "从未"),
        "blindspot_count": len(d.get("blindspots", [])),
        "turn_index": d.get("turn_index", 0),
        "last_turn_time": d.get("last_turn_time", "从未"),
        "rhythm_avg_minutes": d.get("rhythm", {}).get("avg_interval_minutes"),
        "last_interval_minutes": d.get("rhythm", {}).get("last_interval_minutes"),
    }


# ==================== VFM 评分体系 ====================
# ==================== 任务自动拆解 ====================

def _extract_steps(task_name: str) -> list[str]:
    t = task_name.lower()
    if any(kw in t for kw in ['发布', '上传', 'publish', 'upload', 'push']):
        return [f"准备「{task_name}」所需的材料与环境",
                f"执行「{task_name}」的核心操作",
                f"验证「{task_name}」的结果是否正确",
                f"收尾并更新状态为完成"]
    if any(kw in t for kw in ['创建', '开发', 'build', 'create', '实现']):
        return [f"规划「{task_name}」的实现方案",
                f"构建核心代码/文件",
                f"测试并修复问题",
                f"完成并整理产出"]
    if any(kw in t for kw in ['研究', '探索', 'research', 'explore', '分析']):
        return [f"调研「{task_name}」的相关资料",
                f"深入分析核心问题",
                f"提炼结论与产出",
                f"归档到 Obsidian / 记忆系统"]
    if any(kw in t for kw in ['修复', 'fix', 'debug', '解决', '调试']):
        return [f"定位「{task_name}」的根本原因",
                f"实施修复方案",
                f"验证修复是否有效",
                f"沉淀教训到经验库"]
    if any(kw in t for kw in ['整理', '归档', 'organize', 'sync', '同步']):
        return [f"清点「{task_name}」的现有资产",
                f"按结构分类整理",
                f"验证整理结果",
                f"更新索引和引用路径"]
    return [f"明确「{task_name}」的具体目标",
            f"执行核心步骤",
            f"验证执行结果",
            f"收尾并更新状态"]

def _decompose_task(state: dict) -> list[dict]:
    task = state.get("current_task") or {}
    task_name = task.get("task", "")
    progress = task.get("progress_pct", 0)
    if not task_name:
        return []
    steps = _extract_steps(task_name)
    step_size = 100.0 / len(steps)
    proposals = []
    for i, step in enumerate(steps):
        sub_task_name = f"[{i+1}/{len(steps)}] {step}"
        proposals.append({
            "description": sub_task_name,
            "expected_delta_health": 0.12,
            "tags": ["subtask", task_name[:20]],
            "parent_task": task_name,
            "step_index": i + 1,
            "total_steps": len(steps)
        })
    return proposals


def _audit_self_driver() -> list[dict]:
    """
    代码审计层：分析 self_driver.py 自身，发现具体改进点。
    借鉴 GPT Engineer 的"先分析再改进"思路。
    """
    import ast
    proposals = []
    path = "/home/node/.openclaw/workspace/skills/clawmind/scripts/self_driver.py"
    try:
        with open(path) as f:
            tree = ast.parse(f.read())
    except Exception:
        return proposals

    # 1. 收集所有定义的函数名
    defined_funcs = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined_funcs.add(node.name)

    # 2. 检查 CLI 专用函数（只在 __main__ 分支调用）
    cli_only_funcs = {"get_driver_status", "select_best_action"}
    for func in cli_only_funcs & defined_funcs:
        proposals.append({
            "description": f"[代码审计] {func}() 只在 CLI 调用，建议集成到 drive() 主循环",
            "expected_delta_health": 0.05,
            "tags": ["audit", "refactor", "cli"],
            "audit_finding": f"function_never_in_drive",
        })

    # 3. 检查 drive() 是否有硬编码阈值
    drive_func = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "drive"), None)
    if drive_func:
        # 寻找 magic number 0.7（健康度阈值）
        for node in ast.walk(drive_func):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                if 0.6 <= node.value <= 0.8:
                    proposals.append({
                        "description": "[代码审计] drive() 中发现硬编码阈值，建议提取为常量 HEALTH_THRESHOLD",
                        "expected_delta_health": 0.03,
                        "tags": ["audit", "refactor", "health"],
                        "audit_finding": "hardcoded_threshold",
                    })
                    break

    # 4. 检查是否有 TODO/FIXME/HACK 注释
    try:
        with open(path) as f:
            content = f.read()
        for line_no, line in enumerate(content.split("\n"), 1):
            # 排除审计代码自身的字符串字面量（false positive）
            if "for kw in" in line or "in [\"TODO\"" in line:
                continue
            for kw in ["TODO", "FIXME", "HACK", "XXX"]:
                if kw in line and not line.strip().startswith("#"):
                    proposals.append({
                        "description": f"[代码审计] 发现 {kw} 注释（第{line_no}行）: {line.strip()[:50]}",
                        "expected_delta_health": 0.04,
                        "tags": ["audit", "tech-debt"],
                        "audit_finding": f"{kw}_comment",
                    })
                    break
    except Exception:
        pass

    # 5. 检查日志裁剪阈值是否硬编码
    if "_prune_log" in defined_funcs:
        try:
            with open(path) as f:
                content = f.read()
            if "[-20:]" in content or "[-50:]" in content:
                proposals.append({
                    "description": "[代码审计] 发现日志裁剪硬编码（-20/-50），建议提取为 MAX_LOG_SIZE",
                    "expected_delta_health": 0.02,
                    "tags": ["audit", "refactor"],
                    "audit_finding": "magic_number_in_log",
                })
        except Exception:
            pass

    return proposals[:5]  # 最多5个审计提案，避免冗余


def _extract_research_proposals() -> list[dict]:
    """
    从最近的自主研究笔记中提取可执行提案。
    打通 self_research → propose() pipeline 的关键环节。
    """
    proposals = []
    try:
        import glob
        memory_dir = "/home/node/.openclaw/workspace/memory"
        if not os.path.exists(memory_dir):
            return proposals
        # 读取最新的研究笔记（最多读最近3个）
        files = sorted(glob.glob(os.path.join(memory_dir, "auto-exploration-*.md")))
        if not files:
            return proposals
        recent = files[-3:]
        research_insights = []
        for fpath in recent:
            with open(fpath) as f:
                content = f.read()
            # 提取项目名和共性描述
            lines = content.split("\n")
            for line in lines:
                if line.startswith("**方向**") or line.startswith("- **"):
                    research_insights.append(line.strip())
        if research_insights:
            proposals.append({
                "description": f"分析近期研究成果：{' '.join(research_insights[:2])}",
                "expected_delta_health": 0.07,
                "tags": ["research", "analysis"],
            })
    except Exception:
        pass
    return proposals


def _get_remaining_steps(state: dict) -> list[tuple]:
    """
    返回当前任务未完成的 [n/m] 步骤列表。
    每个元素: (description, expected_delta_health)
    """
    task = state.get("current_task", {})
    task_name = task.get("task", "") or ""
    done_steps = set(state.get("_done_steps", []))

    all_steps = [
        ("[1/4] 明确「ClawMind v2 规划实施」的具体目标", 0.12),
        ("[2/4] 执行核心步骤", 0.12),
        ("[3/4] 验证执行结果", 0.12),
        ("[4/4] 收尾并更新状态为完成", 0.12),
    ]

    remaining = []
    for desc, delta in all_steps:
        m = re.match(r"^\[(\d+)/\d+\]\s*", desc)
        if m and m.group(1) not in done_steps:
            remaining.append((desc, delta))
    return remaining


def propose(state: dict, context: str = "") -> list[dict]:
    """
    根据当前状态和上下文生成改进提案列表。
    每个提案包含: description, expected_delta_health, tags
    """
    proposals = []
    task = state.get("current_task") or {}
    task_name = task.get("task", "无任务") or "无任务"
    progress = task.get("progress_pct", 0) or 0
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

    # 3. 拆解提案（如果进度卡住 → 真实生成子任务）
    if progress < 30:
        sub_tasks = _decompose_task(state)
        if sub_tasks:
            proposals.extend(sub_tasks)
        else:
            proposals.append({
                "description": "拆解当前任务为更小的可测试单元",
                "expected_delta_health": 0.08,
                "tags": ["planning", "task"]
            })

    # 3b. 步骤推进（进度 > 30 时，继续推进未完成步骤）
    # 即使进度较高，也要保证未完成步骤能被选中
    if progress >= 30 and progress < 100:
        remaining_steps = _get_remaining_steps(state)
        for step_desc, delta in remaining_steps:
            proposals.append({
                "description": step_desc,
                "expected_delta_health": delta,
                "tags": ["continue", "task"]
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

    # 6. 盲点修复提案（如果有未解决的盲点）
    blindspots = state.get("driver", {}).get("blindspots", [])
    if blindspots:
        for b in blindspots[:2]:  # 最多加2个
            detail = b.get("detail", "")[:50]
            proposals.append({
                "description": f"修复盲点: {detail}",
                "expected_delta_health": 0.06,
                "tags": ["blindspot", "fix"]
            })

    # ── 研究层：从自主研究笔记中提取可执行提案 ────────────────
    research_proposals = _extract_research_proposals()
    proposals.extend(research_proposals)

    # ── 代码审计层：分析自身源码，生成具体改进提案 ────────────────
    audit_proposals = _audit_self_driver()
    proposals.extend(audit_proposals)

    # ── 过滤：排除已完成步骤 [n/m]，避免重复执行 ────────────────
    done_steps = state.get("_done_steps", [])
    if done_steps:
        proposals = [
            p for p in proposals
            if not any(
                re.match(rf"^\[({s})/\d+\]\s*", p.get("description", ""))
                for s in done_steps
            )
        ]

    # 过滤：排除过于宽泛的推进类提案（如果已有具体步骤在队列）
    has_step_proposals = any(re.match(r"^\[\d+/\d+\]\s*", p.get("description", "")) for p in proposals)
    if has_step_proposals:
        proposals = [p for p in proposals if not p.get("description", "").startswith("推进当前任务")]

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
        _mark_dirty()
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

    # 步骤提案（[n/m] 格式）优先：未完成的子步骤应优先执行
    desc = proposal.get("description", "")
    if re.match(r"^\[\d+/\d+\]\s*", desc):
        score *= 1.3  # 步骤提案优先级提高 30%

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
        state = _load_state()
        driver = state.get("driver", {})
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
