# Judge Panel v3 Synthesis — empirical review (execute, diff, recompute)

**Panel (empirical lenses):** gpt-5.6-sol (adversarial execution — ran PoCs), deepseek-v4-pro (baseline-fairness diff-audit), gemini-3.1-pro (blind reproducibility walkthrough), kimi-k3 (absolute-claim audit), claude-opus-5 (line-by-line engineering review), grok-4.6 (video script), qwen3-max-thinking (defend-or-retract the v1 87).
**What changed from v2:** judges *executed code, recomputed numbers, walked the README blind, and read the source line-by-line* instead of reasoning about it. The findings are correspondingly more concrete and more damning.

---

## The 3 that would lose the submission (all confirmed by execution or recompute)

### V3-A. The baseline is a strawman — it never sees the code. (fairness / deepseek)
The single most damaging finding. The baseline gets only a repo map (file names + symbol *names*); the advanced gets full file contents + symbol tables with signatures. So the "improvement" in depth/validity/coverage is largely *because the advanced sees code*, not because of the repair/verify machinery the changelog credits.
- deepseek: "a strawman that denies the LLM the very input that makes documentation possible."
- The fix is one change: give the baseline the same file contents, keep everything else simple.
- **Until this is fixed, the entire measured-improvement claim (15 points) is unsound.**

### V3-B. The README's eval command is broken as written. (repro / gemini)
A judge following REPRODUCE.md hits:
1. `python -m evals.runner --repos ...,<starter-repo-url>` — placeholder + module mismatch (the 12-repo run used `evals/parallel_runner.py`, not `evals.runner`).
2. Missing `python-dotenv` in requirements.txt — the `.env` file is never loaded, so the first LLM call 401s.
3. Missing `pytest` for the Makefile `test` target.
4. "10 repos" in one section, "12" in another.
- gemini scored Reproducibility **8/15** purely from the docs. This is the cheapest 7 points available.

### V3-C. ~30 concrete bugs in the deterministic core. (linereview / opus-5)
A staff-level merge review found real, verifiable bugs, several of which corrupt the metrics the whole submission rests on:
- **quality.py `b <= n + 5`** treats 5 lines past EOF as valid → inflates validity. (high)
- **module_coverage slug mismatch**: `module.name.replace('/','-')` on already-dotted names → systematic near-zero coverage. (high, silent)
- **symbol_coverage is substring search** — `get`/`run` match "target"/"running" → coverage ≈ inflated to ~1.0. (high)
- **parse.py relative imports** lose package context (`from . import x`) → dependency edges silently vanish. (high)
- **parse.py nested functions** flatten to module level (dead `if False`) → qualname collisions, wrong line ranges. (high)
- **ast.parse only catches SyntaxError** — a file with NUL bytes (ValueError) crashes the whole index run. (crash)
- Plus ~24 more (unicode citations, off-by-one line counts, nondeterministic glob order, readability splitter, etc.)

## What v3 confirmed is now genuinely strong

- **exec / gpt-5.6-sol:** ran both v2 integrity PoCs against the current code — **both FIXED** (ambiguous same-file symbols and src/lib aliases now fail closed). The resolver teeth work.
- **win2 / qwen3-max (the v1 87 dissenter):** retracted-and-reaffirmed at **92/100**, explicitly *because* the v2 fixes landed. Their one remaining gap to 95+: **no measured-usefulness study** (onboarding QA task).

## Prioritized fix list (points per hour)

| # | Fix | Effort | Why |
|---|---|---|---|
| 1 | **Fair baseline**: give it file contents too | ~30 min | saves the entire 15-pt improvement claim |
| 2 | **Fix REPRODUCE**: real command, add python-dotenv+pytest to reqs, align 10/12 | ~20 min | 7 cheap reproducibility points |
| 3 | **quality.py metric integrity**: kill the +5 slack, fix symbol_coverage substring, fix module_coverage slug | ~45 min | the metrics ARE the submission |
| 4 | **parse.py robustness**: catch all ast exceptions, handle relative imports, nested qualnames | ~45 min | the grounding layer must not crash or drop edges |
| 5 | **Video**: move the verifier-rejection moment to <75s (video judge's one change) | edit | the only non-interchangeable beat |

## The one thing that makes it WIN (consensus across v1+v2+v3)

**A measured-usefulness study**: N engineers answer onboarding questions with baseline vs advanced wiki, measure time-to-correct-answer. All three panels independently named this as the gap between "clever system" and "first prize." It converts the claim from "citations resolve" to "a new engineer is faster." Everything else is plumbing.
