#!/usr/bin/env python3
"""
auto_created_skill.py — ClawMind Skill 自创建引擎 v2.0
混合三代系统精华：

1. Hermes Agent（NousResearch）：prompt 引导自觉
   → "5+ tool calls / 棘手错误 / 非平凡工作流 → 保存为 Skill"
2. AgentHandover（sandroandric）：自动观察 + Dwell 检测
   → 行为持续出现才记录
3. Honcho（plastic-labs）：分级推理
   → 复杂任务用更深度推理

触发条件（满足任一即创建）：
- Hermes: 复杂任务（5+ tool calls）
- Hermes: 修复棘手错误
- Hermes: 发现非平凡工作流
- AgentHandover: 同一行为模式出现 DWELL_THRESHOLD 次
- AgentHandover: 错误恢复模式（同类错误再次出现时）
- 用户明确要求

SKILL.md 格式：agentskills.io 标准（含 YAML frontmatter）
"""

import os, json, re
from datetime import datetime
from typing import Optional

SKILLS_DIR = "/home/node/.openclaw/workspace/skills/auto_created/"
SKILL_MD_TEMPLATE = """---
name: {name}
description: {description}
version: 1.0.0
source: clawmind-auto-created
trigger:
{trigger_lines}
platforms: [macos, linux, windows]
metadata:
  clawmind:
    created_at: {created_at}
    improvement_count: {improvement_count}
    last_used: "{last_used}"
    created_from: "{created_from}"
---

# {display_name}

## 描述

{description}

## 触发条件

{trigger_md}

## 系统提示词

{prompt}

## 所需工具

{tools}

## 使用示例

{examples}

---

*此 Skill 由 ClawMind 自动创建（v2.0）*
*创建时间：{created_at} | 来源：{created_from}*
"""

# ==================== 触发条件常量 ====================
TOOL_CALL_THRESHOLD = 5       # Hermes: 5+ tool calls = 复杂任务
DWELL_THRESHOLD = 3           # AgentHandover: 同一模式出现3次
CONTEXT_COMPLEXITY = 300      # 上下文复杂度阈值（字符数）


# ==================== 数据结构 ====================

class AutoCreatedSkill:
    def __init__(self, name, trigger, prompt, tools, examples, created_from, description=""):
        self.name = name
        self.description = description
        self.trigger = trigger          # list of trigger strings
        self.prompt = prompt
        self.tools = tools
        self.examples = examples
        self.created_from = created_from
        self.improvement_count = 0
        self.last_used = None
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger,
            "prompt": self.prompt,
            "tools": self.tools,
            "examples": self.examples,
            "created_from": self.created_from,
            "improvement_count": self.improvement_count,
            "last_used": self.last_used,
            "created_at": self.created_at,
        }

    def to_markdown(self):
        """导出为 agentskills.io 标准的 SKILL.md 格式"""
        # 格式化触发条件
        trigger_lines = "\n".join(f"  - {t}" for t in self.trigger)
        trigger_md = "\n".join(f"- {t}" for t in self.trigger)
        examples_md = ""
        for i, ex in enumerate(self.examples, 1):
            examples_md += f"### 示例 {i}\n{ex.get('description', '')}\n````\n{ex.get('prompt', '')}\n````\n\n"
        if not examples_md:
            examples_md = "暂无示例\n"

        tools_md = ", ".join(self.tools) if self.tools else "无特定工具"

        return SKILL_MD_TEMPLATE.format(
            name=self.name,
            description=self.description or f"自动创建的 Skill，来源：{self.created_from}",
            display_name=self.name.replace("-", " ").replace("_", " ").title(),
            trigger_lines=trigger_lines,
            trigger_md=trigger_md,
            prompt=self.prompt,
            tools=tools_md,
            examples=examples_md,
            created_at=self.created_at,
            created_from=self.created_from,
            improvement_count=self.improvement_count,
            last_used=self.last_used or "从未使用",
        )

    def save(self) -> str:
        """保存 Skill 到 SKILL.md + meta.json"""
        slug = self.name.replace(" ", "-").lower()
        skill_path = os.path.join(SKILLS_DIR, slug, "SKILL.md")
        meta_path = os.path.join(SKILLS_DIR, slug, "meta.json")

        os.makedirs(os.path.dirname(skill_path), exist_ok=True)

        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        with open(skill_path, 'w', encoding='utf-8') as f:
            f.write(self.to_markdown())
        return skill_path

    def increment_use(self):
        """记录一次使用，用于改进计数"""
        self.last_used = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.improvement_count += 1


# ==================== Skill 创建引擎 v2.0 ====================

