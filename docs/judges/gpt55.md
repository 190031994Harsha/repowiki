# Judge: gpt55 (openai/gpt-5.5)
_Role: adversarial-lead · 2026-08-31 05:40 UTC_

# repowiki — Lead Judge Rejection Critique

## 1. Verdict

**Reject: repowiki is a polished documentation generator demo whose central “grounded citations” claim collapses into coordinate validation, not factual grounding, and whose evaluation is internally inconsistent and engineered to show an artificial baseline delta.**

---

## 2. Score breakdown against the rubric

> Scored as a hackathon “agentic workflows for frontier engineering” submission: problem importance, novelty, agentic design, grounding/reliability, evaluation, engineering/reproducibility, and product usefulness.

| Category | Score | Evidence |
|---|---:|---|
| Problem relevance / usefulness | **12 / 15** | The problem is real: onboarding engineers to unfamiliar repos is painful. The README clearly targets “the engineer who just inherited a codebase.” Generated overview / architecture / module pages are plausible useful artifacts. But this is a crowded problem space — codebase wiki generation, repo summarizers, DeepWiki-style tools, Sourcegraph/Cody-style code explanations — so relevance is high but not sufficient. |
| Novelty | **5 / 15** | The core idea — parse code, build an index, make an LLM cite symbols, resolve citations deterministically — is sensible but not novel enough for a winning agentic workflow. It is mostly prompt + AST + validation glue. `docs/DESIGN.md` explicitly rejects embeddings and broader retrieval, narrowing the technical contribution. Multi-language support is also shallow: README admits “Python is the deep-parse language” and other languages use regex scanners only. |
| Agentic workflow quality | **6 / 15** | This is largely a batch generation pipeline, not a strong agentic workflow. In `repowiki/advanced.py`, the “agent” does: plan JSON, generate pages, retry on invalid citations. The repair loop is useful but narrow. There is no rich tool use, iterative repo exploration, hypothesis testing, user feedback, or self-directed investigation. The planner is mostly decorative because deterministic backfill overrides it. |
| Citation grounding / reliability | **8 / 25** | The citation mechanism is the strongest part, but the claim is overstated. `repowiki/citations.py` validates that a file exists and a line range is in bounds; it does **not** validate that the cited lines support the prose claim. README even admits this: “citations guarantee that claims are anchored, not that every nuance is correct.” That is fatal because the submission markets “every non-obvious claim carries a verifiable citation.” Also, `quality.py` counts rendered ``path:a-b`` citations as valid if the range is inside the file, not if it corresponds to the claimed symbol or semantic fact. |
| Evaluation quality | **5 / 20** | The evaluation is internally inconsistent and selectively favorable. README claims “10 public repos × 2 modes (20 runs),” but `evals/report.md` says “10 repos x 2 modes = 19 runs” and omits the FastAPI baseline. FastAPI is the declared “challenging metaprogramming case,” yet only the advanced row is shown, with terrible module coverage **0.04** and symbol coverage **0.19**. The headline “advanced improvement” is mostly engineered because baseline is file-level only while advanced is allowed symbol-level citations. |
| Engineering / reproducibility | **10 / 15** | The repo appears runnable, has `docs/REPRODUCE.md`, trajectory claims, a deterministic scorer, and clean module structure. But the reproduction guide contradicts the headline 10-repo eval: it says `evals.runner --repos https://github.com/psf/requests,<starter-repo-url>`, i.e. two repos, not the submitted ten. The report itself has arithmetic/reporting errors, e.g. “10 repos x 2 modes = 19 runs.” |
| Product output quality | **6 / 15** | Advanced is often slower, more expensive, less readable, and not consistently more correct. In `evals/report.md`, advanced readability is **0.00** on `httpx` and `packaging`, worse than baseline by **-0.87** and **-0.66** respectively. Advanced citation validity is worse than baseline on `click`, `colorama`, and `httpx`. Module coverage is worse on `anyio`, `flask`, `httpx`, and catastrophic on `fastapi`. |

**Total: 52 / 120**  
Equivalent: **43 / 100 — impressive demo, not a real winning solution.**

---

## 3. The 3 most likely reasons this loses

### 1. The grounding claim does not survive scrutiny

The submission’s central promise is:

> “every non-obvious claim carries a verifiable citation”

But the implementation verifies only syntactic anchor validity.

In `repowiki/citations.py`:

- `resolve()` checks whether a file exists or a symbol resolves in the index.
- `validate()` checks whether rendered ranges like ``file.py:12-40`` are in bounds.
- There is no entailment check.
- There is no claim extraction.
- There is no test that the cited code actually supports the sentence.

