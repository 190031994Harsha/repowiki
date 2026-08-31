# Judge Panel Synthesis — repowiki (micro1 Agentic Workflows)

**Panel:** gpt-5.6-sol, gpt-5.5, claude-opus-5, kimi-k3, grok-4.6, deepseek-v4-pro, gemini-3.1-pro, qwen3-max (8 substantive; glm-5.3 failed to emit).
**Blind scores given:** 45, 43, 67.5, 87, plus three role-scoped (measured-improvement 5–6/15, reproducibility 6/15, end-to-end 16/20).
**Center of mass: ~55–65/100. The submission as-is is a strong demo that loses on integrity-of-measurement, not on engineering.**

Every judge found the SAME failures independently. That convergence is the signal — these aren't taste differences.

---

## The 5 consensus failures (found by ≥4 judges each)

### F1. The headline metric is engineered, not measured. (ALL 8)
`citation_depth` 0.00 → 0.75 is the largest number in the README table, and it's **definitional**: baseline emits `[file]`, advanced emits `[[sym]]` which the resolver turns into ranges. The baseline was *prohibited* from producing the thing we're measuring. deepseek: "claiming a bicycle is 100% better than a car at having handlebars."
**Every judge discounted the whole table on this alone.**

### F2. We validate coordinates, not claims. (gpt56sol, opus5, gpt55, grok46, kimik3)
The README's promise — "every non-obvious claim carries a verifiable citation" — is not what the code does. `resolve()` checks a span exists; nothing checks the cited code *supports the sentence*. We even admit it in README ("checks anchors, not truth") and then never measure truth. A false claim citing a real symbol scores full marks.
**This is the fatal one. The 30-point grounding criterion is won on claim-support, which we never measure.**

### F3. The README table cherry-picks; the regressions are real. (opus5, kimik3, grok46, gpt55, deepseekv4)
Advanced *loses* on: citation validity (click 0.96→0.78), module coverage (4 repos), readability (httpx 0.87→**0.00**, packaging 0.66→**0.00**). None of those three metrics are in the README table. For a project whose entire identity is "measurement honesty," this is disqualifying-sounding. opus5: "the honesty framing is louder than the honesty."

### F4. 19 ≠ 20: the challenging repo has no baseline. (ALL 8)
Report says "10 repos × 2 modes = 19 runs" and the missing cell is **fastapi baseline** — the designated hard case. Plus fastapi advanced shows module_coverage **0.04**. Reads as "we ran the hard one and quietly excluded it." (Root cause kimik3 found: planner cap limits backfill, not the planner; and backfill ≥50 lines vs scorer ≥30 — a threshold mismatch manufacturing fake regressions.)

### F5. Contract broken: unresolved citations still ship. (gpt56sol, opus5, kimik3, grok46)
`_gen_with_repair` gives up after 3 attempts and **renders the page anyway** with `*(unresolved citation)*`. README says the wiki "cannot contain a hallucinated citation." False per the code. We fail *open*, not closed.

---

## Consensus high-leverage fixes (ranked by frequency × impact × cost)

| # | Fix | Judges citing | Cost | Points recovered |
|---|---|---|---|---|
| 1 | **Claim-support eval**: sample ~40 citations, blind-judge "does this span support this sentence" (hand or 2nd model), report precision. | gpt56sol, opus5, kimik3, deepseekv4, gpt55 | ~2h | +3–4 (the differentiator) |
| 2 | **Publish ALL metrics incl. regressions**, own each one in prose. Kill or fix the broken readability metric (0.00 = sentence splitter choking on cite-dense prose). | opus5, kimik3, gpt55, deepseekv4 | ~30min | +2–3 |
| 3 | **Fail closed**: after last repair, DROP the sentence with the unresolvable cite, report `claims_dropped`. Makes "cannot contain" literally true. | opus5, grok46, gpt56sol | ~1h | +2–3 |
| 4 | **Run fastapi baseline** (complete the 20/20) + fix the ≥30/≥50 threshold mismatch. | ALL | ~30min | +1.5 |
| 5 | **Resolver teeth**: no degrade-to-whole-file-on-missing-symbol; suffix/simple-name match = repair hint, not silent bind. | grok46, gpt56sol | ~1h | +1–2 |
| 6 | **2 non-Python eval repos** (Go + TS) with honestly-lower depth. | opus5, kimik3, gemini31, gpt55 | ~20min run | +1 |
| 7 | **A fairer baseline** that also attempts ranges (regex/grep) so the depth delta is real. | deepseekv4, gpt55 | ~1h | +2 |
| 8 | **Commit example wiki pages** into the bundle (judges read 40KB about a wiki and never saw one). | opus5, grok46 | 5min | +2 |

## What would WIN (consensus across all 8)
- **Claim-level grounding** (atomize claims → cite → entailment-check), not pointer validity. [7/8]
- **Independent proof of accuracy** — frozen held-out set + blinded audit, adversarial false-but-valid-cited cases. [6/8]
- **Measure usefulness, not well-formedness** — onboarding QA task: "answer 40 questions with the wiki vs baseline vs raw repo." [opus5, deepseekv4, gemini31, kimik3]
- **Close the loop into CI** — drift-check that re-validates citations on push. The "tool, not demo" move. [opus5, grok46, gemini31]

## The lone dissenter worth noting
**qwen3max scored 87/100** and called grounding "near-perfect." It read the README's claims rather than the code's behavior. That's the score we get if a judge *doesn't* dig. The other 7 dug. We optimize for the diggers.
