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
   citations are rejected and the page is sent back for repair (bounded), so the emitted
   wiki cannot contain a citation the tree doesn't support.
4. A post-hoc **validator** re-checks every emitted citation (file exists, range in
   bounds) for the eval score — validity is a measurement, not a hope.

## Baseline vs Advanced

| | **Baseline** | **Advanced** |
|---|---|---|
| Context | repo map only | repo map **+ actual file contents + symbol tables** |
| Citations | file-level only (`[path]`) | symbol-level, resolved to line ranges |
| Page plan | fixed template | planner LLM, backfilled for full module coverage |
| Verification | resolve-only | reject-and-repair loop on bad citations |
| Extras | — | data-flow from the real call graph (+ mermaid), glossary, backlinks, orphan detection |
| Results | see [`evals/report.md`](evals/report.md) | same table, same repos, same scorer |

## Quickstart

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
| `trajectories/` | JSONL trajectories, one per run |
| `docs/` | DESIGN, CHANGELOG (improvement log), REPRODUCE, VIDEO_SCRIPT |

## Known limitations / failure modes

- **Python is the deep-parse language.** JS/TS/Go/Rust/Java get structural scanning
  (symbols with line numbers, imports) but no call graph; data-flow pages for those repos
  are import-based, not call-based.
- **Very large repos** are truncated at ingest (4 MB content cap; oversized files are
  skeletonized in prompts). Monorepo-scale input will need per-package runs.
- **The LLM can still write true-but-unguided prose** — citations guarantee that claims
  are *anchored*, not that every nuance is correct. The verifier checks anchors, not truth.
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
