#!/usr/bin/env python3
"""
研究步骤执行器
由 research_daemon.py 调用
每次触发推进一个研究子步骤
"""

import sys, os, json, base64, urllib.request, datetime as dt

WORKSPACE = "/home/node/.openclaw/workspace"
STATE_FILE = f"{WORKSPACE}/state/current_state.json"
GITHUB_TOKEN = open(f"{WORKSPACE}/.github_token").read().strip()
OWNER, REPO = "numuly", "sisi-log"

def api(url, data=None, method="GET"):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    if data:
        data = json.dumps(data).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def upload_to_github(content, path, msg):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    sha = None
    try:
        sha = api(url)["sha"]
    except:
        pass
    data = {"message": msg, "content": base64.b64encode(content.encode()).decode()}
    if sha:
        data["sha"] = sha
    api(url, data=data, method="PUT")
    return True

def run():
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    with open(STATE_FILE) as f:
        state = json.load(f)

    active = [p for p in state.get("projects", []) if p.get("status") == "active"]
    if not active:
        print("NO ACTIVE PROJECT")
        return

    project = active[0]
    project_name = project.get("name", "")
    next_action = project.get("next_action", "")

    # github-exploration 类型 → 委托给 self_research.py
    if "github-exploration" in project_name:
        import subprocess
        result = subprocess.run(
            [sys.executable, "/home/node/.openclaw/workspace/projects/self-improvement-research/self_research.py"],
            capture_output=True, text=True, timeout=60
        )
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    print(f"  {line}")
        if result.returncode != 0:
            print(f"  self_research error: {result.stderr[:100]}")
        return

    # 确定下一个要写的文件
    next_file = None
    for path in [
        "exploration/self-improvement/05-three-layer-architecture.md",
        "exploration/self-improvement/06-self-reflection-design.md",
        "exploration/self-improvement/07-reflexion-deep-dive.md",
    ]:
        try:
            api(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}")
        except:
            next_file = path
            break

    if not next_file:
        print("ALL RESEARCH FILES COMPLETE")
        project["status"] = "completed"
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return

    # 根据文件路径生成内容
    if "05-three-layer" in next_file:
        content = f"""# 5. 自我改进的三层架构

> 生成时间：{ts}
> 状态：自动生成

## 三层架构概述

基于 Reflexion / proactive-agent / ClawMind 的分析，提出三层自我改进架构：

| 层次 | 名称 | 解决的问题 | 代表机制 |
|------|------|-----------|---------|
| L1 | 错误不重复 | 上次犯的错不再犯 | self-improving-agent |
| L2 | 状态驱动 | 没有方向时找到方向 | ClawMind drive() |
| L3 | 主动发现 | 主动发现未知问题 | 缺失（研究方向） |

## L1：错误不重复（被动层）

触发条件：发生了错误/纠正
机制：记忆 recall 应用

## L2：状态驱动（半自动层）

触发条件：健康度低于阈值
机制：VFM 评分 drive() 决策 行动

## L3：主动发现（自动层） 研究空白

触发条件：没有任何触发条件——主动探测
机制：未知，需要设计

## L3 的设计挑战

核心问题：没有错误发生，怎么知道哪里有问题？

可能的路径：
1. 盲点探测：主动搜索"我不知道什么"
2. 一致性检查：让 agent 验证自己的假设
3. 外部基准对比：和同类系统比较发现自己
4. 模式异常检测：在 patterns 中发现异常模式

## 下一步

设计一个 L3 的原型机制
"""
        project["next_action"] = "设计 L3 主动发现机制原型"

    elif "06-self-reflection" in next_file:
        content = f"""# 6. L3 主动发现机制设计

> 生成时间：{ts}
> 状态：自动生成

## 核心问题

如何让 agent 在没有任何外部反馈的情况下，主动发现自身可能存在的缺陷？

## 灵感来源

人类有三个认知层次：
- 知道自己知道（清醒）
- 知道自己不知道（学习）
- 不知道自己不知道（盲点）← L3 要解决的

## 设计方案：盲点日志

### 机制

每次 drive() 被调用时，额外生成一条盲点探测日志：

```
盲点探测结果：
- 当前假设：...
- 可能的问题：...
- 需要验证的：...
```

### 实现思路

在 drive() 中加入 probe_blindspots() 调用：

```python
def probe_blindspots(state):
    issues = []
    # 1. 检查成功率是否虚高
    recent = state["log"][-10:]
    if all(p.get("type") == "success" for p in recent):
        issues.append("近期全部成功，可能是评估标准太宽松")
    # 2. 检查长时间无进展的项目
    for proj in state.get("projects", []):
        if proj.get("status") == "active":
            last = proj.get("last_log_time", "")
            if last and days_ago(last) > 7:
                proj_name = proj.get("name", "未知")
                issues.append("项目" + proj_name + "一周无进展")
    return issues
```

### 下一步

1. 实现 probe_blindspots() 函数
2. 在 drive() 中加入盲点探测调用
3. 把探测结果写入 patterns
4. 测试在无外部反馈情况下是否能主动发现问题
"""
        project["next_action"] = "实现 probe_blindspots 函数并测试"

    else:  # 07-reflexion-deep-dive
        content = f"""# 7. Reflexion 核心机制精读

> 生成时间：{ts}
> 状态：自动生成

## Reflexion 的三个核心组件

### 1. Actor（执行器）
使用现有的 CoT / ReAct agent 执行任务

### 2. Evaluator（评估器）
根据任务类型判断成功或失败：
- 外部评估：使用规则/测试验证
- 语义评估：LLM 判断输出质量

### 3. Self-Reflection（自我反思）
这是 Reflexion 的核心创新：

当任务失败时，agent 生成一段文本反思：
上次尝试：描述上次做了什么
失败原因：分析为什么失败
下次改进：具体改进建议

这个反思被加入下次尝试的 context，继续尝试。

## 对 ClawMind 的启发

ClawMind 可以借鉴 Reflexion 的 self-reflection 机制：

1. 保留当前的健康度评估（类似 Evaluator）
2. 在 drive() 返回的结果中加入反思文本
3. 下次 drive() 调用时，把上次反思作为 context 参考

## 融合方案

```python
def self_reflect(state, last_result):
    fail_kw = ["失败", "错误", "无法", "没有完成"]
    is_fail = any(kw in last_result for kw in fail_kw)
    if is_fail:
        return "上次健康度下降，原因分析：" + last_result + "。建议：调整策略。"
    else:
        return "上次执行顺利，当前健康度良好。继续保持。"
```

这是 L2 + L3 融合的起点。
"""
        project["next_action"] = "实现 probe_blindspots 函数并测试"

    upload_to_github(content, next_file, f"docs: auto research step — {next_file}")
    print(f"WROTE {next_file}")

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"DONE: {project.get('next_action', '')}")

if __name__ == "__main__":
    run()
