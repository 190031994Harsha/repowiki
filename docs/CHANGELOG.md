# Improvement Changelog

Every meaningful iteration, connected to the evidence that drove it. Newest at the bottom.

---

## [1] Baseline generator — 2026-08-28 (day 1, ~2h in)

**What:** fixed-template pipeline — repo map → one LLM call per page (overview,
architecture, per-module), file-level `[path]` citations, simple see-also links.

**Result on first real run** (local test repo, 25 files/1177 lines): 11 pages, 80
citations, **0 unresolved**, $0.0055, 119s. File-level citations resolve trivially —
the interesting failures were elsewhere (below).

**Evidence:** `trajectories/micro1-frontier-baseline-*.jsonl`

---

## [2] Advanced generator: cite-by-symbol + resolver + repair loop — 2026-08-28

**Change:** LLM cites `[[sym:qual.name]]`; deterministic AST index attaches line ranges;
unresolvable citations bounce the page back for repair (≤2 cycles).

**Evidence that drove it:** baseline pages contained subtly wrong claims that file-level
citations can't catch ("FaultState enum" — it's a class; "combinatorial testing" — it
isn't). Grounding had to get finer than whole files to be checkable.

**Result:** 13 pages, 177 citations, 0 unresolved, 100% citation validity with **78% of
citations carrying exact line ranges** (baseline: 0%). Cost $0.0155 (+2.8x), time 295s
(+2.5x). Trade accepted: grounding is 30% of the rubric; cost is bounded and disclosed.

---

## [3] Scorer honesty fixes — 2026-08-28

**Change:** the quality scorer initially (a) missed rendered citations, reporting
baseline `citations_total: 0`, and (b) undercounted advanced symbol coverage because
rendered `file:a-b` cites don't contain the symbol's name. Fixed to score rendered and
raw forms and to count a symbol covered when a cited range intersects its span.

**Evidence that drove it:** first comparison table showed baseline beating advanced on
symbol coverage (0.95 vs 0.58) — a scorer artifact, not reality. **If the measurement
is wrong, the improvement claim is worthless.** Fixed before any further tuning.

**Result:** baseline depth 0.00 vs advanced 0.78; symbol coverage 0.95 vs 1.00.

---

## [4] Coverage backfill — 2026-08-28

**Change:** after the planner LLM returns its page plan, deterministically append any
non-trivial module (≥30 lines) it skipped.

**Evidence that drove it:** advanced run scored module_coverage 0.875 — the planner
dropped one cluster. Coverage shouldn't depend on planner whim: the LLM proposes, the
deterministic layer guarantees.

---

## Main failure mode

On metaprogramming-heavy repos (decorator-registered routes, dynamic imports), the static
call graph under-reports edges, so data-flow pages get conservative. We under-claim rather
than hallucinate — but it's the first thing we'd fix with tree-sitter.

## Hot take

The biggest quality jump didn't come from a better model or a longer prompt. It came from
*removing the model's ability to be wrong about coordinates*. LLMs are bad at line numbers
and great at judgment — so give judgment to the model and line numbers to the AST. Every
"LLM accuracy" problem we've solved this weekend reduced to that split.
