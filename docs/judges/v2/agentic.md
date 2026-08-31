# Judge v2: agentic (anthropic/claude-opus-4.7)
_2026-08-31 12:20 UTC_

# Agentic Depth Audit: repowiki

## Is this multi-agent or a batch pipeline?

**It's a batch pipeline with agentic garnish.** The evidence is unambiguous:

### Planner is largely theater
`_plan()` (advanced.py:78-108) calls the LLM once for a JSON page list, but:
- On JSONDecodeError → deterministic fallback plan (lines 97-104)
- Post-hoc **backfill** (lines 148-155) forces any module ≥30 lines the planner "skipped" back into the plan, capped at 12
- Core pages (overview/architecture/data-flow/onboarding/glossary) are hardcoded in the prompt itself (lines 87-91)

The planner's actual degrees of freedom are: focus strings, and which of the top-12 modules get consolidated into `module-other`. **The plan is 90% predetermined.** A judge inspecting this sees the LLM rubber-stamping a template.

### "Per-module agents" are independent calls
`_gen_with_repair()` (lines 128-158) is invoked per page with no shared scratchpad, no dependency ordering, no cross-page memory. The `data-flow` page cannot cite decisions the `architecture` page made. Backlinks are computed post-hoc from string matching, not from agents referencing each other's work. **N independent calls, not a collaborating swarm.**

### Verification loop is fixed 3-retry, not verification-driven
Line 132: `for attempt in range(3)`. The repair prompt (lines 133-137) just re-injects the same problem list. There's no:
- Escalation (e.g., pull more context on attempt 2)
- Root-cause reasoning ("why did the model hallucinate this symbol?")
- Adaptive budget (easy pages get 1 try, hard pages get 6)
- Alternative strategies (switch from symbol cite to file cite)

And per SYNTHESIS F5, when retries exhaust, the original design **shipped unresolved cites anyway**; the `_drop_unresolved_sentences` fail-closed patch (lines 111-126) is a text scrub, not an agent decision.

### Strongest ABSENT capability
**Cross-agent claim verification.** A winning submission would spawn a *reader agent* per page that re-reads the cited spans and answers "does this code support this sentence?" — the exact gap SYNTHESIS F2 identifies as fatal. That's the difference between validating coordinates and validating claims, and it requires a *second agent role* the system doesn't have.

---

## Score: Agent Solution & Engineering — **17/30**

| Dimension | Score | Evidence |
|---|---|---|
| **Planning** | 3/6 | advanced.py:78-108 plan exists but backfill (148-155) + hardcoded core pages (87-91) make it near-deterministic; no re-planning on failure |
| **Tool use** | 5/6 | Strong: AST index, resolver, call graph, secret scan — genuine deterministic scaffolding (DESIGN.md pipeline). Best part of the system. |
| **Memory / state sharing** | 1/6 | Trajectory is a log, not a blackboard. Pages don't see each other. `stats` dict is the only shared mutable state. |
| **Verification** | 3/6 | Citation resolver + 3-retry (advanced.py:132) + fail-closed drop (111-126). But per SYNTHESIS F2, verifies coordinates not claims — the deep gap. |
| **Orchestration** | 3/6 | Linear phases (plan→gen→verify→link). No dynamic dispatch, no agent-to-agent handoff, no adaptive control flow. Baseline vs advanced are two separate scripts (baseline.py, advanced.py), not orchestrated peers. |
| **Robustness / integrity** | 2/? bundled | F1/F4/F5 in SYNTHESIS: metric engineered by construction, missing fastapi baseline, threshold mismatch (≥30 vs ≥50). Engineering rigor gaps visible from panel. |

Deductions concentrated on: predetermined planning (advanced.py:87-91, 148-155), no inter-agent memory, fixed retry loop (line 132), verification-of-coordinates-not-claims (SYNTHESIS F2), fail-open until patched (SYNTHESIS F5).

Credit given for: genuinely good deterministic tool layer, honest baseline including `_grep_upgrade` (baseline.py:19-40) as a fair comparison, trajectory logging, fail-closed patch.

---

## The ONE orchestration upgrade

**Add a Verifier Agent role with veto power, called per-claim (not per-page).**

Concretely: after `resolve_all()` succeeds on coordinates, spawn a lightweight second-model call per cited sentence that receives `(sentence, resolved code span)` and returns `{supported: bool, reason: str}`. Unsupported claims feed back into `_gen_with_repair` as a *new class of problem* alongside unresolved cites. Report `claim_support_precision` as a first-class metric.

Why this one:
- Converts the fixed 3-retry into **verification-driven iteration** (retry until claims verified, not until N attempts) — fixes the rubric's verification dimension
- Introduces a **second agent role** with a distinct objective (skeptic vs author), making it genuinely multi-agent
- Directly closes SYNTHESIS F2 (the fatal finding) — the headline metric becomes claim-support, which is actually measured
- Creates real shared state: the verifier's rejections become memory the generator conditions on

Estimated score movement: **17/30 → 24/30**. It upgrades planning (adaptive budget from verifier signal), memory (verifier findings as state), verification (claim-level, not coordinate-level), and orchestration (two-role loop) simultaneously — the only single change that touches four rubric dimensions.