class SkillCreationEngine:
    """
    混合三代系统精华的 Skill 自创建引擎

    触发检测（任一满足即触发）：
    1. Hermes 复杂任务（5+ tool calls）
    2. Hermes 棘手错误修复
    3. Hermes 非平凡工作流发现
    4. AgentHandover Dwell 检测（3+ 重复行为）
    5. AgentHandover 错误恢复模式
    6. 用户明确要求（user_requested=True）
    """

    def __init__(self, state: dict = None):
        self.state = state or {}
        # 行为历史：Dwell 检测用
        self.behavior_history: list[dict] = []
        # 错误历史：错误恢复模式检测用
        self.error_history: list[dict] = []
        # 已创建的 Skill 名称（避免重复创建）
        self.created_skills: set[str] = set()
        # 加载已存在的 Skill
        self._load_existing_skills()

    def _load_existing_skills(self):
        """扫描 SKILLS_DIR，加载已创建的 Skill 名称"""
        if not os.path.exists(SKILLS_DIR):
            return
        for entry in os.listdir(SKILLS_DIR):
            skill_dir = os.path.join(SKILLS_DIR, entry)
            if os.path.isdir(skill_dir) and os.path.exists(os.path.join(skill_dir, "meta.json")):
                try:
                    with open(os.path.join(skill_dir, "meta.json")) as f:
                        meta = json.load(f)
                        self.created_skills.add(meta.get("name", entry))
                except:
                    pass

    def record_behavior(self, behavior: dict):
        """
        记录一个行为模式，供 Dwell 检测使用
        behavior: {"type": "task_pattern", "key": "...", "context": "..."}
        """
        self.behavior_history.append(behavior)
        # 只保留最近 50 条
        if len(self.behavior_history) > 50:
            self.behavior_history = self.behavior_history[-50:]

    def record_error(self, error: dict):
        """记录一个错误，供错误恢复模式检测使用"""
        self.error_history.append(error)
        if len(self.error_history) > 30:
            self.error_history = self.error_history[-30:]

    def check_should_create(self, task_info: dict) -> tuple[bool, str]:
        """
        判断是否应该创建 Skill
        返回: (should_create, reason)
        """
        # 0. 用户明确要求 → 直接创建
        if task_info.get("user_requested"):
            return True, "user_requested"

        # 1. Hermes: 复杂任务（5+ tool calls）
        tool_calls = task_info.get("tool_calls", 0)
        if tool_calls >= TOOL_CALL_THRESHOLD:
            return True, f"complex_task({tool_calls} tool calls)"

        # 2. Hermes: 棘手错误修复
        if task_info.get("error_recovered"):
            return True, "error_recovery"

        # 3. Hermes: 非平凡工作流（上下文复杂度）
        context = task_info.get("context", "")
        if len(context) >= CONTEXT_COMPLEXITY and task_info.get("multi_step"):
            return True, f"nontrivial_workflow(len={len(context)})"

        # 4. AgentHandover: Dwell 检测（同一行为模式 3+ 次）
        key = task_info.get("behavior_key", "")
        if key:
            recent_same = [
                b for b in self.behavior_history[-15:]
                if b.get("key") == key
            ]
            if len(recent_same) >= DWELL_THRESHOLD:
                # 避免重复创建同一个 Skill
                skill_name = f"auto-{re.sub(r'[^a-zA-Z0-9_-]', '_', key)[:40]}"
                if skill_name not in self.created_skills:
                    return True, f"dwell_pattern({len(recent_same)}x {key})"

        # 5. AgentHandover: 错误恢复模式（同类错误再次出现后成功解决）
        error_type = task_info.get("error_type", "")
        if error_type:
            prev_errors = [e for e in self.error_history[-10:] if e.get("type") == error_type]
            if len(prev_errors) >= 2 and task_info.get("resolved"):
                return True, f"error_recovery_pattern({error_type})"

        return False, ""

    def create_skill(self, task_info: dict) -> Optional[AutoCreatedSkill]:
        """
        从任务信息中创建 Skill
        """
        should_create, reason = self.check_should_create(task_info)
        if not should_create:
            return None

        name = task_info.get("task", "untitled")
        context = task_info.get("context", "")
        behavior_key = task_info.get("behavior_key", "")

        # 生成安全的 Skill 名称（agentskills.io: 小写 + 字母数字 + 连字符）
        if behavior_key:
            safe_name = re.sub(r'[^a-zA-Z0-9-]', '-', behavior_key.lower())[:50].strip("-")
        else:
            safe_name = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())[:50].strip("-")

        # 避免重复
        full_name = f"auto-{safe_name}"
        if full_name in self.created_skills:
            return None

        # 生成触发条件列表
        triggers = [f"task_type:{name}"[:60]]
        if task_info.get("error_recovered"):
            triggers.append(f"error_recovery:{task_info.get('error_type', 'unknown')}"[:60])
        if task_info.get("behavior_key"):
            triggers.append(f"behavior:{behavior_key}"[:60])
        if task_info.get("tool_calls", 0) >= TOOL_CALL_THRESHOLD:
            triggers.append(f"complexity:{task_info.get('tool_calls')}tool_calls"[:60])

        # 生成系统提示词（参考 Hermes SKILLS_GUIDANCE）
        prompt = self._generate_prompt(task_info)

        skill = AutoCreatedSkill(
            name=full_name,
            description=task_info.get("description", f"自动创建的 Skill，来源：{name}"),
            trigger=triggers,
            prompt=prompt,
            tools=task_info.get("tools_used", []),
            examples=task_info.get("examples", []),
            created_from=task_info.get("task", ""),
        )

        skill.save()
        self.created_skills.add(full_name)

        return skill

    def _generate_prompt(self, task: dict) -> str:
        """生成 Skill 系统提示词（参考 Hermes SKILLS_GUIDANCE）"""
        name = task.get("task", "")
        context = task.get("context", "")
        tools = task.get("tools_used", [])
        error_type = task.get("error_type", "")

        base = f"你擅长处理以下任务类型：{name}\n\n"

        if error_type:
            base += f"相关错误类型：{error_type}\n"
            base += "遇到此类错误时：\n"
            base += "1. 先分析错误信息\n"
            base += "2. 检查相关配置文件\n"
            base += "3. 按既定方案修复\n"
            base += "4. 验证修复结果\n"
        else:
            base += f"背景信息：{context[:400]}\n\n"
            base += "当遇到类似任务时：\n"
            base += "1. 理解任务目标\n"
            base += "2. 识别需要的工具" + (f"（{', '.join(tools[:5])}）" if tools else "") + "\n"
            base += "3. 制定执行计划\n"
            base += "4. 按计划执行\n"
            base += "5. 验证结果\n"

        if task.get("dwell_count", 0) >= DWELL_THRESHOLD:
            base += f"\n此任务类型出现频率较高（Dwell: {task.get('dwell_count')}次），已验证有效方案可直接复用。\n"

        return base

    def patch_skill(self, skill_name: str, old_string: str, new_string: str) -> bool:
        """
        修补现有 Skill（参考 Hermes skill_manage(action='patch')）
        返回是否成功
        """
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(skill_md):
            return False

        try:
            with open(skill_md, encoding='utf-8') as f:
                content = f.read()

            if old_string not in content:
                return False

            # 更新 meta.json 的 improvement_count
            meta_path = os.path.join(skill_dir, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    meta = json.load(f)
                meta["improvement_count"] = meta.get("improvement_count", 0) + 1
                with open(meta_path, 'w') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)

            content = content.replace(old_string, new_string)
            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except:
            return False


