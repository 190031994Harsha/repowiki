"""Symbol index + import graph + module clustering + repo map rendering.

This is the deterministic grounding layer: everything the LLM is allowed to cite lives
here, and every citation is resolved back through here. If a symbol isn't in the index,
the citation is rejected — the generator must fix it before the page is accepted.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .ingest import Repo
from .parse import FileParse, Symbol, parse_file


@dataclass
class Module:
    """A directory-level cluster of files — the unit of wiki deep-dive pages."""
    name: str            # e.g. "src/auth" or "repowiki"
    files: list[str] = field(default_factory=list)
    lang: str = ""
    total_lines: int = 0
    public_symbols: list[str] = field(default_factory=list)  # qualnames of classes/functions


@dataclass
class RepoIndex:
    repo: Repo
    parses: dict[str, FileParse] = field(default_factory=dict)
    symbols: dict[str, Symbol] = field(default_factory=dict)      # qualname -> Symbol
    by_name: dict[str, list[str]] = field(default_factory=dict)   # simple name -> qualnames
    by_file: dict[str, list[str]] = field(default_factory=dict)   # file -> qualnames
    import_graph: dict[str, list[str]] = field(default_factory=dict)  # file -> imported files
    call_graph: dict[str, list[str]] = field(default_factory=dict)    # caller qual -> callee names
    modules: list[Module] = field(default_factory=list)

    # ---- lookups used by the citation resolver ----
    def resolve(self, ref: str) -> Symbol | None:
        """Resolve a citation target. Accepts qualname, simple name (if unique), or path.

        Handles src-layout: the importable package is `flask` but symbols are indexed
        as `src.flask.*` — a cite of `flask.app.Flask` must resolve to
        `src.flask.app.Flask`, not be rejected.
        """
        if ref in self.symbols:
            return self.symbols[ref]
        if ref in self.by_name and len(self.by_name[ref]) == 1:
            return self.symbols[self.by_name[ref][0]]
        # src-layout alias: try prefixing with each known top-level dir
        for prefix in ("src.", "lib.", "app."):
            if not ref.startswith(prefix) and (prefix + ref) in self.symbols:
                return self.symbols[prefix + ref]
        # dotted simple name at any depth: "app.Flask" -> "src.flask.app.Flask"
        if "." in ref:
            matches = [q for q in self.symbols if q.endswith("." + ref) or q == ref]
            if len(matches) == 1:
                return self.symbols[matches[0]]
        # path:line or path form -> the file's module symbol
        path = ref.split(":")[0]
        for qual, sym in self.symbols.items():
            if sym.file == path and sym.kind == "module":
                return sym
        return None

    def file_lines(self, path: str) -> int:
        for f in self.repo.files:
            if f.path == path:
                return f.lines
        return 0

    def content_at(self, path: str, start: int, end: int) -> str:
        for f in self.repo.files:
            if f.path == path:
                lines = f.content.split("\n")
                return "\n".join(lines[max(0, start - 1):end])
        return ""


def _resolve_import(repo: Repo, importer: str, imp: str) -> str | None:
    """Best-effort map an import string to a repo-relative file path."""
    if not imp:
        return None
    imp_path = imp.replace(".", "/")
    candidates = [imp_path + ".py", imp_path + "/__init__.py",
                  "src/" + imp_path + ".py", "src/" + imp_path + "/__init__.py"]
    have = {f.path for f in repo.files}
    for c in candidates:
        if c in have:
            return c
    # relative import: try same dir as importer
    d = str(Path(importer).parent).replace("\\", "/")
    for c in (f"{d}/{imp_path.split('/')[-1]}.py",):
        if c in have:
            return c
    return None


def build_index(repo: Repo) -> RepoIndex:
    idx = RepoIndex(repo=repo)
    for f in repo.code_files:
        fp = parse_file(f.path, f.lang, f.content)
        idx.parses[f.path] = fp
        for sym in fp.symbols:
            if not sym.name or not sym.qualname:
                continue
            if sym.qualname in idx.symbols:
                # collision: keep first, note both under name
                pass
            else:
                idx.symbols[sym.qualname] = sym
            idx.by_name.setdefault(sym.name, [])
            if sym.qualname not in idx.by_name[sym.name]:
                idx.by_name[sym.name].append(sym.qualname)
            idx.by_file.setdefault(f.path, []).append(sym.qualname)
        if fp.calls:
            for caller, callee in fp.calls:
                idx.call_graph.setdefault(caller, [])
                if callee not in idx.call_graph[caller]:
                    idx.call_graph[caller].append(callee)

    # import graph at file granularity
    for f in repo.code_files:
        fp = idx.parses[f.path]
        edges = []
        for imp in fp.imports:
            target = _resolve_import(repo, f.path, imp)
            if target and target != f.path and target not in edges:
                edges.append(target)
        idx.import_graph[f.path] = edges

    # module clustering: group code files by directory
    by_dir: dict[str, list] = defaultdict(list)
    for f in repo.code_files:
        d = str(Path(f.path).parent).replace("\\", "/")
        by_dir["." if d == "" else d].append(f)
    for d in sorted(by_dir):
        files = sorted(by_dir[d], key=lambda x: -x.lines)
        mod = Module(name=d, files=[f.path for f in files],
                     total_lines=sum(f.lines for f in files))
        langs = [f.lang for f in files]
        mod.lang = max(set(langs), key=langs.count) if langs else ""
        for f in files:
            for qual in idx.by_file.get(f.path, []):
                sym = idx.symbols[qual]
                if sym.kind in ("class", "function") and not sym.name.startswith("_"):
                    mod.public_symbols.append(qual)
        idx.modules.append(mod)
    return idx


def render_repo_map(idx: RepoIndex, max_lines: int = 400) -> str:
    """Compact textual map for LLM context: tree + per-module symbol summary."""
    out = [f"# Repository: {idx.repo.name}",
           f"languages: {', '.join(f'{k} ({v} lines)' for k, v in idx.repo.languages.items())}",
           f"files: {len(idx.repo.files)} total, {len(idx.repo.code_files)} code",
           "", "## Module map (directory-level clusters)"]
    for m in idx.modules:
        out.append(f"\n### {m.name}/  [{m.lang}, {m.total_lines} lines, {len(m.files)} files]")
        for f in m.files[:8]:
            syms = [q for q in idx.by_file.get(f, [])
                    if idx.symbols[q].kind in ("class", "function")]
            sym_str = ", ".join(s.split(".")[-1] for s in syms[:6])
            out.append(f"  - {f} ({idx.repo and idx.file_lines(f)} lines)"
                       + (f": {sym_str}" if sym_str else ""))
        if len(m.files) > 8:
            out.append(f"  - ... +{len(m.files) - 8} more files")
    out.append("\n## Cross-module imports")
    for f, edges in sorted(idx.import_graph.items()):
        if edges:
            out.append(f"  {f} -> {', '.join(edges[:6])}")
    return "\n".join(out[:max_lines])
