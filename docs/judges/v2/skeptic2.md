# Judge v2: skeptic2 (qwen/qwen3-max-thinking)
_2026-08-31 12:14 UTC_

Based on a hostile re-review of **repowiki v2**, cross-referencing the README’s claims against the actual evaluation data in `evals/report.md` and judge feedback in `docs/judges/SYNTHESIS.md`, here is the requested triad of critical flaws:

---

### (a) **Claimed fix that doesn’t hold up under code or evals**:  
**“Citation validity improves from 0.92 → 0.96”**

- **Claim**: README states advanced mode *improves* citation validity (+0.04).
- **Reality**: This is a cherry-picked aggregate that hides **serious regressions**.
  - In `click`: validity drops **0.96 → 0.78** (−0.18)
  - In `fastapi`: **0.98 → 0.95** (−0.03)
  - In `httpx`: **1.00 → 0.95** (−0.05)
  - Only 8/12 repos show improvement; 4 show decline.
- **Why it fails**: The +0.04 average is mathematically true but **misleading by omission**. The README presents it as a universal win, while the judges (F3) correctly call this “cherry-picking.” Worse, the root cause isn’t model quality—it’s that the repair loop sometimes gives up and ships unresolved citations (see F5), directly contradicting the “cannot contain hallucinated citation” guarantee.

> ✅ **Verdict**: The claimed fix is statistically fragile and contradicted by per-repo evidence. It’s a definitional sleight-of-hand, not a robust engineering improvement.

---

### (b) **NEW problem introduced by the fixes**:  
**Fail-closed dropping sentences + broken readability metric + ungrounded claim-support judge**

The v2 “fixes” introduce three interlocking new failure modes:

1. **Fail-closed sentence dropping**:  
   The README claims unresolved citations are *rejected and repaired*, and if unrecoverable, the sentence is **dropped** (“fail-closed”). But `evals/report.md` shows **readability = 0.00** for `httpx` and `packaging` in advanced mode.  
   - This isn’t “dense prose”—it’s **empty or malformed output**.  
   - Judges confirm (F5): the system actually **fails open**, rendering `*(unresolved citation)*` instead of dropping the sentence.  
   - Yet the README says “the emitted wiki cannot contain a citation the tree doesn't support”—which is **false** if placeholder text ships.

2. **Grep-upgrade baseline suppressed**:  
   The README admits the baseline *could* use `_grep_upgrade` to attempt line numbers but “can’t verify them.” However, `evals/report.md` shows **TypeScript-TmLanguage baseline already achieves depth=0.35**—meaning it *is* using grep-like heuristics.  
   - So why is baseline depth **0.00** on all Python repos? Because `_grep_upgrade` is either disabled or ineffective outside TS/Go.  
   - This makes the **+0.75 depth delta** partly an artifact of uneven baseline capability—not pure advanced-mode superiority.

3. **Claim-support LLM judge is unverified and gameable**:  
   The README touts “claim-support precision = 0.74” as a new advanced-only metric. But:
   - It’s only evaluated on **3 repos** (requests, flask, click)—not all 12.
   - No methodology is given for how “support” is judged.
   - Judges (F2) note: **nothing in the pipeline validates semantic alignment** between claim and cited code—only coordinate existence.  
   - Thus, this “precision” score is likely based on a **post-hoc LLM judge** that can be gamed via prompt engineering (e.g., asking a model to be lenient on plausible-but-wrong mappings).

> ✅ **Verdict**: The “fixes” create brittle output (readability collapse), hide baseline capabilities, and introduce a new metric that lacks grounding—precisely the kind of measurement fragility the project claims to avoid.

---

### (c) **Most gameable remaining metric**:  
**Claim-support precision (0.74)**

- **Why it’s gameable**:  
  - It’s measured via **LLM judgment** (per README: “claim-support LLM judge”), not deterministic code analysis.  
  - The cited spans are real (validity ≈0.96), but whether they *support* the claim is subjective.  
  - An adversarial system could:  
    - Use vague claims (“this function handles errors”) that match almost any error-related code.  
    - Cite large ranges (entire functions) to increase overlap probability.  
    - Prompt the judge LLM with leading context (“assume good faith”).  
  - There’s **no adversarial testing** or human audit trail—just sampled JSON files (`evals/claim_support.json`) with no transparency into labeling criteria.

- **Evidence of vulnerability**:  
  - `click` scores only **0.62** claim-support vs `requests` at **0.80**—yet both have high validity (~0.78–1.00). This variance suggests the metric reflects **claim vagueness or judge bias**, not ground truth.  
  - Judges explicitly flag (F2): “We validate coordinates, not claims… A false claim citing a real symbol scores full marks.” The claim-support metric *pretends* to solve this but does so via another LLM—reintroducing the hallucination risk at the evaluation layer.

> ✅ **Verdict**: Claim-support precision is the most gameable metric because it replaces one LLM (generator) with another (judge), creating a closed loop of self-validation with no external anchor.

---

### Summary of Hostile Findings:
| Issue | Evidence Source | Contradicted Claim |
|------|------------------|--------------------|
| (a) Validity “improvement” | `evals/report.md` (click, httpx, fastapi rows) | “+0.04 validity gain” as universal win |
| (b) New failures | Readability=0.00 + F5 (fail-open) + grep inconsistency | “Fail-closed”, “baseline can’t do line ranges”, “dense-but-verifiable” |
| (c) Gameable metric | Claim-support only on 3 repos + LLM judge + judge panel F2 | “Claim-support precision = 0.74” as trustworthy |

The v2 release **overstates fixes** by leaning on definitional advantages (symbol vs file cites), omits regressions, and introduces new fragilities—all while claiming “measurement honesty.” The judges’ consensus (F1–F5) confirms these are not nitpicks but **core integrity failures**.