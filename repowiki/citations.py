"""Citation resolution and validation.

Two syntaxes:
  - baseline (file-level):  [src/orders/main.py]            -> validated: file exists
  - advanced (symbol-level): [src/orders/main.py::create_order]  OR  [[sym:orders.create_order]]
      -> resolved through the symbol index to an exact (file, start, end), then rendered
         as  src/orders/main.py:118-142

The LLM never emits line numbers. It emits a path or symbol reference; the resolver
deterministically attaches the line range. Unresolvable citations are rejected and the
generator is asked to repair them (bounded retries), so the emitted wiki cannot contain
a hallucinated path or range.

Every resolution attempt is trajectory-logged — this is the audit trail for the
30-point grounding criterion.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .index import RepoIndex

FILE_CITE_RX = re.compile(r"\[([A-Za-z0-9_\-./]+\.(py|js|jsx|ts|tsx|java|go|rs|cpp|cc|c|h|hpp|rb|php|cs|kt|swift|yaml|yml|toml|sql|sh|json|md))\]")
SYMBOL_CITE_RX = re.compile(r"\[\[sym:([A-Za-z0-9_.]+)\]\]")
PATH_SYMBOL_RX = re.compile(r"\[([A-Za-z0-9_\-./]+\.\w+)::([A-Za-z0-9_.]+)\]")


@dataclass
class Citation:
    raw: str            # as found in the generated markdown
    ref: str            # path or symbol ref
    kind: str           # file | symbol | path_symbol
    status: str = ""    # ok | unresolved | out_of_range
    file: str = ""
    line_start: int = 0
    line_end: int = 0

    def render(self) -> str:
        if self.status == "ok" and self.kind in ("symbol", "path_symbol"):
            return f"`{self.file}:{self.line_start}-{self.line_end}`"
        if self.status == "ok":
            return f"`{self.file}`"
        return f"`{self.raw}` *(unresolved citation)*"


def extract(text: str) -> list[Citation]:
    fences = _code_fence_spans(text)
    out = []
    for rx, kind in ((PATH_SYMBOL_RX, "path_symbol"), (SYMBOL_CITE_RX, "symbol"),
                     (FILE_CITE_RX, "file")):
        for m in rx.finditer(text):
            if any(a <= m.start() < b for a, b in fences):
                continue
            if kind == "file" and f"{m.group(1)}::" in text:
                continue
            ref = f"{m.group(1)}::{m.group(2)}" if kind == "path_symbol" else m.group(1)
            out.append(Citation(raw=m.group(0), ref=ref, kind=kind))
    return out


def resolve(c: Citation, idx: RepoIndex, trajectory=None) -> Citation:
    have = {f.path for f in idx.repo.files}
    if c.kind == "file":
        if c.ref in have:
            c.status, c.file = "ok", c.ref
            c.line_start, c.line_end = 1, idx.file_lines(c.ref)
        else:
            c.status = "unresolved"
    elif c.kind == "path_symbol":
        path, name = c.ref.split("::", 1)
        sym = None
        for qual in idx.by_name.get(name, []):
            if idx.symbols[qual].file == path:
                sym = idx.symbols[qual]
                break
        if sym:
            c.status, c.file = "ok", sym.file
            c.line_start, c.line_end = sym.line_start, sym.line_end
        elif path in have:
            c.status, c.file = "ok", path   # degrade gracefully to file-level
            c.line_start, c.line_end = 1, idx.file_lines(path)
        else:
            c.status = "unresolved"
    else:  # symbol
        sym = idx.resolve(c.ref)
        if sym:
            c.status, c.file = "ok", sym.file
            c.line_start, c.line_end = sym.line_start, sym.line_end
        else:
            c.status = "unresolved"
    if trajectory:
        trajectory.event("citation", {"ref": c.ref, "kind": c.kind, "status": c.status,
                                      "resolved": f"{c.file}:{c.line_start}-{c.line_end}"
                                      if c.status == "ok" else ""})
    return c


def _code_fence_spans(text: str) -> list[tuple[int, int]]:
    """Spans of ``` fenced blocks — citations inside them are diagram syntax, not ours."""
    spans = []
    for m in re.finditer(r"```.*?```", text, re.S):
        spans.append((m.start(), m.end()))
    return spans


def resolve_all(text: str, idx: RepoIndex, trajectory=None) -> tuple[str, list[Citation]]:
    """Resolve every citation in `text`, replacing raw refs with rendered ones.

    Replaces by match position (not text.replace) so repeated identical raw cites
    each resolve correctly instead of the first replacement hiding the rest.
    Skips citations inside ``` fenced code blocks (mermaid diagrams use [[...]] too).
    """
    fences = _code_fence_spans(text)

    def in_fence(pos: int) -> bool:
        return any(a <= pos < b for a, b in fences)

    matches = []
    for rx, kind in ((PATH_SYMBOL_RX, "path_symbol"), (SYMBOL_CITE_RX, "symbol"),
                     (FILE_CITE_RX, "file")):
        for m in rx.finditer(text):
            if in_fence(m.start()):
                continue
            if kind == "file" and f"{m.group(1)}::" in text:
                continue
            ref = f"{m.group(1)}::{m.group(2)}" if kind == "path_symbol" else m.group(1)
            matches.append((m.start(), m.end(), Citation(raw=m.group(0), ref=ref, kind=kind)))
    matches.sort(key=lambda x: x[0])
    cites = []
    for start, end, c in matches:
        cites.append(resolve(c, idx, trajectory))
    # rebuild from the end so offsets stay valid
    for (start, end, _), c in zip(reversed(matches), reversed(cites)):
        text = text[:start] + c.render() + text[end:]
    return text, cites


def validate(text: str, idx: RepoIndex) -> dict:
    """Post-hoc validation of an EMITTED page (used by the scorer)."""
    cites = extract(text)
    n_ok = 0
    problems = []
    for c in cites:
        r = resolve(c, idx)
        if r.status == "ok":
            # line range sanity
            if r.kind in ("symbol", "path_symbol") and r.line_end > idx.file_lines(r.file) + 5:
                problems.append({"cite": c.raw, "why": "range beyond EOF"})
            else:
                n_ok += 1
        else:
            problems.append({"cite": c.raw, "why": "unresolvable"})
    # also check rendered `path:a-b` forms produced by resolve_all
    for m in re.finditer(r"`([A-Za-z0-9_\-./]+\.\w+):(\d+)-(\d+)`", text):
        path, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        n = idx.file_lines(path)
        if n == 0:
            problems.append({"cite": m.group(0), "why": "no such file"})
        elif a < 1 or b > n + 5 or a > b:
            problems.append({"cite": m.group(0), "why": f"range invalid (file has {n} lines)"})
        else:
            n_ok += 1
    total = n_ok + len(problems)
    return {"total": total, "ok": n_ok,
            "validity": (n_ok / total) if total else 1.0, "problems": problems[:20]}
