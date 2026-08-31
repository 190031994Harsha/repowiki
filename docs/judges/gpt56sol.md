# Judge: gpt56sol (openai/gpt-5.6-sol)
_Role: adversarial-lead · 2026-08-31 05:36 UTC_

# repowiki — Lead Judge Critique

## 1. Verdict

**Reject: repowiki is a polished documentation generator whose “grounding” proves only that cited coordinates exist—not that the surrounding claims are true—and its incomplete, self-referential evaluation turns the headline improvement into an engineered metric rather than demonstrated product value.**

---

## 2. Score breakdown against the rubric

> **Provisional score: 45/100.** The official point table is not included in the bundle, so this uses the dimensions the submission itself identifies, including the stated 30-point grounding criterion.

| Dimension | Score | Evidence |
|---|---:|---|
| Problem fit and usefulness | **10/15** | Repository onboarding is real, and the output categories match the challenge. But this is a crowded “LLM writes docs” problem, and no evidence shows that engineers onboard faster or answer codebase questions more accurately. Large repositories are truncated at 4 MB, only 12 directory clusters receive deep dives, and the claimed challenging FastAPI run reaches only **0.04 module coverage** in [`evals/report.md`](evals/report.md). |
| Novelty and technical ambition | **5/15** | AST-backed citation insertion is sensible engineering, but constrained references followed by deterministic resolution are an established structured-generation pattern. The planner, page generators, repair loop, backlinks, and static graphs are conventional orchestration. [`docs/DESIGN.md`](docs/DESIGN.md) describes a good implementation choice, not a major technical breakthrough. |
| Agentic workflow | **10/15** | There is genuine multi-step orchestration: planning, generation, resolution, repair, and scoring in [`repowiki/advanced.py`](repowiki/advanced.py). However, the “agents” do not investigate claims, execute code, query the repository iteratively, or challenge one another. Most authority remains in a static index plus templated LLM calls. The planner is also largely cosmetic because deterministic backfill and fixed core pages define the resulting structure. |
| Citation grounding and correctness | **11/30** | [`repowiki/citations.py`](repowiki/citations.py) verifies file existence and range bounds, not whether a citation supports a sentence. [`RepoIndex.resolve`](repowiki/index.py) allows suffix matching, unique simple-name matching, and aliases, which can resolve an imprecise intent to a real but semantically wrong symbol. `path_symbol` resolution can even “degrade gracefully” to the entire file and still return `ok`. A false claim attached to a real symbol receives full credit. |
| Measured improvement | **4/15** | The headline gain—0.00 to 0.75 citations with line ranges—is mostly guaranteed by the mode definitions: baseline emits file citations, while advanced emits symbols that the system itself converts into ranges. Advanced is not consistently better on validity, coverage, or readability. It is worse on citation validity for Click, Colorama, and HTTPX; worse on module coverage for AnyIO, Flask, and HTTPX; and frequently much worse on readability. The report says “10 repos × 2 modes = 19 runs” and omits the FastAPI baseline entirely. |
| Reproducibility and evaluation rigor | **5/10** | Artifacts, trajectories, and deterministic scoring are positives. But the evaluator is authored by the same team, optimized during development, and measures proxies the implementation directly controls. [`docs/CHANGELOG.md`](docs/CHANGELOG.md) records repeated scorer changes after results looked wrong. There is no frozen test set, independent evaluator, human factuality audit, repeated runs, uncertainty, or comparison with an external baseline. The “~20 minutes” reproduction claim also sits uneasily beside the reported wall times, which total well over two hours if run sequentially. |

### Core technical finding: “valid citation” is not “grounded claim”

The submission repeatedly makes the stronger claim that citations prevent hallucination:

- README: “every non-obvious claim carries a verifiable citation”
- [`docs/DESIGN.md`](docs/DESIGN.md): coordinates are “correct by construction”
- [`AGENTS.md`](AGENTS.md): agents “cannot fabricate citations that survive”

The implementation supports only the narrowest version of that statement.

In [`repowiki/citations.py`](repowiki/citations.py), validation checks:

1. whether the file exists;
2. whether the symbol resolves;
3. whether the line range is within the file.

It does **not** check:

- whether the cited code entails the prose claim;
- whether all non-obvious claims have citations;
- whether the cited symbol is the relevant symbol;
- whether a broad class or file range is useful evidence;
- whether a sentence combines several claims supported by only one anchor.

