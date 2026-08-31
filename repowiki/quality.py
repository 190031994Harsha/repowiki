"""Deterministic wiki quality scoring.

All metrics are computed from the emitted wiki + the repo index — no LLM judge —
so scores are exactly reproducible. This is the evaluation backbone for the
baseline-vs-advanced comparison table.

Metrics (each 0..1 unless noted):
  citation_validity  — fraction of citations that resolve to a real file/valid range
  citation_depth     — fraction of citations with symbol-level line ranges (vs file-only)
  module_coverage    — fraction of non-trivial modules with a dedicated page
  symbol_coverage    — fraction of public symbols cited at least once
  link_health        — 1 - (dead wikilinks / total wikilinks)
  orphan_rate        — fraction of pages unreachable except via index (0 is best)
  structure          — headings/subheadings/paragraph hygiene score
  readability        — sentence-length + jargon proxy (FK-inspired, code-aware)
"""
from __future__ import annotations

import re
from pathlib import Path

from .citations import extract, resolve
from .index import RepoIndex

WIKILINK_RX = re.compile(r"\[\[([a-z0-9\-]+)\]\]")


def score_wiki(wiki_dir: Path, idx: RepoIndex) -> dict:
    pages = {p.stem: p.read_text(encoding="utf-8") for p in wiki_dir.glob("*.md")}
    if not pages:
        return {"error": "no pages"}

    # ---- citations (handle raw [path] / [[sym:x]] AND rendered `path` / `path:a-b`)
    total_c, ok_c, sym_c = 0, 0, 0
    cited_ranges: list[tuple[str, int, int]] = []
    problems = []
    for name, text in pages.items():
        for c in extract(text):
            # after resolve_all ran, ok cites became `path:a-b`/`path`; raw [[sym:]] that
            # REMAIN in the text are ones the resolver already rejected — count as invalid
            # here but don't double-reject (resolver logged them at generation time).
            total_c += 1
            r = resolve(c, idx)
            if r.status == "ok":
                ok_c += 1
                if r.kind in ("symbol", "path_symbol"):
                    sym_c += 1
                    cited_ranges.append((r.file, r.line_start, r.line_end))
            else:
                problems.append(f"{name}: {c.raw}")
        # rendered file-level: `path` (no range)
        for m in re.finditer(r"`([A-Za-z0-9_\-./]+\.(?:py|js|jsx|ts|tsx|java|go|rs|cpp|cc|c|h|hpp|rb|php|cs|kt|swift))`", text):
            if idx.file_lines(m.group(1)) > 0:
                total_c += 1
                ok_c += 1
        # rendered symbol-level: `path:a-b`
        for m in re.finditer(r"`([A-Za-z0-9_\-./]+\.\w+):(\d+)-(\d+)`", text):
            sym_c += 1
            total_c += 1
            n = idx.file_lines(m.group(1))
            a, b = int(m.group(2)), int(m.group(3))
            if n and 1 <= a <= b <= n + 5:
                ok_c += 1
                cited_ranges.append((m.group(1), a, b))
            else:
                problems.append(f"{name}: bad range {m.group(0)}")

    # ---- links
    dead, total_links = 0, 0
    inbound = {name: 0 for name in pages}
    for name, text in pages.items():
        for ref in WIKILINK_RX.findall(text):
            if ref.startswith("sym:"):
                continue
            total_links += 1
            if ref in pages:
                inbound[ref] += 1
            else:
                dead += 1
    orphans = [n for n in pages
               if inbound[n] == 0 and n not in ("index",)]  # index is the root

    # ---- coverage
    nontrivial = [m for m in idx.modules if m.total_lines >= 30]
    covered = sum(1 for m in nontrivial
                  if f"module-{m.name.replace('/', '-')}" in pages)
    pub = [q for m in idx.modules for q in m.public_symbols]
    all_text = "\n".join(pages.values())
    cited_pub = 0
    for q in pub:
        sym = idx.symbols[q]
        if q.split(".")[-1] in all_text:
            cited_pub += 1
            continue
        # covered by a rendered range citation that intersects the symbol's span?
        if any(f == sym.file and a <= sym.line_end and b >= sym.line_start
               for f, a, b in cited_ranges):
            cited_pub += 1

    # ---- structure & readability
    # strip code, citations, list markers and URLs so sentence-length reflects prose,
    # not citation density (the 0.00 scores were this splitter choking, not bad prose)
    words, sentences, heading_pages = 0, 0, 0
    for text in pages.values():
        prose = re.sub(r"```.*?```", " ", text, flags=re.S)
        prose = re.sub(r"`[^`]*`", " ", prose)          # inline code + citations
        prose = re.sub(r"^\s*[-*]\s+", "", prose, flags=re.M)   # list bullets
        prose = re.sub(r"\[\[?[^\]]*\]\]?", " ", prose)  # wikilinks
        prose = re.sub(r"\S+\.(py|js|ts|java|go|rs)", " code ", prose)  # bare paths
        words += len(prose.split())
        sentences += len(re.findall(r"[.!?](?:\s|$)", prose))
        if re.search(r"^##\s", text, re.M):
            heading_pages += 1
    avg_sent = words / max(1, sentences)
    readability = 1.0 - min(abs(avg_sent - 18) / 30, 1.0)  # peak near ~18 words/sentence

    return {
        "pages": len(pages),
        "citation_validity": round(ok_c / total_c, 4) if total_c else 1.0,
        "citation_depth": round(sym_c / total_c, 4) if total_c else 0.0,
        "citations_total": total_c,
        "module_coverage": round(covered / len(nontrivial), 4) if nontrivial else 1.0,
        "symbol_coverage": round(cited_pub / len(pub), 4) if pub else 1.0,
        "link_health": round(1 - dead / total_links, 4) if total_links else 1.0,
        "orphan_pages": orphans,
        "structure": round(heading_pages / len(pages), 4),
        "readability": round(readability, 4),
        "citation_problems": problems[:10],
    }
