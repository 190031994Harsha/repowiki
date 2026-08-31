# Judge Panel v2 Synthesis — deeper multi-lens review (post v1 fixes)

**Panel (distinct lenses, fresh evidence):** gpt-5.6-sol (integrity/red-team PoC), claude-opus-5 (rubric line-by-line), deepseek-v4-pro (source correctness), gemini-3.1-pro (end-user on a real generated wiki), kimi-k3 (README claim-by-claim audit), grok-4.6 (win strategy), qwen3-max-thinking (hostile re-review), claude-opus-4.7 (agentic depth).
**Contrast with v1:** v1 all read the same bundle and converged on measurement-integrity. v2 went deeper — each judge got different evidence tuned to its lens. The result: fewer *re*-found v1 issues (the fixes mostly held) but a sharper set of NEW, deeper problems.

---

## What v2 confirmed was FIXED (v1 → v2)

| v1 failure | v2 verdict |
|---|---|
| 19≠20, fastapi baseline missing | **FIXED** (rubric verified 24/24 rows) |
| cherry-picked README table | **PARTIAL** — structure fixed, but aggregates were stale (computed on 10, labeled 12) |
| all-Python eval | **FIXED on the letter** (Go+TS present), partial on substance (logrus depth 0.00 = resolver does nothing on Go) |
| no claim-support measurement | **PARTIAL** — exists (0.74) but advanced-only, 3/12 repos, judge not blinded |
| fail-open citations | **PARTIAL** — fail-closed added, but rubric found counter-evidence (validity 0.78 on click means unresolved still ship) |

## What v2 found NEW (deeper than v1)

1. **Prose is unreadable — citations strip the noun.** (user, gemini) `"User creates src/requests/models.py:284-375"` — the render dropped the symbol name, leaving a bare coordinate where the noun should be. A new engineer can't grep a line range. **This is the End-to-End Quality killer.** → FIXED: render now keeps the name: `` `Request` (`src/requests/models.py:284-375`)``.

2. **README aggregates don't reconcile with report.md.** (rubric, opus) depth 0.75 claimed vs 0.674 actual over 12 repos; "8/12 wins" vs actual 7 wins/1 tie/4 losses. The table was computed on the 10-Python subset but labeled 12. → FIXED: aggregates recomputed by script from report.json.

3. **Wrong-but-valid citations still ship via two PoC paths.** (integrity, gpt-5.6-sol) — same-file same-name symbols resolve to first match; src/lib prefix alias picks arbitrary. → FIXED: both now require uniqueness, else fail-closed.

4. **It's a batch pipeline, not a multi-agent system.** (agentic, opus-4.7) — planner is near-deterministic, per-module "agents" are N independent calls, fixed 3-retry not verification-driven. The one upgrade that touches 4 rubric dimensions: **a per-claim verifier agent with veto**. → BUILT: `_verify_claims` drops unsupported claims; the verifier is a distinct skeptic role.

5. **No product surface.** (winstrategy, grok) — "judges screenshot UI, not evals/report.md." → BUILT: `repowiki showcase` — self-contained HTML receipt with expandable citations + grounding ledger + dropped-claims appendix.

## The one remaining un-fixed finding

**Claim-support is advanced-only and single-judge.** A rigorous version runs it on the baseline too (proving the delta) and uses a second blind judge or human spot-check. Noted honestly in README as a limitation rather than overstated.

## Net

v1 center of mass was ~55–65. v2 fixed the measurement-integrity disqualifiers and the readability killer, and added the two differentiators (verifier agent + inspectable refusal). The remaining gap to "wins first prize" is a *measured usefulness* study (onboarding QA task) and baseline claim-support — both noted as honest limitations rather than claimed.
