# Judge: opus5 (anthropic/claude-opus-5)
_Role: rubrics-scorer · 2026-08-31 05:36 UTC_

# Critique: `repowiki` — micro1 Agentic Workflows Hackathon (Aug 2026)

## 1. Verdict

A genuinely good core idea (never let the model emit coordinates) wrapped in unusually honest process docs — undermined by a headline table that quietly drops the two metrics where the advanced system *loses*, a flagship correctness claim its own eval falsifies, and an evaluation that measures resolver self-agreement rather than whether any claim is actually true.

---

## 2. Score breakdown

| # | Criterion | Pts | Score | Evidence |
|---|---|---|---|---|
| 1 | Problem framing & user value | 15 | **10** | Sharp ICP ("the engineer who just inherited a codebase"), real bottleneck, and the read-only/secret-scan posture shows product thinking. But zero positioning against the obvious incumbents (DeepWiki, Cursor/Devin wikis, Sourcegraph) — a judge who knows the space will ask "why is this new?" and the bundle never answers. No user-facing artifact in the bundle either (see #4), so "value" is asserted, not shown. |
| 2 | Technical depth & grounding | 30 | **19** | The cite-by-symbol contract is the right architecture and articulated crisply in DESIGN.md; positional-replacement fix, code-fence exclusion, src-layout alias resolution, bounded repair loop are all real engineering. Three deductions, all serious: **(a)** README asserts "the emitted wiki *cannot* contain a citation the tree doesn't support" — `evals/report.md` shows click advanced at 0.78 validity, i.e. ~22% unresolved shipped as `*(unresolved citation)*` after the loop exhausts. The system fails *open*, not closed, contradicting its own thesis sentence. **(b)** `citation_validity` is computed by the same `resolve()` that generated the citation — it measures resolver self-consistency, not grounding. You concede this ("checks anchors, not truth") but then never measure truth, which is what the 30 points are for. **(c)** `symbol_coverage` credits a symbol if `q.split(".")[-1] in all_text` — a bare substring match anywhere on any page, including See-also lists and prose. That's not coverage, it's word-search, and it inflates the metric you use to claim +0.12. |
| 3 | Evaluation rigor | 20 | **12** | Ten repos, deterministic no-LLM-judge scorer, per-repo comparison tables, temp 0, model slug + date recorded — clearly above median effort. But: README says "20 runs," report says 19, and the missing run is **fastapi baseline** — so the deliberately-challenging repo has *no baseline-vs-advanced comparison at all*, and the aggregate means are computed over unequal sets. Advanced *loses* on citation validity in 3/9 paired repos (click −0.18, httpx −0.05, colorama −0.01), loses module coverage in 3/9 (anyio −0.25, httpx −0.20, flask −0.10), and loses readability in 5/9 including two 0.00 floors — **none of these three metrics appear in the README's headline table**, which shows only the metrics where advanced wins. That is selective reporting in a submission whose entire narrative is measurement honesty. Also: all ten eval repos are Python libraries despite advertised JS/TS/Java/Go/Rust support, single model, single seed, no variance bars. |
| 4 | Engineering quality & craft | 15 | **10** | `citations.py` / `index.py` / `quality.py` are clean, typed, well-commented, zero native deps — a judge can actually run this. Against: no tests anywhere in the bundle; `readability = 1.0 - min(abs(avg_sent - 18)/30, 1.0)` is a made-up proxy that returns 0.00 on real output (that's ≥48 words/sentence — almost certainly your sentence splitter choking on citation-dense prose, i.e. a fourth measurement bug of exactly the kind CHANGELOG [3][5][7] congratulate themselves for catching); in-run page generation is serial, so fastapi advanced takes **1720s / 29 minutes** for one wiki; magic constants (12 clusters, 30/50 lines, `+5` line slack) are unjustified. |
| 5 | Docs, reproducibility & agent disclosure | 15 | **13** | Best part of the submission. REPRODUCE.md has pinned versions, expected output, expected cost, expected runtime, *and* a "if it doesn't run" section — rare. AGENTS.md separates coding-agent from in-product-agent cleanly, with trajectories for both and explicit boundaries. CHANGELOG is evidence-linked iteration, not a diary. Docked for the internal inconsistencies (20 vs 19 runs; CHANGELOG [3]'s "symbol coverage 0.95 vs 1.00" sits next to a report showing 0.35 vs 0.47 with no note that these are different repos). |
| 6 | Presentation & insight | 5 | **3.5** | The hot take ("give judgment to the model and line numbers to the AST"; "the first hour of any 'the agent got worse' debugging should be spent on the harness") is earned by the changelog rather than asserted — genuinely memorable. But VIDEO_SCRIPT.md is referenced and absent, and the bundle contains **not one line of generated wiki output**. |
| | **Total** | **100** | **67.5** | Solid, well-documented, one real idea — but the honesty framing is louder than the honesty. |

---

## 3. The 3 most likely reasons this loses

1. **The headline table looks curated, and the per-repo tables prove it.** A judge reads "Citation validity 0.92 → 0.96 (+0.04)" then scrolls to click (0.96 → **0.78**) and readability (httpx 0.87 → **0.00**, packaging 0.66 → **0.00**) and realizes the README's five-row table is the subset where advanced wins. For a project whose differentiator is "validity is a measurement, not a hope," this is fatal — it converts your greatest strength into your loudest liability. The fix costs 20 minutes and you didn't take it.

2. **Grounding is 30 points and you measured the wrong thing.** Every number in the report answers "does this citation resolve?" — which is true by construction of your own resolver — and none answers "does the cited code support the sentence?" The CHANGELOG even records the failure mode ("FaultState enum — it's a class") that only a *support* check catches, then never builds one. First-prize submissions in a grounding-focused challenge will have sampled claims and reported precision against ground truth.

3. **The challenging case is a hole, not a highlight.** fastapi: module coverage **0.04**, no baseline pair, 1720s, and the only defense is prose in CHANGELOG [6]. The one repo designed to stress the system produced the worst number in the report and the least evidence. Right now it reads as "we ran the hard one and quietly excluded it from the comparison."

---

## 4. The 3 highest-leverage fixes

1. **Ship a claim-support eval (≈2 hours, worth ~+3–4).** Sample 30 emitted citations stratified across 5 repos; for each, paste the cited line range next to the sentence and label support / partial / contradicted — by hand, or by a cheap second-model judge that sees *only* the excerpt and the sentence. Report precision and the confusion cases. This converts "our verifier checks anchors, not truth" from a limitation into a measured number, and it's the single thing that separates you from every other citation-flavored submission.

2. **Publish the full comparison, regressions first (≈30 min, worth ~+2–3).** Put citation validity, module coverage, **and readability** in the README table, then write two sentences owning each regression: click's validity drop is the repair loop's ceiling; module coverage drops are the deliberate 12-cluster cap (rename the metric `module_coverage@cap` or report both); readability 0.00 is a broken proxy — either fix the sentence splitter or delete the metric and say why. Deltas you explain are credibility; deltas you omit are the reason you lose.

3. **Fail closed, and show the output (≈1–2 hours, worth ~+2–3).** After the last repair attempt, *drop* the sentence carrying an unresolvable citation instead of rendering `*(unresolved citation)*` — then the README's "cannot contain a hallucinated citation" is literally true and validity is 1.00 by construction, with a reported `claims_dropped` rate as the honest cost. Simultaneously commit `examples/requests-advanced/overview.md` + one module page into the bundle. Right now a judge can read 40KB about your wiki generator without ever seeing a wiki.

---

## 5. What would make this WIN

The winning version of this project makes three moves you didn't.

**It measures usefulness, not just well-formedness.** Build a 40-question onboarding QA set across 5 repos ("where is retry logic implemented?", "what happens between `Session.send` and the adapter?") with human-written answer keys, then score baseline vs advanced vs raw-README on answer accuracy *and* whether the wiki's cited line range contains the answer. That reframes the whole submission from "our citations resolve" to "a new engineer answers 8/10 questions in 4 minutes instead of 40" — which is the claim your ICP paragraph promises and your eval never tests.

**It proves generality where it claims it.** Two non-Python repos in the eval (one Go, one TS) with honestly lower `citation_depth`, plus one cross-model run (a frontier slug alongside deepseek) showing the resolver's guarantee holds regardless of model. Six advertised languages and ten Python libraries is a hole a judge finds in ten seconds; two rows close it.

**It closes the loop into CI.** DESIGN.md's "what we'd do with another week" lists the killer feature — a drift check that re-validates every citation on push and fails the build when anchors rot. A 60-line GitHub Action + one screenshot of a red build on a deliberately-moved function turns a doc generator into a *maintained invariant*, and it's the natural extension of your one real idea: coordinates owned by the AST, forever, not once.

**Cheapest 10 points on the table right now:** full comparison table with regressions owned (+2.5) · run the missing fastapi baseline for a real 20/20 (+1.5) · commit two example wiki pages (+2) · 30-claim hand-verified support precision (+3) · fail-closed on unresolved citations so the README's central claim is true (+1.5). All five are under a day, and none require a new idea.