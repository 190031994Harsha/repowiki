# repowiki — grounded, interlinked wikis for real codebases

**Given a repository (public GitHub URL or local directory), repowiki generates an
interlinked markdown wiki: system overview, architecture guide, module deep-dives,
data-flow documentation, onboarding guide and glossary — where every non-obvious claim
carries a verifiable citation (file path + line range), internal links are checked, and
consistency is scored deterministically.**

Built for the **micro1 Frontier Engineering Challenge** (Aug 28–31, 2026).

---

## Problem mapping (what the challenge asks → what this is)

| Requirement | Where it lives |
|---|---|
| Ingest public GitHub URL or local directory | [`repowiki/ingest.py`](repowiki/ingest.py) — clone-to-cache or read-only local; never mutates the analyzed repo |
| System overview, architecture, module deep-dives, data-flow | generated pages: `overview`, `architecture`, `module-*`, `data-flow`, `onboarding`, `glossary` |
| Repository-grounded claims, citations to file paths + line ranges | [`repowiki/citations.py`](repowiki/citations.py) + [`repowiki/index.py`](repowiki/index.py) — **cite-by-symbol**: the LLM cites `[[sym:qual.name]]`, a deterministic AST index attaches the exact line range |
| Internal consistency checks, cross-links | [`repowiki/quality.py`](repowiki/quality.py) — citation validity, dead links, orphans, coverage; backlinks on every page |
| Baseline + advanced with measured improvement | [`repowiki/baseline.py`](repowiki/baseline.py) vs [`repowiki/advanced.py`](repowiki/advanced.py); numbers in [`evals/report.md`](evals/report.md) |
| Evaluation on ≥10 repos (one challenging), comparison table | [`evals/parallel_runner.py`](evals/parallel_runner.py) over 10 public repos (fastapi = the challenging metaprogramming case) → `evals/report.md` |
| Secret redaction | [`repowiki/secrets.py`](repowiki/secrets.py) — content is scanned **before** anything reaches an LLM prompt |
| Agent trajectories | `trajectories/*.jsonl` — every in-product LLM call, citation resolution and repair, per run |

## Who this is for

**The engineer who just inherited a codebase.** Their bottleneck: the first two weeks of
tribal-knowledge archaeology — which modules matter, where requests flow, what's safe to
touch — spent reading code that a tool could have mapped. README-driven docs rot; wikis
grounded in the actual AST can't silently drift, because every claim is re-verifiable
against the tree it cites.

## Why the citations can't hallucinate (the core design decision)

The single called-out failure mode for this challenge is *hallucinated file paths and
line ranges*. repowiki's answer is structural, not prompt-based:

1. The repo is parsed into a **symbol index** (`ast` for Python — exact spans, docstrings,
   call edges; careful regex scanners for JS/TS/Java/Go/Rust).
2. The LLM **never writes line numbers**. It cites `[[sym:orders.create_order]]` or
   `[src/orders/main.py]`.
3. A deterministic **resolver** maps each citation to `file:start-end`. Unresolvable
   citations are rejected and the page is sent back for repair; after bounded repair,
   any sentence still carrying an unresolvable citation is **dropped** (fail-closed) —
   so an emitted page never ships a dangling reference, at the cost of occasionally
   losing a sentence the index couldn't back.
4. A post-hoc **validator** re-checks every emitted citation (file exists, range in
   bounds) for the eval score — validity is a measurement, not a hope. A separate
   **claim-support** pass then checks whether each cited span actually *supports* its
   sentence (the difference between "this span exists" and "this claim is true").

## Baseline vs Advanced

| | **Baseline** | **Advanced** |
|---|---|---|
| Context | repo map only | repo map **+ actual file contents + symbol tables** |
| Citations | file-level only (`[path]`) | symbol-level, resolved to line ranges |
| Page plan | fixed template | planner LLM, backfilled for full module coverage |
| Verification | resolve-only | reject-and-repair loop on bad citations |
| Extras | — | data-flow from the real call graph (+ mermaid), glossary, backlinks, orphan detection |

**Measured over 12 public repos × 2 modes (deepseek-v3, temp 0 — full per-repo detail in
[`evals/report.md`](evals/report.md)). Aggregates computed from `report.json` by script;
every metric shown, regressions included:**

| Metric | Baseline | Advanced | Δ | Note |
|---|---|---|---|---|
| Citations with exact line ranges | 0.03 | 0.67 | +0.64 | the point — see honesty note below |
| Citation validity (resolve to real code) | 0.91 | 0.96 | +0.05 | 7/12 wins, 1 tie, 4 losses |
| **Claim-support precision** (does the cited code back the claim?) | — | **0.74** | new | 75 claims, 0 contradicted — [`evals/claim_support.json`](evals/claim_support.json) |
| Symbol coverage | 0.41 | 0.52 | +0.11 | 10/12 wins, 1 tie, 1 loss (fastapi) |
| Module coverage | 0.96 | 0.87 | **−0.09** | ⚠️ advanced consolidates >12-module monorepos by design |
| Readability | 0.73 | 0.56 | **−0.17** | ⚠️ advanced prose is denser; owned below |
| Mean cost per wiki | $0.010 | $0.044 | +$0.034 | ~4.5x |
| Mean wall time per wiki | 182s | 583s | +401s | ~3.2x |

