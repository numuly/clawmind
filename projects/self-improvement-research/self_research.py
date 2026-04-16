#!/usr/bin/env python3
"""
self_research.py — ClawMind 自主研究模块
在无活跃项目时也能运行，利用记忆系统主动探索

研究策略：
1. 读 memory/ 最近日记，找未完成的探索方向
2. 读 memory_db，找最近关注的领域
3. 如果都没有 → 搜索 GitHub trending，找有价值的 self-improving agent 项目
4. 将研究发现写入 memory/日记 + 更新 state
"""

import os, sys, json, time, re
from datetime import datetime, timezone, timedelta

STATE_FILE = "/home/node/.openclaw/workspace/state/current_state.json"
MEMORY_DIR = "/home/node/.openclaw/workspace/memory"
MEMORY_DB = "/home/node/.openclaw/workspace/my_memory_core/memory.db"
OWNER = "numuly"
REPO = "sisi-log"

def log(msg):
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def set_project_active(name: str, next_action: str):
    """创建或激活一个研究项目（保持兼容，但 self_research.py 不再调用）"""
    pass  # 已废弃，daemon 不依赖项目状态

def read_recent_memories(n=5):
    """读最近 N 条记忆"""
    memories = []
    if not os.path.exists(MEMORY_DIR):
        return memories
    for entry in sorted(os.listdir(MEMORY_DIR), reverse=True)[:n]:
        if not entry.endswith(".md"):
            continue
        path = os.path.join(MEMORY_DIR, entry)
        try:
            with open(path) as f:
                memories.append({"file": entry, "content": f.read()[-2000:]})
        except:
            pass
    return memories

def search_memory_db(query: str, limit=3):
    """搜索记忆数据库"""
    if not os.path.exists(MEMORY_DB):
        return []
    try:
        import sqlite3
        conn = sqlite3.connect(MEMORY_DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT task_intent, key_insight FROM experiences WHERE task_intent LIKE ? OR key_insight LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        )
        rows = cur.fetchall()
        conn.close()
        return [{"task": r["task_intent"], "insight": r["key_insight"]} for r in rows]
    except Exception as e:
        return []

def github_search(keyword: str):
    """搜索 GitHub 项目"""
    import urllib.request
    TOKEN = open("/home/node/.openclaw/workspace/.github_token").read().strip()
    # 用更宽泛的日期范围（最近3个月）避免结果过少
    import urllib.parse
    q = urllib.parse.quote(keyword)
    url = f"https://api.github.com/search/repositories?q={q}+pushed:%3E2026-01-01&sort=stars&order=desc&per_page=5"
    req = urllib.request.Request(url, headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return [(d["full_name"], d["description"] or "", d["stargazers_count"]) 
                     for d in data.get("items", [])[:5]]
    except Exception as e:
        return []

MAX_FILE_SIZE_MB = 1

def _rotate_if_needed(path: str):
    """如果文件超过阈值，归档并新建"""
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb >= MAX_FILE_SIZE_MB:
            archive_dir = os.path.join(MEMORY_DIR, "exploration-archive")
            os.makedirs(archive_dir, exist_ok=True)
            archive_name = f"{os.path.basename(path).replace('.md', '')}_{datetime.now(timezone(timedelta(hours=8))).strftime('%H%M%S')}.md"
            archive_path = os.path.join(archive_dir, archive_name)
            os.rename(path, archive_path)
            return True
    return False


def write_research_note(topic: str, content: str):
    """写研究笔记到 memory/，文件过大时自动归档"""
    date = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    filename = f"auto-exploration-{date}.md"
    path = os.path.join(MEMORY_DIR, filename)
    _rotate_if_needed(path)
    with open(path, "a") as f:
        f.write(f"\n---\n## 自主探索: {topic}\n")
        f.write(f"_自动生成 {datetime.now(timezone(timedelta(hours=8))).strftime('%H:%M:%S')}_\n\n")
        f.write(content + "\n")
    # 写入后再次检查大小（防止单次写入就超过限制）
    _rotate_if_needed(path)

def decide_research_topic():
    """
    决定研究主题。
    策略：基于时间轮转 + 记忆引导
    """
    # 直接从 fallback 候选轮转，不从笔记提取（笔记是自我产出，会造成反馈循环）
    fallback_candidates = [
        ("self-improving AI agent", "self-improving AI agent"),
        ("autonomous coding agent", "autonomous coding agent"),
        ("agent memory system", "agent memory system"),
        ("agent skill creation", "agent skill creation"),
        ("context compression LLM", "context compression LLM"),
        ("multi-agent collaboration", "multi-agent collaboration"),
        ("open-source AI agent", "open-source AI agent"),
        ("tool calling agent", "tool calling agent"),
    ]
    idx = int(time.time()) // 180 % len(fallback_candidates)
    search_term = fallback_candidates[idx][0]
    topic_label = fallback_candidates[idx][0]

    return topic_label, search_term

def run():
    log("启动自主研究")

    # 决定研究主题
    topic_label, search_term = decide_research_topic()
    log(f"选择主题: {topic_label} (搜索: {search_term})")

    # 搜索 GitHub
    results = github_search(search_term)
    if not results:
        log("GitHub 搜索无结果，尝试替代主题")
        results = github_search("self-improving agent autonomous")

    if results:
        lines = []
        # 提取共性模式
        descs = [r[1] for r in results[:3] if r[1]]
        common = descs[0][:80] if descs else ""
        lines.append(f"**方向**: {search_term}")
        lines.append(f"**共性**: {common}\n")
        for r in results[:3]:
            lines.append(f"- **{r[0]}** ({r[2]}⭐): {r[1][:100] if r[1] else '(无描述)'}")
        lines.append("")
        lines.append("**洞察**: ")
        lines.append("")
        content = "\n".join(lines)
        write_research_note(topic_label, content)
        log(f"写入研究笔记: {topic_label} | {len(results)} 个项目")
    else:
        log("无法获取 GitHub 数据，搜索其他方向")
        # 写一个待机笔记
        note = f"## 自主探索结果\n\n未能获取有效数据。主题: {topic_label}\n"
        write_research_note("exploration-failure", note)

if __name__ == "__main__":
    run()