So a page can say:

> “This function implements OAuth token refresh” `src/foo.py:10-20`

and the scorer will accept it as valid if `src/foo.py` exists and lines 10–20 are inside the file. That is not citation grounding; it is coordinate grounding.

The README acknowledges this limitation:

> “citations guarantee that claims are anchored, not that every nuance is correct. The verifier checks anchors, not truth.”

That sentence undercuts the submission’s main selling point. A judge will not accept “file path + line range exists” as proof that the generated wiki is factual.

Worse, `quality.py` reinforces the problem. It treats rendered symbol-level citations as valid if:

```python
n and 1 <= a <= b <= n + 5
```

That is merely range sanity. It does not confirm the cited range maps to the original symbol or supports the prose. The whole “cannot hallucinate citations” claim is technically true only for paths/ranges, not for factual documentation.

---

### 2. The baseline-vs-advanced improvement is engineered, not persuasive

The headline metric is:

| Metric | Baseline | Advanced |
|---|---:|---:|
| Citations with exact line ranges | 0.00 | 0.75 |

But this is not a fair improvement. The baseline is explicitly designed to use file-level citations only, while advanced is given symbol-level citation syntax and a resolver.

README:

| Baseline | Advanced |
|---|---|
| Citations: file-level only `[path]` | symbol-level, resolved to line ranges |

So the largest reported delta is a consequence of feature gating. The baseline is not a competitive baseline; it is intentionally deprived of the core mechanism. A fair baseline would be:

- same LLM,
- same file contents,
- same parser/index,
- citations resolved to nearest enclosing symbol or line range,
- no repair loop / no planner.

Instead, the advanced system wins the exact metric it alone is allowed to optimize.

The rest of the metrics are far less favorable:

From `evals/report.md`:

- `click`: advanced citation validity **0.78**, baseline **0.96**
- `httpx`: advanced validity **0.95**, baseline **1.00**
- `colorama`: advanced validity **0.95**, baseline **0.96**
- `anyio`: advanced module coverage **0.75**, baseline **1.00**
- `flask`: advanced module coverage **0.90**, baseline **1.00**
- `httpx`: advanced module coverage **0.80**, baseline **1.00**
- `httpx`: advanced readability **0.00**, baseline **0.87**
- `packaging`: advanced readability **0.00**, baseline **0.66**

So the advanced system is slower, costlier, sometimes less valid, often less readable, and frequently worse on coverage. The “improvement” is mostly: it emits line ranges because the baseline was not allowed to.

---

### 3. The evaluation report is internally inconsistent, and the hardest case fails

The README claims:

> “10 public repos … 10 public repos × 2 modes (20 runs)”

But `evals/report.md` says:

> “10 repos x 2 modes = 19 runs”

And the summary table indeed has 19 rows. The missing run is critical: **FastAPI baseline is absent.**

This matters because the README names FastAPI as the challenging metaprogramming case:

> “fastapi = the challenging metaprogramming case”

But the only FastAPI row shown is:

| Repo | Mode | Citation validity | w/ line ranges | Module cov | Symbol cov | Wall s |
|---|---|---:|---:|---:|---:|---:|
| fastapi | advanced | 0.95 | 0.86 | **0.04** | **0.19** | **1720.3** |

That is not a successful challenging-case result. It is a near-failure:

- module coverage: **4%**
- symbol coverage: **19%**
- runtime: almost **29 minutes**
- no baseline comparison

The code explains why. In `repowiki/advanced.py`, module backfill is capped:

```python
cap = max(0, 12 - len(planned_modules))
...
skipped = backfill[cap:]
if skipped:
    plan.append({"name": "module-other", "kind": "survey", ...})
```

So despite README language about “backfilled for full module coverage,” the advanced generator explicitly caps module pages and consolidates the rest. This directly produces the FastAPI coverage collapse.

This is exactly the sort of mismatch judges punish: the submission says “challenging case handled,” but the report shows the challenging case is where the approach breaks.

---

## 4. The 3 highest-leverage fixes

### 1. Replace coordinate validation with claim-level grounding

The current verifier answers:

> “Does this path/range exist?”

A winning verifier must answer:

> “Does this cited code support this sentence?”

High-leverage fix:

- Extract atomic claims from generated prose.
- Require every non-obvious claim to map to one or more citations.
- Use a deterministic check where possible:
  - symbol existence,
  - call edge existence,
  - import edge existence,
  - class/function definition,
  - config key presence,
  - route registration,
  - test assertion.