A model could write “`Flask` encrypts all request bodies before dispatch” and cite the real `Flask` class. The citation would resolve to a valid span and pass the scorer even though the claim is false. The changelog’s example—`flask.app.Flask -> src/flask/app.py:110-1628`—also illustrates how a **1,500-line class citation** can be technically valid while providing little auditability.

There are additional escapes:

- [`RepoIndex.resolve`](repowiki/index.py) accepts a unique simple name or unique suffix, so the exact model intent is not preserved.
- In [`citations.resolve`](repowiki/citations.py), a missing `path::symbol` can degrade to a whole-file citation and still receive `status="ok"`.
- [`_gen_with_repair`](repowiki/advanced.py) stops after three attempts but returns the final body regardless; unresolved citations can therefore still be emitted. That directly contradicts “the emitted wiki cannot contain” an unresolved citation.
- Only **75%** of advanced citations have ranges in the aggregate claim, meaning one quarter still retain only file-level grounding.
- [`quality.py`](repowiki/quality.py) never performs sentence-level citation coverage or claim entailment.

The system prevents fabricated **coordinates**. It does not prevent fabricated **claims**.

### The scoring harness rewards implementation artifacts

Several metrics are structurally gameable:

- **Citation depth:** baseline is defined to produce no ranges, while advanced deterministically attaches them. The +0.75 result establishes that the renderer ran, not that documentation became more accurate.
- **Symbol coverage:** [`quality.py`](repowiki/quality.py) counts a public symbol as covered if its simple name occurs anywhere in the wiki, even if it is not cited. It also counts any intersecting citation range as coverage.
- **Link health:** [`_page_links`](repowiki/advanced.py) appends links to up to eight other pages mechanically. A graph of arbitrary “See also” links can score 1.00 without demonstrating conceptual consistency.
- **Citation validity:** a valid file path or in-bounds range earns credit independently of semantic support.
- **Readability:** the metric is only distance from an 18-word average sentence. Its implausible 0.00 scores for HTTPX and Packaging expose it as a weak proxy.

This is not an independent evaluation of wiki quality; it is primarily a conformance test for the format repowiki generates.

### The reported comparison is incomplete and materially mixed

[`evals/report.md`](evals/report.md) says:

> `10 repos x 2 modes = 19 runs`

That is not a minor typo. FastAPI—the designated challenging case—has no baseline run, so the submission cannot make a baseline-versus-advanced claim on its most important example.

The advanced mode also regresses on meaningful dimensions:

- **Click:** validity 0.96 → 0.78; readability 0.81 → 0.52.
- **HTTPX:** validity 1.00 → 0.95; module coverage 1.00 → 0.80; readability 0.87 → 0.00.
- **Flask:** module coverage 1.00 → 0.90; readability 0.66 → 0.30.
- **AnyIO:** module coverage 1.00 → 0.75; readability 0.54 → 0.37.
- **Packaging:** readability 0.66 → 0.00.
- **FastAPI:** module coverage is only 0.04, with no paired baseline.

Meanwhile, advanced costs roughly five times as much and takes about 2.5 times as long. The README frames this as buying better grounding, but the main improvement is a range-format metric that advanced mode was explicitly designed to win.

---

## 3. The three most likely reasons this loses

### 1. The citation-grounding claim does not survive scrutiny

This is the fatal flaw.

The system validates the **address**, not the **assertion**. Real file paths and AST spans can accompany entirely false prose. No component performs claim extraction, evidence entailment, contradiction detection, or citation completeness checking.

The submission itself admits this in the README:

> “citations guarantee that claims are anchored, not that every nuance is correct. The verifier checks anchors, not truth.”

That limitation is not peripheral—it collapses the central pitch. “The cited object exists” is substantially weaker than “the claim is repository-grounded.”

### 2. The “advanced improvement” is engineered into the metric and the comparison is incomplete

Baseline is prohibited from producing exact ranges; advanced gets ranges attached automatically. Reporting 0.00 versus 0.75 as the largest gain is therefore close to testing whether the two modes follow their own formatting rules.

More damagingly:

- only 19 of 20 claimed runs exist;
- the missing run is the FastAPI baseline;
- several advanced results regress;
- no independent correctness or user-outcome measurement is present;
- the scoring harness was repeatedly changed while evaluating the same repositories, as documented in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

A judge cannot distinguish genuine improvement from benchmark shaping.

### 3. It remains an impressive small-Python-repository demo, not a robust codebase understanding system

