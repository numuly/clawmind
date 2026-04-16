# ClawMind v2 验证方案

## 验证目标
确认 v2 核心功能正常工作：
1. drive() 正确调用 select_best_action() ✓
2. 提案通过 VFM 评分选优 ✓
3. task 类提案生成代码/分析 ✓
4. 研究洞察汇入提案系统 ✓

## 验证方法
```bash
cd /home/node/.openclaw/workspace
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from self_driver import drive, propose, select_best_action, _load_state
state = _load_state()
print('health:', state['driver']['last_health'])
print('turn:', state['driver']['turn_index'])
proposals = propose(state)
print('proposals:', len(proposals))
best = select_best_action(proposals, state['driver'])
print('best:', best['description'], 'score:', best['score'])
"
```

## 预期结果
- 健康度 >= 0.5
- 提案数 >= 6（包含研究提案）
- 最高分提案不是"无事可做"
