# Judge v3: win2 (qwen/qwen3-max-thinking)
_2026-08-31 13:17 UTC_

**Honest v2 Score: 92/100**  
*(Up from 87 → now justified, not naive)*

---

### Was the original 87 naive?

**No—but it was premature.**  
In v1, I (and likely the other high-scoring judge) saw the *architectural insight*: **decoupling LLM judgment from factual grounding via a deterministic resolver**. That’s rare, robust, and directly targets the rubric’s #1 failure mode (hallucinated citations). But v1’s execution had real gaps—stale aggregates, unblinded evals, unreadable output—that made the 87 feel generous to peers who dug into code or ran the system.

The other judges weren’t wrong to score 43–67. They caught **measurable integrity flaws**: mismatched repo counts, missing baselines, Go/TS depth = 0, and fail-open behavior. Those *are* disqualifying in a challenge demanding rigor. My 87 reflected belief in the core idea *despite* those flaws—not blindness to them.

So: **not naive, but optimistic**. The design deserved credit; the implementation didn’t yet earn it.

---

### Why 92 now? What’s fixed—and what still holds me back from 95+?

**v2 fixes are substantial and rubric-aligned:**
- ✅ **Readability killer resolved**: Citations now render as `` `Symbol` (`file:line`)`` — instantly usable by engineers.
- ✅ **Measurement integrity restored**: Aggregates recomputed from `report.json`; table now matches data.
- ✅ **True fail-closed**: Unresolvable or ambiguous symbols now drop claims (not ship broken refs).
- ✅ **Verifier agent added**: A distinct “skeptic” role checks claim-support and vetoes unsupported assertions.
- ✅ **Showcase UI built**: Judges can *see* grounding, dropped claims, and trajectories—no more digging through JSON.

These address **all major v1 disqualifiers**. The system now walks its talk: grounded, inspectable, and honest about limitations.

---

### The single biggest remaining gap to 95+:

> **No measured usefulness study comparing baseline vs advanced on an actual user task (e.g., onboarding QA).**

The rubric rewards *demonstrated impact*, not just technical correctness. You have:
- Strong **factual integrity** (validity 0.96, claim-support 0.74)
- Clear **technical delta** (symbol-level grounding, repair loops)

But you lack **human validation** that the advanced wiki *actually helps engineers faster or better*. For example:
- Give 10 devs a debugging task in FastAPI.
- Half use baseline wiki, half use advanced.
- Measure time-to-answer, confidence, errors.

Without this, the “so what?” lingers. The 0.74 claim-support is impressive—but does it *matter* to the user? That’s the final leap from “clever system” to “first-prize winner.”

*(Note: You honestly disclose this gap—kudos. But disclosure isn’t substitution for evidence.)*

---

### Why I still score higher than the pack:

The other judges are rightly focused on **what’s provably delivered**. But I’m also weighing **what’s generalizable and defensible at scale**.

What they may have missed:
1. **The resolver pattern is exportable**: This isn’t just a wiki—it’s a blueprint for *any* LLM system needing verifiable grounding (docs, audits, compliance). That’s frontier engineering.
2. **Fail-closed by construction > prompt tricks**: Most submissions “hope” citations are right. You *guarantee* they’re either right or absent. That’s a paradigm shift.
3. **Transparency as feature**: Trajectories, dropped claims, grounding ledgers—this is the anti-black-box. Judges can *audit* every decision. In an era of LLM distrust, that’s gold.

Others saw a batch pipeline. I see a **verifiable reasoning scaffold**—one that could underpin trustworthy AI tooling beyond this challenge.

---

### Final note

At 92, repowiki is **the strongest submission I’ve seen** in this challenge cycle. It’s rigorous, honest, and architecturally significant. Close the usefulness gap—even with a small pilot—and it’s a lock for first prize.

Until then: **excellent work, not yet perfect.**