The system’s strongest path is Python AST parsing. Other supported languages use “careful regex scanners,” with no real call graph. Large repositories hit a 4 MB cap; long-tail modules are consolidated; metaprogramming is explicitly under-modeled; and FastAPI receives 4% module coverage.

The product also lacks the feature that would make “living wiki” credible: incremental regeneration or CI drift enforcement. [`docs/DESIGN.md`](docs/DESIGN.md) lists drift checking as something to build “with another week.” Thus the submission’s argument about preventing documentation rot describes a future product, not the submitted one.

---

## 4. The three highest-leverage fixes

### 1. Build and evaluate semantic claim-to-evidence verification

This would change the grounding score most.

Required changes:

- Split generated prose into atomic factual claims.
- Require each factual sentence or clause to carry one or more citations.
- Retrieve the exact cited source excerpt.
- Run an entailment/contradiction verifier over claim plus excerpt.
- Reject broad evidence spans beyond a reasonable size unless narrowed.
- Do not allow `path::symbol` to degrade silently to a whole file.
- Fail generation after bounded repair instead of emitting unresolved content.
- Report citation **precision**, claim **coverage**, and unsupported-claim rate.

Most importantly, manually audit a statistically meaningful random sample. Independent reviewers should label each claim as supported, partially supported, unsupported, or contradicted without seeing the system’s score.

### 2. Replace the self-referential evaluation with a frozen, paired, independent benchmark

Before tuning:

- Freeze the scorer and held-out repository list.
- Run both modes on every repository, including FastAPI.
- Include multiple languages and genuinely large repositories.
- Compare against strong external baselines, not only an intentionally weak internal baseline.
- Repeat stochastic runs and report variance.
- Measure factual correctness, omission rate, navigation utility, and onboarding task completion.
- Publish all generated wikis and raw per-run artifacts, not only aggregate metrics.

A credible result would be something like: “Engineers answer architecture questions 25% faster with repowiki, with 92% claim-level citation precision versus 68% for the strongest baseline.”

### 3. Prove real codebase scale and “living documentation” behavior

Implement the missing product loop:

- tree-sitter or language-server-backed indexing for supported languages;
- framework-aware route, dependency-injection, and registration analysis;
- package-level hierarchical generation instead of a fixed 4 MB prompt cap;
- incremental regeneration from `git diff`;
- CI validation when symbols move or claims lose support;
- stable GitHub commit permalinks rather than inline-code strings such as `` `path.py:12-40` ``.

This also fixes a concrete documentation overclaim: [`docs/REPRODUCE.md`](docs/REPRODUCE.md) says clicking an inline citation in “any markdown viewer” lands on code, but [`Citation.render`](repowiki/citations.py) emits inline code, not a hyperlink.

---

## 5. What would make this WIN

A first-prize version would not merely generate more polished wiki pages with valid-looking coordinates. It would establish a trustworthy, continuously maintained relationship between **claims and executable source evidence**.

The winning version would demonstrate all of the following:

1. **Claim-level grounding, not pointer validity**  
   Every factual claim is atomized, cited, checked against a bounded evidence span, and assigned an entailment status. Unsupported claims are removed rather than merely attached to a nearby symbol.

2. **Independent proof of accuracy**  
   A frozen, held-out benchmark and blinded human audit show that citations actually support claims. The evaluation includes false-but-validly-cited adversarial examples to prove the verifier detects semantic mismatch.

3. **A strong, fair baseline**  
   Compare against a modern repository-documentation or RAG agent with the same model, token budget, and source access—not a baseline intentionally restricted to file-level citations and a repo map.

4. **Real repository scale**  
   Demonstrate Python plus at least one major non-Python ecosystem, a large monorepo, framework-heavy dynamic behavior, and no silent 4 MB truncation. The challenging case must have complete paired results and meaningful coverage.

5. **Measurable user value**  
   Put engineers through onboarding tasks: locate an extension point, trace a request, identify change impact, and explain module boundaries. Show faster completion and fewer wrong answers than README-only and baseline-generated docs.

6. **A genuine living-docs workflow**  
   Generate commit-pinned links, update only affected pages on a diff, flag invalidated claims in CI, and preserve reviewable provenance. This turns the project from a weekend wiki generator into infrastructure teams could trust.

The current submission has a useful deterministic citation-rendering primitive. To win, it must stop equating **“this span exists”** with **“this statement is true,”** and prove that the resulting wiki improves real engineering work on codebases that exceed the demo’s comfortable operating envelope.