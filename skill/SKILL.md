---
name: mind
description: Self-evolving AI agent engine with health-driven motivation, VFM proposal scoring, and semantic experience memory. Triggers on: self-evolution, autonomous driving, health tracking, VFM decision-making, goal management, experience recall.
---

# mind — Self-Evolving Agent Engine

An AI agent's "mind": the unified system of memory and self-motivation. **Memory** lets it learn from past mistakes without repeating them. **Self-driver** keeps it moving forward autonomously.

Inspired by Hermes Agent's Self-Evolving Agent Memory mechanism — automatic experience extraction (intent + path + key_insight) with semantic clustering.

## Core Architecture

```
mind/
├── self_driver.py       ← Drive: health + VFM scoring + reflection
├── state_manager.py     ← State: project / task / log management
├── quality_score.py      ← Scoring: 5-dimension briefing quality
└── memory/
    └── memory_core.py   ← Memory: experience recall (remember / recall)
```

**Closed loop**:
```
drive() → propose() generate proposals → score_action() VFM rank → execute
                                                           ↓
                              recall() retrieve ← remember() deposit
```

---

## Health System

### `calc_health(state) → float`

```
health = 0.4 + success*0.25 + progress*0.2 + momentum*0.1 - fail_penalty*0.15 + completion*0.1
```

| Component | Range | Description |
|-----------|-------|-------------|
| Base | 0.4 | Starting point |
| Success rate | 0~0.25 | Ratio of successful entries in last 5 logs |
| Progress | 0~0.2 | Current task completion % |
| Momentum | 0~0.1 | +0.1 if progress rising across last 3 entries |
| Fail penalty | 0 or -0.15 | -0.15 if last 3 entries all failures |
| Completion | 0 or +0.1 | +0.1 if any entry shows 100% completion |

### Health Thresholds

| Health | Status | Action |
|--------|--------|--------|
| < 0.3 | Danger | Reduce scope, split into smallest testable units |
| 0.3~0.4 | Low | Reduce workload per cycle, ensure deliverable progress |
| 0.4~0.7 | OK | Maintain rhythm, focus on current step |
| ≥ 0.7 | Good | Push forward, take on more |

---

## VFM Proposal Scoring

### `propose(state, context="") → list[dict]`

Generate improvement proposal list with `description`, `expected_delta_health`, `tags`.

**Typical proposals**:

| Proposal | Trigger | delta |
|----------|---------|-------|
| Push current task | Active task | 0.1 |
| Learn from experience | Recent success log | 0.05 |
| Split task → sub-tasks | Progress < 30% | 0.12 (per sub-task) |
| Check skill updates | Always included | 0.03 |
| Deposit knowledge | Recent core insight | 0.04 |

When progress < 30%, `propose()` calls `_decompose_task()` which automatically breaks the task into 3-4 concrete sub-tasks based on keyword patterns:
- **publish/upload** → prepare → execute → verify → conclude
- **create/build** → plan → build → test → complete
- **research/explore** → research → analyze → conclude → archive
- **fix/debug** → locate → fix → verify → deposit lesson
- **organize/sync** → inventory → classify → verify → update index
- **default** → define goal → execute → verify → conclude
### `score_action(proposal, driver) → float`

**VFM formula**: `Value × Feasibility × Momentum × 100`

- **Value**: Higher delta proposals worth more when health is low
- **Feasibility**: Boosted by past success patterns, reduced by consecutive lows
- **Momentum**: Health ≥0.6 → 0.9, ≥0.4 → 0.6, <0.4 → 0.3

### `select_best_action(proposals, driver) → dict`

Returns top-scored proposal with full ranking table.

---

## Experience Memory

### `remember(experience, source, tags) → None`

Deposit a task result or insight into experience DB.

```python
remember("Docker network conflict solved — must specify --subnet explicitly",
         source="task", tags=["docker", "debug"])
```

### `recall_experiences(query, tags, limit) → list[dict]`

Retrieve relevant experiences semantically.

```python
results = recall_experiences("docker", limit=3)
for r in results:
    print(r['task_intent'], '|', r['key_insight'][:60])
```

---

## State Management

```python
from state_manager import push_project, set_task, add_log

push_project("project-name", "goal description", "active")
set_task("task name", 2, 5, "next action")
add_log("heartbeat 10:00: completed module A")
```

---

## CLI Usage

```bash
# Main loop
python3 self_driver.py

# Engine status
python3 self_driver.py status

# Proposal scoring report
python3 self_driver.py propose
```

---

## Reflection Questions (triggered when health < 0.4)

1. Where is the current task stuck? Is it a logic problem or execution problem?
2. Is there past experience I can apply here?
3. Is this step actually worth doing, or am I avoiding something more critical?
4. If I had to solve this tomorrow, what's the minimum I should finish today?
5. Have I broken this problem down small enough?

---

## File Index

| File | Purpose |
|------|---------|
| `scripts/self_driver.py` | Self-driver core |
| `scripts/state_manager.py` | State management |
| `scripts/quality_score.py` | Briefing quality scorer |
| `scripts/memory/memory_core.py` | Experience memory core |
| `references/state-manager.md` | state_manager full API |
| `references/vfm-design.md` | VFM scoring design details |
