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

## [5] Full 10-repo eval → three bugs found in the *measurement*, not the model — 2026-08-29

**Change:** ran the 10-repo eval (baseline + advanced, 20 runs). Three findings, all
infrastructure honesty bugs, all fixed before publishing numbers:

1. **src-layout blind spot** — fastapi indexed as "3139 files, 16 symbols" because the
   content cap hit before the walker reached `src/fastapi/`. Fix: code-first priority walk.
   *(Without this, the "challenging case" would've been documentation of a JS shell.)*
2. **Citation replace collision** — `text.replace(raw, rendered)` silently left duplicate
   raw cites unresolved when a symbol appeared twice; the validator then scored them as
   hallucinations. Fix: positional replacement by match span. Advanced validity recovered
   (requests 0.81 → ~0.99 expected).
3. **Validator double-count** — rendered pages still contained `[[sym:...]]` in See-also
   cross-links; the scorer re-resolved them as fresh citations. Fix: don't re-reject what
   the resolver already handled.

**Evidence:** `evals/report.json` (first full run), fixes verified by re-ingest + tests.

**Learning (feeds the hot take):** every one of these looked, in the output, like a *model*
failure (low validity, tiny symbol count). All three were *measurement* failures. The first
hour of any "the agent got worse" debugging should be spent on the harness, not the model.

---

## [6] Module consolidation for monorepo-scale repos — 2026-08-29

**Change:** baseline and advanced both cap per-directory deep-dives at the 12 largest
clusters and consolidate the long tail into a `module-other` survey page.

**Evidence that drove it:** fastapi (the deliberately challenging case) has ~100
directory clusters (docs examples, test fixtures); uncapped, the generator wrote 100+
pages, ran past 30 minutes, and the useful signal drowned in per-example trivia. The
fix is a *scope* decision, not a quality compromise: the 12 biggest clusters carry the
architecture; the tail gets an honest survey.

**Learning:** the right wiki for a monorepo is not "more pages." Coverage that costs the
reader an hour of navigation fails the user even when every citation is valid.

---

## [7] src-layout alias resolution — 2026-08-29

**Change:** the resolver now maps importable package names (`flask.app.Flask`) to their
src-layout indexed forms (`src.flask.app.Flask`) via prefix aliasing + unique suffix match.

**Evidence that drove it:** the flask re-run after the fence fix still showed 13
unresolved citations — all of them *correct* LLM citations (`flask.sessions.SecureCookieSession`)
rejected because the index stored `src.flask.sessions.SecureCookieSession`. The model was
right; the index was wrong. Fixed in the resolver, verified live:
`flask.app.Flask -> src/flask/app.py:110-1628`.

**Learning (the hot take, sharpened):** twice this weekend the "model error rate" was a
grounding-layer assumption (exact-match qualnames, code-fence blindness) masquerading as
one. The repair loop is only as honest as the index behind it.

---

## [8] Adversarial multi-model judge panel → the honesty rewrite — 2026-08-31

**Change:** before submitting, ran the submission bundle past a panel of 8 frontier models
(GPT-5.5, GPT-5.6-sol, Claude Opus 5, Kimi K3, Grok 4.6, DeepSeek v4 Pro, Gemini 3.1 Pro,
Qwen3 Max Thinking) in adversarial roles — lead-rejection, rubric-scorer, red-team,
end-user. Read all 8 critiques (`docs/judges/*.md`), found they converged on the same 5
failures, and fixed every one:

| Judge consensus | Fix shipped |
|---|---|
| depth delta is definitional (baseline can't emit ranges) | baseline now attempts ranges via grep (`_grep_upgrade`); the delta is earned |
| validates coordinates, not claims | built `evals/claim_support.py` — independent model judges whether cited code supports each claim: **0.80/0.74/0.62 precision, 0 contradicted** |
| README cherry-picks, hides regressions | README now shows all metrics with regressions owned in prose |
| 19≠20 runs, fastapi baseline missing | ran it: 0.98 validity / 0.00 depth / 0.50 modcov |
| unresolved cites still ship (fail-open) | fail-closed: unresolvable sentences dropped, `claims_dropped` counted |
| all-Python eval | added logrus (Go) + TypeScript-TmLanguage; depth honestly lower (0.00, 0.63) |
| resolver silently degrades symbol→whole-file | removed; wrong span = unresolved = repair |
| readability metric returned 0.00 | fixed the sentence splitter (was choking on cite-dense prose) |

**Evidence that drove it:** the panel. Blind scores were 43–67 (one 87 outlier that read
claims not code). After these fixes the same critiques no longer apply.

**Learning:** the single highest-value hour of this project was paying 8 models to attack
it before a human judge could. Every submission should have a red-team panel step.

---

## [9] Judge panel v2 (deep multi-lens) → readability, verifier agent, showcase — 2026-08-31

**Change:** ran a second, deeper panel — 7 models with *distinct lenses and fresh evidence*
(a full generated wiki, the README's own claims, runnable resolver source as a PoC target).
This round found what v1 missed:

| v2 finding (judge) | Fix shipped |
|---|---|
| Prose replaces symbol names with raw coordinates — "User creates `src/requests/models.py:284-375`" is unreadable (user) | citations now render as `` `Request` (`src/requests/models.py:284-375`)`` — noun preserved, span in parentheses |
| README aggregates stale: computed on 10 repos, labeled 12; depth 0.75 claimed vs 0.67 actual (rubric) | recomputed all aggregates from `report.json` by script; table now matches exactly |
| Same-file same-name symbols resolve to first match — wrong-but-valid (integrity PoC) | `path::name` resolves only when exactly one candidate; else fail-closed to repair |
| src/lib alias picks arbitrary prefix (integrity PoC) | prefix aliases resolve only when unique |
| Batch pipeline, not multi-agent; no claim-level verification (agentic) | **added the verifier agent** — per-claim support check with veto, distinct skeptic role |
| No product surface — judges screenshot UI, not JSON (winstrategy) | **built `repowiki showcase`** — self-contained HTML receipt: expandable citations showing exact source lines + grounding ledger + dropped-claims appendix |

**Evidence that drove it:** `docs/judges/v2/*.md` — 8 reports, incl. two concrete PoCs
(working exploit inputs) from the integrity judge.

**The differentiator (winstrategy):** "a wiki that would rather delete a sentence than
underline a lie." The showcase makes refusal inspectable — a judge clicks a citation and
sees the exact code, and can read the sentences the system *refused to ship*.

---

## [10] Judge panel v3 (empirical) → the strawman baseline + broken repro — 2026-08-31

**Change:** third panel, this time *empirical* — judges executed code, recomputed numbers,
walked the README blind, and reviewed the source line-by-line instead of reasoning about it.

| v3 finding (judge) | Fix shipped |
|---|---|
| **Baseline is a strawman** — never sees file contents, so the improvement is confounded by information access, not pipeline (fairness / deepseek) | baseline module pages now get the same file contents + symbol signatures; only the *process* differs (no planner/repair) |
| **README eval command broken as written** — placeholder, wrong module, missing python-dotenv/pytest (repro / gemini) | fixed command, added both deps, aligned 10/12 repo counts |
| **Metric integrity bugs** — +5-line EOF slack inflates validity; symbol_coverage is substring search (`get` matches "target"); (linereview / opus-5) | killed the slack (strict in-bounds), word-boundary match for coverage |
| **Parser crashes / drops edges** — ast.parse only caught SyntaxError (NUL bytes crash the run); relative imports lost package context | catch all ast exceptions; `from . import x` anchors at package |
| ~30 minor findings (unicode cites, off-by-ones, glob order, readability splitter) | noted; several fixed, rest documented |

**Verified by execution:** both v2 integrity PoCs re-run — ambiguous same-file symbols and
src/lib aliases now **fail closed** (`unresolved`), confirming the resolver teeth hold.

**The one thing all three panels agree wins first prize:** a measured-usefulness study
(engineers answer onboarding questions faster with the advanced wiki). Noted in README as
the honest remaining gap, not claimed.

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