- Add an LLM-as-judge or NLI-style verifier only as a secondary semantic entailment check, with quoted evidence snippets.
- Penalize unsupported claims, not just invalid coordinates.

The output should show claim cards like:

```json
{
  "claim": "ClientSession owns connection pooling",
  "citation": "aiohttp/client.py:245-388",
  "evidence": "class ClientSession ... connector ...",
  "verdict": "supported"
}
```

Without this, “grounded wiki” remains a shallow citation-format demo.

---

### 2. Make the baseline comparison fair

The current baseline is too weak by construction. To make the improvement credible:

- Give baseline access to the same repo contents.
- Let baseline cite files and ask the deterministic layer to attach nearest relevant line ranges.
- Remove only the agentic parts:
  - no planner,
  - no repair loop,
  - no call-graph/data-flow synthesis,
  - no coverage backfill.
- Compare against at least one external baseline:
  - raw Claude/GPT repo summary,
  - README-only generation,
  - existing repo summarizer / code wiki approach if allowed.

Then report metrics that are not tautological:

- factual claim support rate,
- citation precision,
- citation recall over important symbols,
- human usefulness rating,
- time-to-answer benchmark for onboarding questions,
- diff robustness after code changes.

Right now “advanced has line ranges and baseline does not” is not enough.

---

### 3. Fix evaluation integrity before adding features

The eval artifacts need to be judge-proof.

Immediate fixes:

- Resolve the `20 runs` vs `19 runs` contradiction.
- Include FastAPI baseline or remove FastAPI from the 10-repo claim.
- Explain every failed / missing run.
- Stop using `module_coverage` wording if the implementation intentionally caps modules.
- Add generated wiki artifacts for every reported row.
- Include per-repo citation problem samples, not just aggregate validity.
- Add non-Python repos if claiming JS/TS/Go/Rust/Java support.
- Add a held-out repo evaluation that was not used during development.

Also fix questionable scorer behavior in `repowiki/quality.py`:

```python
if q.split(".")[-1] in all_text:
    cited_pub += 1
```

This counts a public symbol as “covered” if its simple name appears anywhere in the wiki text. That is not symbol coverage. It can be inflated by prose, tables, or copied symbol lists. Coverage should require an actual resolved citation intersecting the symbol span.

---

## 5. What would make this WIN

To become a first-prize submission, repowiki needs to move from “generates plausible docs with valid-looking anchors” to “produces a trustworthy, inspectable codebase understanding system.”

A winning version would have:

1. **Claim-level verification**
   - Every paragraph decomposed into claims.
   - Every claim linked to quoted evidence.
   - Verifier distinguishes supported / unsupported / overbroad.
   - Unsupported claims are removed or rewritten.

2. **Real repository understanding**
   - Multi-language parsing via tree-sitter or language servers.
   - Actual call graph / import graph / route graph / config graph.
   - Framework-specific analyzers for hard cases like FastAPI decorators, Flask routing, pytest fixtures, SQLAlchemy models, etc.
   - Data-flow pages derived from graph facts, not mostly LLM prose.

3. **A fair, hard evaluation**
   - 10+ repos actually evaluated in both modes.
   - Include large and non-Python repos.
   - Include at least one private/local-style repo fixture with secrets redaction tested.
   - Measure factual accuracy against human-labeled questions.
   - Measure onboarding usefulness: can a new engineer answer architecture questions faster?

4. **A stronger agentic loop**
   - The agent should ask and answer investigation questions:
     - “Where are requests accepted?”
     - “Where is persistence handled?”
     - “What are the extension points?”
     - “What code paths implement auth?”
   - It should inspect missing evidence, revise claims, and produce an audit trail.
   - Current `advanced.py` is mostly generation + retry; a winner would demonstrate autonomous codebase investigation.

5. **Honest failure handling**
   - If FastAPI module coverage is 0.04, the system should say: “I cannot produce a complete wiki for this repo under current caps.”
   - The wiki should include confidence levels and known blind spots.
   - The report should not present the hard case as a success when the metrics show otherwise.

---

## Bottom line

repowiki has a good engineering instinct: put deterministic structure between the LLM and factual coordinates. But the submission overclaims that into “grounded documentation.” The repo proves only that citations can be made syntactically valid, not that the generated explanations are true.

The fatal flaw is not implementation polish; it is evaluation honesty. The biggest reported gain is built into the baseline design, the hardest repo lacks a baseline and performs poorly, and the verifier validates anchors rather than claims. That is why this lands as an impressive weekend demo, not a real solution.