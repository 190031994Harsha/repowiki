# repowiki — Design Notes

## The one decision everything hangs on

LLMs hallucinate citations. Prompting harder doesn't fix it — the model has no feedback
signal telling it a path is wrong. So repowiki removes the *opportunity*: **the model
never produces a path or line number.** It produces intent (`[[sym:qual.name]]`), and a
deterministic resolver — built from an `ast` parse of the real tree — produces the
coordinates. Wrong intent is detectable (symbol not in index → reject → repair);
coordinates are then correct by construction.

This is the generalizable engineering pattern: *use the LLM for judgment, use the
deterministic layer for facts, and put a machine-checkable contract between them.*

## Pipeline

```
repo (URL | local dir)
  └─ ingest.py     clone-to-cache / read-only walk; language detect; SECRET SCAN
  └─ parse.py      Python: ast (symbols, spans, docstrings, call edges)
                   JS/TS/Go/Rust/Java: regex structure scanners
  └─ index.py      symbol table · import graph · call graph · directory→module clusters
  └─ baseline.py │ advanced.py        (two independent generators, same index)
  └─ citations.py  resolve [[sym:...]]/[path] -> file:start-end; reject + repair loop
  └─ quality.py    deterministic scoring (no LLM judge): validity, coverage, links…
```

## Why no embeddings / vector search

Retrieval-augmented generation would scale to bigger repos, but it (a) costs
reproducibility (embedding models drift, indices version), (b) hides the reasoning a
judge wants to inspect, and (c) is unnecessary at the target scale: a compact
deterministic repo map (~400 lines) plus per-module file excerpts fits comfortably in
context. Deliberate scope: *deep and verifiable* beats *broad and fuzzy* for this rubric.

## Baseline vs advanced: what the delta actually is

Not a bigger prompt. The advanced system differs in **information access** (file contents
and symbol tables, not just a map), **grounding** (symbol citations resolved to ranges),
**verification** (repair loop), and **structure** (planner + coverage backfill). The eval
scorer treats both identically; the comparison table is the claim.

## Language support strategy

Python gets the full treatment via stdlib `ast` (zero-dependency reproducibility — no
tree-sitter binaries for judges to fight). Other languages get honest structural
scanning: symbols + imports, no call edges. The scorer reports the difference
(citation_depth will be lower); we'd rather score honestly than fake precision.

## Safety & policy

- Analyzed repos are **read-only**; clones go to a temp cache. No target-repo mutation,
  no calls to any private service of the target.
- `secrets.py` scans all ingested content **before prompt construction**; findings are
  redacted and reported in the run stats.
- The only credentials are the user's own LLM API key, env-provided, never logged
  (trajectory logs record prompts/responses, never headers/keys).

## What we would do with another week

- Tree-sitter optional plugin for real multi-language call graphs
- Incremental re-generation on `git diff` (only re-wiki changed modules)
- A drift check as CI: re-validate all citations on every push; fail the build when the
  wiki's anchors rot