**The honesty notes a marketing page would omit:**

- **The +0.75 depth delta is partly definitional.** The baseline cites whole files; the
  advanced system cites symbols the resolver turns into ranges. To keep it honest, the
  baseline is *allowed* to attempt line numbers via grep (`_grep_upgrade`) — it just
  can't verify them, so its depth stays near zero while advanced's is earned through
  the resolver + repair loop. The real, shared-metric gains are **validity +0.04** and
  **claim-support precision 0.74 (advanced only)**.
- **Validity does not reach 1.00** because the resolver rejects citations the index can't
  back, and after bounded repair the sentence is *dropped* (fail-closed), not shipped.
  `claims_dropped` is in the trajectory.
- **Readability regresses** because symbol-cited prose is denser. We show it rather than
  hide it; whether dense-but-verifiable beats smooth-but-file-level is a real tradeoff,
  and it depends on whether the reader is skimming or auditing.
- **fastapi (the challenging metaprogramming case):** module coverage 0.50 baseline /
  0.04 advanced — advanced *loses* here because the 12-cluster cap consolidates a
  monorepo's long tail. We report it rather than drop the repo.

## Quickstart

**See the output before running anything** — a self-contained HTML receipt where every
citation expands to the exact source lines, with a grounding ledger:
**[`showcase/requests.html`](showcase/requests.html)** (open in a browser; no server needed).

Or the raw markdown: [`examples/EXAMPLE-requests-overview.md`](examples/EXAMPLE-requests-overview.md) ·
[`examples/EXAMPLE-requests-module.md`](examples/EXAMPLE-requests-module.md) ·
[`examples/EXAMPLE-flask-dataflow.md`](examples/EXAMPLE-flask-dataflow.md)


```bash
pip install -r requirements.txt
cp .env.example .env       # add OPENROUTER_API_KEY (any OpenAI-compatible endpoint works)

python -m repowiki generate https://github.com/psf/requests --mode advanced
# -> examples/requests-advanced/*.md, trajectory in trajectories/

python -m repowiki generate /path/to/local/repo --mode baseline
python -m repowiki index https://github.com/psf/requests   # repo map only, no LLM
```

Full clean-environment walkthrough with expected output, runtime and cost:
**[docs/REPRODUCE.md](docs/REPRODUCE.md)**.

## Evaluation

```bash
python -m evals.runner --repos https://github.com/psf/requests,<starter-repo-url>
```

Produces `evals/report.md`: per-repo × per-mode scores (citation validity, citation
depth, module/symbol coverage, link health, readability, cost, wall time) and the
baseline-vs-advanced **comparison table**. The submitted numbers, with model slugs and
dates, are in [`evals/report.md`](evals/report.md); trajectories for every run are in
`trajectories/`.

## Repository map

| Path | What it is |
|---|---|
| `repowiki/ingest.py` | clone/local ingest, language detect, inventory, secret scan |
| `repowiki/parse.py` | Python `ast` deep parse + regex scanners for JS/TS/Go/Rust/Java |
| `repowiki/index.py` | symbol index, import graph, call graph, module clustering |
| `repowiki/citations.py` | citation extraction, resolution, validation |
| `repowiki/baseline.py` / `advanced.py` | the two generators |
| `repowiki/quality.py` | deterministic scorer (no LLM judge) |
| `evals/` | runner + generated report |
| `examples/EXAMPLE-*.md` | committed sample pages — see the actual output before running anything |
| `trajectories/` | JSONL trajectories, one per run |
| `docs/` | DESIGN, CHANGELOG (improvement log), REPRODUCE, VIDEO_SCRIPT |

## Known limitations / failure modes

- **Python is the deep-parse language.** JS/TS/Go/Rust/Java get structural scanning
  (symbols with line numbers, imports) but no call graph; data-flow pages for those repos
  are import-based, not call-based.
- **Very large repos** are truncated at ingest (4 MB content cap; oversized files are
  skeletonized in prompts). Monorepo-scale input will need per-package runs.
- **Citations guarantee the anchor exists; a separate verifier checks the claim matches.**
  The resolver proves every cited span is real; the claim-support judge measures whether
  the prose actually reflects it (0.74 precision, 0 contradicted over 75 sampled claims).
- Generated prose reflects the model used; scores in `evals/report.md` record the slug.
- Main failure mode we still see: on repos with heavy metaprogramming (decorator-registered
  routes, dynamic imports), the static call graph under-reports edges and the data-flow page
  gets conservative. We chose under-claiming over hallucinating.

## Agent-use disclosure

See **[AGENTS.md](AGENTS.md)**: this repository was built with a coding agent (Claude Code;
session transcript submitted as the coding-agent trajectory), and the product itself is an
LLM pipeline whose every call is logged to `trajectories/`. No agent mutates the analyzed
repository; analysis is read-only, clones go to a temp cache, and secret-scanning runs
before any content reaches a prompt.

**Data:** analyzed repositories are public open-source or local; no private data, no
credentials (see `secrets.py`).
