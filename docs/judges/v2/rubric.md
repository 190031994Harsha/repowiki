# Judge v2: rubric (anthropic/claude-opus-5)
_2026-08-31 12:16 UTC_

# repowiki v2 — Rubric Scoring & Fix Verification

## Part 1: Did the v1 critiques actually get fixed?

I checked each claimed fix against artifacts, not against `CHANGELOG.md` prose. Where I could recompute numbers from `evals/report.md`'s summary table, I did.

### Fix A — "README cherry-picks, hides regressions" → **PARTIALLY ADDRESSED**

**Real progress:** the README table now carries module coverage (−0.08), readability (−0.15), cost (+5x), wall time (+2.5x), and a prose paragraph owning each regression plus a named fastapi loss. That's a genuine structural change from v1.

**But the aggregates don't reconcile with the per-repo data in the same bundle.** Recomputing means over the 24 rows in `evals/report.md`:

| Metric | README claims | Recomputed from report.md (12 repos) |
|---|---|---|
| Depth, baseline | 0.00 | **0.03** (TS-TmLanguage 0.35, logrus 0.04) |
| Depth, advanced | **0.75** | **0.68** (8.10/12) |
| Symbol cov | 0.35 → 0.47 | 0.41 → 0.52 |
| Readability | 0.66 → 0.51 | 0.73 → 0.56 |
| Module cov | 1.00 → 0.92 | 0.96 → 0.87 |

Drop the two non-Python repos and the numbers snap into place: advanced depth over the 10 Python repos = 7.47/10 = **0.747 ≈ 0.75**; baseline validity = 9.25/10 = **0.92**; symbol cov = 0.35/0.47 exactly. **The headline table is still the old 10-Python-repo aggregate wearing a "Measured over 12 public repos" label.** For a project whose identity is measurement honesty, that's the same class of defect as v1, one level deeper.

Two further residues:
- "Symbol coverage … **advanced higher on all**" is contradicted two rows later by its own fastapi note (0.35 → 0.19) and by logrus (1.00 tie).
- "advanced wins on 8/12, ties/loses on 4" — actual count is **7 wins, 1 tie, 4 losses**. The tie was banked as a win.

### Fix B — "fastapi baseline missing (19≠20)" → **FIXED**

Header reads `12 repos x 2 modes = 24 runs`; the summary contains `fastapi | baseline | 16 | 0.98 | 0.00 | 0.50 | 0.35 | 0.86 | $0.0195 | 271.6`, and a full per-repo comparison block exists. Row count checks out (24 rows present). The uncomfortable number (advanced modcov **0.04**, a −0.45 regression on the designated hard case) is published, not buried.

Caveat: the judge-panel root cause for fastapi's collapse (`backfill ≥50 lines vs scorer ≥30` threshold mismatch, "planner cap limits backfill") is **not shown as fixed anywhere** — the changelog reframes 0.04 as "by design" via the 12-cluster cap. Running the missing cell ≠ fixing the manufactured regression.

### Fix C — "validates coordinates, not claims" → **PARTIALLY ADDRESSED**

**Real:** two independent artifacts reference it — `evals/report.md` header (`requests 0.80, flask 0.74, click 0.62`) and the README row (`0.74, 75 claims, 0 contradicted`). This is the single most valuable v2 addition and it is not vaporware in the sense that per-repo numbers exist.

**Not sufficient for the 30-point criterion:**
- **Advanced-only.** No baseline claim-support number, so the project *still* cannot claim a measured improvement on the metric the judges called the fatal one. The README even labels it "new" rather than a delta.
- **3 of 12 repos, n=75, one judge model.** No inter-rater check, no human spot-check, no blinding protocol described in the bundle.
- Numbers don't quite reconcile: mean of (0.80, 0.74, 0.62) = 0.72, README says 0.74 — plausible under claim-weighting, but unstated.
- `evals/claim_support.json` and `claim_support.py` are cited but **not included in the bundle**, so the measurement itself is unverifiable here.
- 0.74 precision means **~1 in 4 grounded claims isn't backed by its cited span** — honestly reported, but it undercuts the README's headline promise that "every non-obvious claim carries a verifiable citation."

