# Judge: deepseekv4 (deepseek/deepseek-v4-pro)
_Role: skeptical-reviewer · 2026-08-31 05:36 UTC_

# repowiki — Technical Review

**Verdict:** The core cite-by-symbol engineering is clever, but the evaluation overstates improvement by measuring a feature the baseline doesn’t attempt, hides a missing baseline on the “challenging” repo, and reports regressions in coverage and readability that the authors conveniently sidestep.

---

## 2. Score breakdown (Measured Improvement / 15)

| Component | Weight | Score | Evidence |
|---|---|---|---|
| **Experimental design** | 4 | 0.5 | The evaluation compares “baseline” (file-level citations only) with “advanced” (symbol-level + line ranges). The headline metric “citations with exact line ranges” jumps from 0.00 to 0.75 **by construction** — the baseline can’t produce line ranges, so the delta is not a *measured improvement* but a *feature addition*. Real improvement on shared metrics is ~0.04 in validity, ~0.12 in symbol coverage, while **module coverage drops** (e.g., anyio 1.00→0.75, flask 1.00→0.90) and **readability plummets** (httpx 0.87→0.00, packaging 0.66→0.00). The evaluation is a “horse race” where the advanced system is scored on a different track. The missing baseline run for **fastapi** (the “challenging” case) further undermines the design. |
| **Baseline fairness** | 3 | 1.0 | The baseline is a reasonable strawman: fixed-template, repo-map-only, no file contents. It’s a valid “naïve” approach. However, the unfair part is that the baseline is **not asked to produce line ranges**, so the improvement metric is rigged. A fair baseline would at least attempt to output line numbers (e.g., via a simple regex/grep) and then be scored on correctness. The current comparison is like claiming a bicycle is 100% better than a car at “having handlebars.” |
| **Metrics appropriateness** | 3 | 1.5 | The chosen metrics (citation validity, depth, coverage, link health, readability) are sensible. The problem is that **citation_depth** (fraction of citations with line ranges) is treated as a primary quality measure, equating “more line ranges” with “better documentation.” That’s a leap — a wiki with 100% line-range citations but poor prose is not better. The scorer also doubles as a self-evaluation tool, which risks circularity, though the code (quality.py) appears externally deterministic. Still, the readability metric is a crude sentence-length heuristic, and the 0.00 scores suggest the advanced pages are garbled, which the authors never address. |
| **Significance of improvement** | 3 | 1.0 | The actual, non-tautological improvement is tiny: **citation validity improves by 0.04 on average** (0.92→0.96). Symbol coverage improves by 0.12 (0.35→0.47). These are small gains, and they come with **module coverage regressions** (avg ~0.05 drop) and **readability collapses** (3 repos hit 0.00). The cost quadruples and time more than doubles. The net benefit is marginal at best; the authors’ own numbers show the advanced system is often *worse* for the reader. |
| **Reproducibility & rigor** | 2 | 1.0 | The REPRODUCE.md is clear, and the code is provided. However, the eval report contains **19 runs instead of 20** (fastapi baseline is missing). The authors claim “10 repos × 2 modes = 19 runs” but never explain why baseline was skipped on the most important repo. This omission is a red flag. The temperature-0 runs are claimed to wobble slightly, but provider-side nondeterminism could still produce different numbers; no error bars or multiple runs are reported. The changelog admits multiple measurement bugs that were fixed *after* the full eval, yet the final numbers are presented as one clean run — no evidence of a re-run from scratch. |

**Total Measured Improvement score: 5.0 / 15** — the evaluation is competent in parts but fundamentally misrepresents the nature of the improvement, omits a critical baseline, and ignores regressions.

---

## 3. The 3 most likely reasons this loses

1. **The headline improvement is a category error.**  
   The jump from 0.00 to 0.75 in “citations with line ranges” is not a measured improvement; it’s a feature the baseline never attempted. Judges will see through this immediately. The real, shared-metric improvement is ~0.04 — an unimpressive gain that doesn’t offset the cost and the regressions. The submission reads like a marketing trick, not a rigorous evaluation.

2. **Missing baseline on the challenging repo and embarrassing regressions.**  
   The fastapi baseline is mysteriously absent; the advanced system on fastapi delivers **4% module coverage, 19% symbol coverage, and a readability of 0.00**. The “challenging” case actually demonstrates the advanced system’s failure. The baseline might have been even worse, but we’ll never know — the omission undermines the entire 10-repo claim.

3. **The advanced system is not a clear win for the end user.**  
   The produced wikis are less readable, sometimes miss modules, and cost 4× more money and 2.5× more time. The only tangible benefit is line-range citations, which are nice but not game-changing. The hackathon rubric rewards “measured improvement” — meaning the system has to be *better* in a way that matters. This submission doesn’t prove that the advanced wiki is more useful; it only proves that the authors can build a resolver.

---

## 4. The 3 highest-leverage fixes

1. **Re-run the fastapi baseline, and restructure the evaluation to measure *documentation quality* on a common yardstick.**  
   Add a human-evaluation or task-based metric (e.g., “how many questions can a new engineer answer using the wiki?”) or at least a LLM-based judge that scores both outputs on correctness, completeness, and clarity. The current number-only comparison is too easy to game. The fastapi omission must be fixed; if the baseline is too slow/costly to run, that’s a finding worth reporting.

2. **Fix the readability and coverage regressions before claiming improvement.**  
   The 0.00 readability scores for httpx and packaging suggest the advanced pages are broken (maybe too many code snippets, no prose). The module coverage drops because the planner caps at 12 pages and skips non-trivial modules. These are solvable: adjust the planner’s fallback, improve the prose-generation prompt, and verify that the advanced system never produces a worse wiki than the baseline on *any* metric. Right now, the advanced is a sidegrade, not an upgrade.

3. **Add a competitive baseline that *also* produces line ranges.**  
   A simple regex-based approach (e.g., grep for `def foo` and cite `file:lineno`) would give a non-zero `citation_depth` and make the improvement meaningful. Showing that the cite-by-symbol resolver beats regex on accuracy, coverage, and repair would be a genuine measured improvement. Without that, the delta is just a design choice.

---

## 5. What would make this WIN

A winning submission would demonstrate that the advanced wiki **dramatically improves a real downstream task** — e.g., engineers answer a set of onboarding questions 2× faster, or the wiki catches drift in a CI pipeline with measurable accuracy gains. The cite-by-symbol machinery is a solid foundation, but the current evaluation collapses under scrutiny. To win, the authors would need to:

- Run a controlled user study with at least 10 engineers, showing that the advanced wiki leads to faster, more accurate code comprehension.
- Show that the line-range citations are not just present but *actionable* — e.g., linking to the exact code in a live IDE, and that this reduces errors in follow-up tasks.
- Provide a fair baseline that tries to be helpful (at least file-level citations with some heuristics) and show that the advanced system is **unambiguously better** across all metrics, including cost and readability.
- Handle the fastapi challenge with grace: the static call graph is a known limitation; they should have a fallback that still produces a useful wiki (e.g., dynamic analysis via AST instrumentation or a hybrid approach). Without that, the system fails on exactly the kind of codebase a judge would test.

Right now, the project is a polished demo of a deterministic citation resolver — interesting, but not a prize-winning “measured improvement.”