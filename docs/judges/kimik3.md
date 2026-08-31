# Judge: kimik3 (moonshotai/kimi-k3)
_Role: skeptical-reviewer · 2026-08-31 05:41 UTC_

# Review: repowiki — Measured Improvement Critique

**Reviewer stance:** Hostile. I assume the numbers are wrong until the artifact proves otherwise. I reviewed every file provided; several referenced artifacts (`baseline.py`, `trajectories/*.jsonl`, `evals/report.json`, the tail of `advanced.py`, which is truncated mid-sentence in the bundle) were not inspectable, and that itself is noted below.

---

## 1. Verdict

repowiki is genuinely solid citation *plumbing* wrapped around a measurement that mostly proves a tautology — the headline "+0.75 citations with line ranges" is guaranteed by construction (baseline cannot emit line ranges, advanced attaches them automatically) — while the metrics where advanced actually *loses* (module coverage, readability, click's 0.78 validity) are quietly omitted from the README table, and the single "challenging" repo ships without a baseline, so nothing in this bundle demonstrates improved grounding, only improved citation *formatting*.

---

## 2. Score breakdown: Measured Improvement — **6 / 15**

| Sub-criterion | Score | Evidence |
|---|---|---|
| Does the metric measure grounding? | 1/4 | No. It measures *resolvability*, and barely that independently. See below. |
| Baseline fairness & attribution | 1/3 | Baseline isn't a strawman, but 5 variables change at once; zero ablations. |
| Eval set adequacy | 1.5/3 | 10 repos ✓, but all-Python, all popular/clean, challenging repo has no comparison arm. |
| Robustness / hostile re-run survivability | 1/3 | 1 run/cell, no pinned SHAs, no variance, single model; key deltas within noise. |
| Honesty of reporting | 1.5/2 | Changelog and full per-repo tables are unusually candid; README table is curated. |

### The headline number is definitional, not measured

`citation_depth`: baseline emits `[path]` only → rendered as `` `path` `` → depth **0.00, forever, by construction**. Advanced emits `[[sym:x]]` → resolver renders `path:a-b` → depth ~0.75 automatically. The +0.75 "improvement" is the observation that *the system that can emit line ranges emits line ranges*. It is a conformance check on output syntax wearing a delta's clothing. A judge who has seen this trick — and hackathon judges have — discounts the entire table on contact.

### The eval grades the system with the system's own grader

- The advanced pipeline rejects unresolvable citations and repairs them (≤3 attempts, and note: **after the third attempt the page ships anyway**, unresolved cites rendered as `*(unresolved citation)*` — so the README's "the emitted wiki *cannot* contain a citation the tree doesn't support" is false per `_gen_with_repair`'s loop structure).
- Then `quality.py` scores validity using **the same `resolve()` function** that did the generation-time filtering. A systematic resolver bug (and the changelog admits to several — src-layout aliasing, fence blindness, positional replacement) corrupts generation *and* scoring in the same direction, invisibly. There is no independent re-parse, no held-out ground truth, no human spot-check of even ten citations.
- Validity of a rendered range = `1 <= a <= b <= n+5`. The **+5 lines of EOF slack** exists only to absorb index/scorer inconsistency — a fudge factor sitting inside the score.
- Nothing anywhere checks that the cited symbol *supports the claim*. An LLM citing a real-but-irrelevant symbol scores as a perfectly valid, deep, symbol-level citation. The README concedes "the verifier checks anchors, not truth" — but then sells "grounded claims" on the cover. The eval measures something that *correlates* with grounding only when the model picks the right symbol, and symbol-pick accuracy is entirely unmeasured.
- `symbol_coverage` counts a symbol "covered" if its **simple name appears as a substring anywhere in the wiki** (`q.split(".")[-1] in all_text`). `get`, `run`, `close`, `parse` are "documented" if English prose mentions them. Both arms are inflated; the +0.12 delta is noise riding on a broken denominator.
- `link_health` is 1.00 in 17/19 rows because `_page_links` mechanically appends 8 valid "See also" links to every page. A metric that cannot move is decoration.

### Attribution: nothing isolates the claimed mechanism

The narrative credits the repair loop and cite-by-symbol. But baseline→advanced changes **five things simultaneously**: context access, citation syntax, planner, repair loop, extras. There is no advanced-minus-repair arm, no advanced-with-file-citations arm. The one mechanism-independent delta, validity +0.04 mean, has per-repo spread **−0.18 (click) to +0.14 (records)** with n=9, one run per cell, temp 0 with acknowledged provider nondeterminism. A hostile re-run plausibly flips the sign. The authors' own changelog ("if the measurement is wrong, the improvement claim is worthless") states the standard their ablation-free design fails.

### The challenging repo has no baseline

README: "10 repos × 2 modes (**20 runs**)." Report header: "**19 runs**." The missing row is **fastapi-baseline** — the designated challenging case, the most important cell in the comparison. Unexplained anywhere. Meanwhile fastapi-advanced shows **module_coverage 0.04** despite 37 pages and a claimed 12-module cap — which (a) suggests the cap in the code only limits *backfill*, not the planner (`cap = max(0, 12 - len(planned_modules))`), contradicting changelog [6]'s description, and (b) smells like a planner-page-naming vs scorer-name-matching artifact of exactly the type they fixed five times already. Nobody investigated, because with no baseline row there was no anomaly to notice. Also: the generator backfills at ≥50 lines while the scorer counts modules ≥30 lines — a threshold mismatch that manufactures advanced's coverage regressions on anyio (0.75), httpx (0.80), flask (0.90).

### The README table cherry-picks by omission

The README comparison shows: depth, validity, symbol coverage, cost, time. It omits module coverage (advanced ≤ baseline on 4 of 9 repos), readability (advanced worse on 6 of 9, including **0.87→0.00 on httpx and 0.66→0.00 on packaging** — either the prose degraded or the sentence-length heuristic is junk; both readings damage the submission), and click's 0.78 validity regression, which receives no failure analysis anywhere. Credit where due: the full per-repo tables *are* committed, so this is curation, not concealment — but it's curation that a judge will find in one click, and it retroactively taints the changelog's hard-earned honesty signal.

### Minor but telling

- REPRODUCE.md's "full evaluation" command contains a literal `<starter-repo-url>` placeholder; the actual 10-repo list with URLs/**commit SHAs is never pinned** — fatal for a project whose entire pitch is reproducibility, since HEAD moves.
- Changelog [5]: "0.81 → **~0.99 expected**" — the fix's outcome was written before the re-run.
- All 10 eval repos are Python — the one language with real AST support; the JS/TS/Go/Rust/Java claims are evaluated zero times.
- Single model (deepseek-v3-0324). The repair-bound, cost, and validity claims are untested against a weaker or stronger model.
- README claims wikis "can't silently drift"; DESIGN.md's own future-work section proposes a drift-check CI because they can and do.

---

## 3. The 3 most likely reasons this loses

1. **The headline improvement is tautological.** +0.75 line-range depth is a property of the output schema, not a measured gain; the residual honest deltas (+0.04 validity, +0.12 substring-coverage) are within run-to-run noise and confounded five ways. Judges pattern-match this instantly.
2. **"Grounding" is asserted, never measured.** Same resolver generates and grades; zero claim-support verification; substring coverage; +5-line fudge; 19/20 runs with the challenging repo's baseline missing. A hostile re-read finds no independent evidence that any cited line range supports its sentence.
3. **The curated README table versus the full report.** Advanced *loses* on module coverage (incl. 0.04 on the flagship repo), readability (two 0.00s), and validity on click — all absent from the summary. The submission's best asset was its honesty narrative; the cherry-pick spends it.

---

## 4. The 3 highest-leverage fixes

1. **Measure claim support, not just resolvability.** Hand-check (or blind-judge with the cited snippet, judged independently of the generator's code) a sample of ~50 citations: does this span support this sentence? Report claim-support rate next to validity. Re-implement the scorer to re-parse the repo independently of the generation-time index, pin repo SHAs, and delete the +5 slack and substring coverage rule.
2. **Complete and de-confound the comparison.** Run fastapi-baseline; add two ablation arms (advanced-no-repair; advanced-file-level-citations) so the repair loop and cite-by-symbol each get an attributable delta; 3 repeats per cell with mean±range. Fix the ≥30/≥50 threshold mismatch and explain click's 0.78.
3. **Re-frame honestly.** Demote depth to a design property, lead the README with the full metric set *including the regressions*, and reconcile absolute claims ("cannot contain," "can't drift") with the code's actual bounded-repair behavior. The candor is already 80% there — finish it and it becomes the differentiator.

---

## 5. What would make this WIN

The gap between this and first prize is the gap between *plumbing that works* and *evidence that the plumbing matters*. A winning submission adds: **(a)** a ground-truth grounding eval — a labeled set of repo claims with known-correct citations, scoring precision/recall of citation *relevance*, proving the metric measures grounding rather than correlating with it; **(b)** an end-to-end utility measure — answer real questions about each repo using only the generated wiki vs. the baseline wiki vs. raw-repo access, comparing answer accuracy (this measures the actual product promise: faster onboarding); **(c)** ablations with error bars isolating each design decision, on pinned inputs, across ≥2 models including a weak one that stress-tests the repair bound; **(d)** one genuinely adversarial eval repo — non-Python, docstring-free, dynamically dispatched — where the honest failure modes are shown and quantified rather than relegated to a limitations section; and **(e)** a third-party-auditable trail: trajectories a judge can spot-check against emitted pages in minutes. Today's submission proves the citations resolve. The winner proves the claims are true — and that a stranger inheriting the codebase is actually better off.