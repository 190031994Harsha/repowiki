# Agent-Use Disclosure

This project uses AI agents in **two distinct roles**, both disclosed with trajectories.

## 1. Coding agent — how this repository was built

**Tool:** Claude Code (Anthropic), running interactively under human direction.

**What it did:** authored the deterministic layer (ingest, parsers, index, citations,
scorer), both generators, the eval harness, and this documentation, across a single
working session on 2026-08-28. The human set the product direction, reviewed design
decisions, and ran the approval gates.

**Trajectory:** the full Claude Code session transcript is included in the submission
package (JSONL export), alongside the in-product trajectories below.

## 2. In-product agents — the LLM components of repowiki itself

repowiki's generators are LLM pipelines. Every call is logged: system prompt, user
prompt, response, token counts, cost, latency, and every citation-resolution and repair
event. Per-run files land in `trajectories/<repo>-<mode>-<ts>.jsonl`; render any of them:

```bash
python -c "from repowiki.trajectory import render_file; print(render_file('trajectories/<file>.jsonl'))"
```

**Models used in product runs:** recorded per-run in the trajectory (`model` field on
every `llm_call` event) and in `evals/report.md`. Development/eval default:
`deepseek/deepseek-chat-v3-0324` via OpenRouter, temperature 0.

**Agent boundaries:**
- Agents **never mutate the analyzed repository** — ingest is read-only (clones land in a
  temp cache), and no tool exists that writes to the target tree.
- Agents **never see secrets** — all content is scanned and redacted (`repowiki/secrets.py`)
  before prompt construction; findings are reported per run.
- Agents **cannot fabricate citations that survive** — the deterministic resolver rejects
  any symbol/path not in the index, and the scorer re-validates everything emitted.

## Human checkpoints

Model choice, the cite-by-symbol design decision, the scope decision (no embeddings), and
final submission are human calls. Generation and evaluation are automated but every score
is recomputed deterministically from artifacts a judge can inspect directly.