### Fix D — "fail-open citations" → **PARTIALLY ADDRESSED / evidence points against it**

Claimed: unresolvable sentences dropped, `claims_dropped` counted. Three pieces of counter-evidence in the bundle:

1. **Advanced validity is 0.78 on click, 0.95 on four others.** If unresolvable citations are dropped *before* emission, a post-hoc validator over emitted citations should read ≈1.00. It doesn't.
2. The README's explanation is self-contradictory: "Validity does not reach 1.00 because the resolver rejects citations … and after bounded repair the sentence is *dropped* (fail-closed), **not shipped**." A not-shipped citation cannot lower the score of shipped citations. Either the drop isn't happening or the metric is still counting pre-drop rejects.
3. `docs/REPRODUCE.md` still lists as a live symptom: *"A page full of 'unresolved citation'"* — the exact v1 fail-open render string the panel flagged in `_gen_with_repair`.

Also, `claims_dropped` is only "in the trajectory" — **not aggregated into `report.md`**, so the fail-closed contract has no published number.

### Fix E — "all-Python eval" → **FIXED on the letter, PARTIAL on substance**

`logrus` (Go) and `TypeScript-TmLanguage` (TS) both appear with baseline + advanced rows. Real, verifiable, and the degradation is disclosed ("depth honestly lower (0.00, 0.63)").

Substance caveats worth naming: logrus **advanced depth = 0.00 while baseline = 0.04** — the flagship symbol→line-range mechanism does not function on Go at all, which is the whole product thesis. logrus advanced sym-cov 1.00 and TS-TmLanguage's "960 files, 776 symbols" both smell like regex-scanner artifacts rather than measured coverage. And TmLanguage is a grammar/fixture repo, not a real TS codebase — so 2/12 non-Python, one of which is a near-degenerate case.

---

## Part 2: Scores

| # | Criterion | Pts | Score |
|---|---|---|---|
| 1 | Problem framing & product thinking | 15 | **12** |
| 2 | Repository grounding & citation integrity | 30 | **19** |
| 3 | Baseline→advanced measured improvement & eval rigor | 20 | **11** |
| 4 | Engineering quality & reproducibility | 15 | **10** |
| 5 | Communication, documentation & honesty | 15 | **11** |
| 6 | Agent trajectories / process transparency | 5 | **4** |
| | **Total** | **100** | **67** |

**1. Framing — 12/15.** Sharp, non-generic user ("the engineer who just inherited a codebase," the two-week archaeology bottleneck) and an explicit requirement→artifact mapping table. Real scope judgment in changelog [6]: "the right wiki for a monorepo is not more pages." Held back because the product's own eval shows it failing hardest exactly where the pitch is strongest — a 3,139-file monorepo gets 0.04 module coverage, i.e. the inherited-codebase case the framing targets.

**2. Grounding — 19/30.** The architecture is the best thing here: LLM never writes line numbers, deterministic AST index owns spans, reject-and-repair, independent post-hoc validator. Claim-support now exists (0.74) where v1 had nothing. Deductions: no baseline claim-support so no *measured* grounding improvement on the metric that decides this criterion; claim-support covers 3/12 repos with unshipped artifacts; fail-closed is asserted but contradicted by validity <1.00 and by REPRODUCE's own troubleshooting text; Go depth 0.00 means grounding is Python-only in practice; click advanced validity 0.78 is a real regression in the core metric.

**3. Measured improvement — 11/20.** 24/24 runs complete, per-repo two-column deltas, cost and latency published, regressions visible. But the headline comparison table is computed over a 10-repo subset while labeled 12, misstates baseline depth (0.00 vs 0.03) and advanced depth (0.75 vs 0.68), asserts "higher on all" against its own data, and miscounts wins 8 vs 7. The readability metric the changelog says was **fixed** still returns **0.00** for httpx and packaging in a report dated "final, post judge-panel" — a claimed fix visibly not landed. Net: the eval is now complete but the summary layer is not trustworthy without recomputation, which is the criterion's whole point.

