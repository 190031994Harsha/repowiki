# Agent trajectories

One JSONL file per generation run. Each records, in order: the planner's page plan,
every LLM call (system prompt, user prompt, response, tokens, cost, latency), every
citation resolution (accepted or rejected), every repair cycle, and the final stats.

**Read one:**

```bash
python -c "from repowiki.trajectory import render_file; print(render_file('trajectories/<file>.jsonl'))"
```

**Naming:** `<repo>-<mode>-<yyyymmdd>-<hhmmss>.jsonl`; eval runs are prefixed `eval-`.

**Good examples to start with:**
- `eval-requests-advanced-*.jsonl` — clean run, symbol citations resolving, no repairs needed
- `eval-click-advanced-*.jsonl` — shows repair cycles firing on decorator-heavy symbols
- `eval-fastapi-advanced-*.jsonl` — the challenging metaprogramming case: planner +
  coverage backfill + consolidation all visible

The *coding-agent* trajectory (the Claude Code session that built this repository) is
disclosed separately per the submission form — it is not a JSONL here because it is the
session transcript itself.
