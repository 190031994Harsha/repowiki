# Reproduction Guide

Two tiers, honestly labeled:

- **Smoke test** (2 repos, requests + click): **~10 minutes, ~$0.10**. Verifies the whole
  pipeline works.
- **Full evaluation** (12 repos × 2 modes): **~40 minutes wall with 4 parallel workers,
  ~$0.60**. Run sequentially it's ~2.5 hours — don't do that.

All on the default model (deepseek via OpenRouter); frontier slugs cost ~$2–5 more.

## 1. Prerequisites

| Requirement | Version used | Notes |
|---|---|---|
| Python | 3.12.10 | 3.11+ fine; stdlib `ast` does the heavy lifting — **no native deps** |
| git | 2.54 | for cloning URL inputs |
| LLM endpoint | OpenRouter | any OpenAI-compatible base URL works (`REPOWIKI_BASE_URL`) |
| OS | Windows 11 (git-bash) | pure Python; macOS/Linux identical |

## 2. Setup

```bash
git clone <this-repo> && cd repowiki
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # put your OPENROUTER_API_KEY in it
```

## 3. Smoke test (no LLM, no cost, ~5 seconds)

```bash
python -m repowiki index https://github.com/psf/requests
```

Expected: the deterministic repo map — module clusters, per-file symbols, import edges.
If this works, ingest+parse+index are healthy.

## 4. One wiki (the video path, ~2–5 min, ~$0.02)

```bash
python -m repowiki generate https://github.com/psf/requests --mode advanced
```

Expected tail output:

```
[repowiki] wrote N pages to examples/requests-advanced
[repowiki] M LLM calls, $0.0x, ~200s, citations: ~150 (0 unresolved)
[repowiki] trajectory: trajectories/requests-advanced-<ts>.jsonl
```

Open `examples/requests-advanced/overview.md` — every citation renders as
`` `path/file.py:12-40` `` and clicking through in any markdown viewer lands on real code.

## 5. The full evaluation (12 repos × 2 modes)

```bash
python -m evals.parallel_runner 4     # 4 parallel workers; the 12-repo list is built in
cat evals/report.md
```

Expected: a summary table plus per-repo **baseline vs advanced** comparison tables. The
submitted numbers are committed at `evals/report.md` with model slug + date; your numbers
will wobble slightly (provider-side nondeterminism at temperature 0) but the *direction
and rough size* of every delta should reproduce.

## 6. Trajectories

```bash
python -c "from repowiki.trajectory import render_file; print(render_file('<path>.jsonl'))"
```

Every run logs every LLM call (prompt/response/tokens/cost), every citation resolution,
and every repair cycle.

## If it doesn't run

- `openai.AuthenticationError` → key missing/invalid in `.env`.
- `git clone` failures → network or private repo; use a local path instead.
- A page full of "unresolved citation" → you're on a non-Python repo with an exotic layout;
  run `--mode baseline` as the fallback path and check `trajectories/` for resolver rejects.
- Nothing is written outside `examples/`, `evals/`, `trajectories/` and the temp clone
  cache. Delete those to reset completely.