**4. Engineering / reproducibility — 10/15.** Tiered runs with honest time/cost envelopes, pinned Python/git versions, no native deps, explicit "nothing written outside these dirs," named failure modes. Deductions: §5's full-eval command is `python -m evals.runner --repos requests,<starter-repo-url>` — an unfilled placeholder and a different module than the `evals/parallel_runner.py` the README credits for the 12-repo run, so the headline result has **no working reproduction command**; §3 is titled "Smoke test (no LLM, no cost)" while the top of the file defines the smoke test as ~$0.10/10 min; no test suite or requirements pinning visible in the bundle; single-OS verification.

**5. Communication / honesty — 11/15.** Genuinely unusual transparency: shipping `docs/judges/SYNTHESIS.md` with the blind scores (45, 43, 67.5, 87) and "center of mass ~55–65" against itself, plus a changelog where each change names the evidence that forced it and the "measurement failure, not model failure" learning. The honesty notes section pre-empts the definitional-delta objection. Deducted because the loudest honesty claims sit directly on top of numbers that don't reconcile — opus5's v1 line "the honesty framing is louder than the honesty" survives v2 at the aggregate-table level.

**6. Trajectories — 4/5.** Per-run JSONL covering every LLM call, citation resolution, repair cycle, plus a render helper and filename conventions referenced from the changelog. Short of full marks: no sample trajectory in the bundle, and `claims_dropped` — the one trajectory field load-bearing for a rubric claim — is never surfaced in the report.

---

## Part 3: Cheapest remaining points

Ranked by points per minute.

1. **Regenerate the README table from `report.json` with a script (~15 min, +2–3).** Every discrepancy above is arithmetic: depth 0.00→**0.03** / 0.75→**0.68**, symcov 0.41→0.52, readability 0.73→0.56, modcov 0.96→0.87, "higher on all" → "higher on 10/12, fastapi and logrus excepted," "8/12" → "7 wins / 1 tie / 4 losses." Print `n=12` next to each mean. This is the single highest-leverage fix in the bundle because it removes the one objection that generalizes to "don't trust any number here."

2. **Run claim-support on the *baseline* over the same 75 claims (~45 min, +2–3, criterion 2).** Right now the differentiator is a standalone 0.74. As a delta (e.g. baseline 0.5x → advanced 0.74) it becomes the measured improvement on the 30-point criterion — which is the largest single pool of unearned points left.

3. **Ship `evals/claim_support.py` + `claim_support.json` and state the protocol (~15 min, +1).** Judge model, sampling method, blinding, and how 0.80/0.74/0.62 weights to 0.74. Unverifiable evidence scores as absent.

4. **Publish `claims_dropped` in `report.md` and split validity into emitted-only vs pre-repair (~30 min, +1–2).** This is what makes fail-closed *checkable* and resolves the incoherence between "dropped, not shipped" and validity 0.78. Simultaneously delete the stale "page full of unresolved citation" line from REPRODUCE, or admit the fail-open path still exists.

5. **Fix REPRODUCE §5: real command, real repo list, no `<placeholder>`; retitle §3 (~10 min, +1).** A headline result with no runnable command is the cheapest point on the board.

6. **Re-run httpx + packaging advanced or delete the readability metric (~20 min, +1).** Two 0.00 cells in a "final" report directly contradict a changelog line claiming the splitter was fixed. Either number would do; the contradiction is what costs.

Items 1, 3, 5, 6 total roughly an hour and are pure bookkeeping — call it **+5–6**. Adding item 2 (the baseline claim-support delta) plausibly lands this in the **mid-to-high 70s**, and unlike v1's fixes these are verifiable from the artifacts themselves rather than assertable in a changelog.