# ==================== 快速创建接口 ====================

def create_from_conversation(conversation: dict) -> Optional[AutoCreatedSkill]:
    """
    从对话信息快速创建 Skill
    conversation: {"task": "...", "context": "...", "tool_calls": N, ...}
    """
    engine = SkillCreationEngine()
    return engine.create_skill(conversation)


# ==================== 用户模型（参考 Hermes USER.md）====================

USER_PROFILE_PATH = "/home/node/.openclaw/workspace/USER.md"

def update_user_profile(key: str, value: str):
    """
    更新用户画像
    参考 Hermes Agent 的 USER.md 机制
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## {timestamp} 更新\n- **{key}**: {value}\n"
    with open(USER_PROFILE_PATH, 'a', encoding='utf-8') as f:
        f.write(entry)


def get_user_profile() -> str:
    """读取用户画像"""
    try:
        with open(USER_PROFILE_PATH, encoding='utf-8') as f:
            return f.read()
    except:
        return ""


# ==================== 测试 ====================

if __name__ == "__main__":
    # 测试触发条件
    engine = SkillCreationEngine()

    # 测试1: Hermes 复杂任务（5+ tool calls）
    result1 = engine.check_should_create({
        "task": "修复 Docker 网络问题",
        "context": "Docker 容器网络冲突，需要重建网络...",
        "tool_calls": 7,
        "multi_step": True,
    })
    print(f"Test 1 (7 tool calls): should_create={result1[0]}, reason={result1[1]}")

    # 测试2: Dwell 检测
    for i in range(3):
        engine.record_behavior({"type": "task_pattern", "key": "docker-network-fix"})
    result2 = engine.check_should_create({
        "task": "修复 Docker 网络",
        "behavior_key": "docker-network-fix",
    })
    print(f"Test 2 (Dwell 3x): should_create={result2[0]}, reason={result2[1]}")

    # 测试3: 用户明确要求
    result3 = engine.check_should_create({
        "task": "写一个简单脚本",
        "user_requested": True,
    })
    print(f"Test 3 (user requested): should_create={result3[0]}, reason={result3[1]}")

    # 测试4: 创建 Skill
    skill = engine.create_skill({
        "task": "修复 Docker 网络问题",
        "context": "Docker 容器网络冲突，需要重建网络...",
        "description": "自动创建，来源：修复 Docker 网络问题",
        "tool_calls": 7,
        "multi_step": True,
        "tools_used": ["exec", "write"],
    })
    if skill:
        print(f"Skill created: {skill.name}")
        print(f"  saved to: {skill.save()}")
