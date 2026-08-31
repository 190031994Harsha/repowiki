"""Baseline generator — minimal viable repo wiki.

Single-pass, template-driven: one repo map, one LLM call per page (overview,
architecture, one per module), file-level citations only, simple cross-links.
Deliberately simple: this is the honest measuring stick the advanced system must beat.
"""
from __future__ import annotations

import time
from pathlib import Path

from .citations import resolve_all
from .index import RepoIndex, render_repo_map
from .llm import LLM
from .trajectory import Trajectory

BASELINE_SYSTEM = """You are documenting a code repository for a new engineer.
Write precise, factual markdown. Cite evidence using [path/to/file.py] notation after
every non-obvious claim, and where you can, name the specific function or class with
its approximate line number, e.g. [path/to/file.py::function_name]. Only cite files
from the provided repository map — never invent paths. Keep it readable: short
paragraphs, concrete names, no filler."""


def _grep_upgrade(body: str, idx: RepoIndex) -> str:
    """Baseline fairness: let the baseline attempt line ranges via a naive grep.

    For each [path::name] cite the model emitted, grep the file for `def name` /
    `class name` and upgrade the cite to a single-line range. This is the honest naive
    approach a competent engineer would try first — so the advanced system's depth
    advantage is earned (accuracy + repair), not definitional.
    """
    import re
    from pathlib import Path

    def upgrade(m):
        path, name = m.group(1), m.group(2)
        full = idx.repo.root / path
        if not full.exists():
            return m.group(0)
        for i, line in enumerate(full.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            if re.search(rf"\b(def|class|func|fn)\s+{re.escape(name)}\b", line):
                return f"`{path}:{i}-{i}`"
        return m.group(0)  # grep failed: leave file-level

    return re.sub(r"\[([A-Za-z0-9_\-./]+\.\w+)::([A-Za-z0-9_]+)\]", upgrade, body)


def _page_links(pages: list[str]) -> str:
    links = "\n".join(f"- [[{p}]]" for p in pages)
    return f"\n\n---\n## See also\n{links}\n"


def generate_baseline(idx: RepoIndex, out_dir: Path, llm: LLM,
                      trajectory: Trajectory) -> dict:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    repo_map = render_repo_map(idx)
    pages = ["overview", "architecture"] + [f"module-{m.name.replace('/', '-')}"
                                            for m in idx.modules]
    stats = {"pages": 0, "citations": 0, "unresolved": 0}

    readme = ""
    for f in idx.repo.files:
        if f.path.lower() in ("readme.md", "readme.rst", "readme.txt", "readme"):
            readme = f.content[:3000]
            break

    def gen(name: str, prompt: str) -> str:
        resp = llm.chat(BASELINE_SYSTEM, prompt, purpose=f"baseline:{name}")
        # baseline attempts line ranges via grep upgrade (fair comparison for depth)
        resp_text = _grep_upgrade(resp.text, idx)
        body, cites = resolve_all(resp_text, idx, trajectory)
        stats["citations"] += len(cites)
        stats["unresolved"] += sum(1 for c in cites if c.status != "ok")
        page = f"# {name.replace('-', ' ').title()}\n\n{body}\n{_page_links(pages)}"
        (out_dir / f"{name}.md").write_text(page, encoding="utf-8")
        stats["pages"] += 1
        trajectory.event("page", {"name": name, "mode": "baseline",
                                  "chars": len(page),
                                  "citations": len(cites)})
        return page

    # overview
    gen("overview", f"""Repository map:

{repo_map}

README (excerpt):
{readme or '(none)'}

Write overview.md: what this project does, who uses it, how it's structured at the top
level, and how to get started. Cite files as [path].""")

    # architecture
    gen("architecture", f"""Repository map:

{repo_map}

Write architecture.md: the major components and how they interact, the request/data
flow through the system, and key design decisions visible in the code organization.
Cite files as [path].""")

    # module deep-dives — consolidated so monorepos don't explode into 100 pages.
    # FAIRNESS: the baseline sees the SAME file contents + symbol signatures the advanced
    # sees. The difference is the *process* (single-pass template, no planner, no repair
    # loop, naive grep line-ranges) — not the information access. That's what makes the
    # comparison a measurement of the pipeline, not of who's allowed to read code.
    top = sorted(idx.modules, key=lambda m: -m.total_lines)
    significant = [m for m in top if m.total_lines >= 50][:12]
    other = [m for m in top if m not in significant]

    def module_context(mod) -> str:
        parts = []
        for path in mod.files[:6]:
            content = ""
            for f in idx.repo.files:
                if f.path == path:
                    content = f.content
                    break
            excerpt = content[:3000] + ("\n...(truncated)" if len(content) > 3000 else "")
            parts.append(f"### {path}\n```\n{excerpt}\n```")
        syms = []
        for qual in mod.public_symbols[:20]:
            s = idx.symbols.get(qual)
            if s:
                doc = f" — {s.docstring[:60]}" if s.docstring else ""
                syms.append(f"  - {qual}{s.signature}{doc}")
        parts.append("Symbol table:\n" + "\n".join(syms))
        return "\n\n".join(parts)

    for m in significant:
        gen(f"module-{m.name.replace('/', '-')}",
            f"""Repository map (context):

{repo_map[:2000]}

Module under documentation: {m.name}/ ({m.lang}, {m.total_lines} lines)

{module_context(m)}

Write a module deep-dive: the module's responsibility, its key files and what each does,
its important classes/functions, and how it connects to the rest of the system.
Cite files as [path] and, where you can, name a function/class with its line as
[path::name].""")
    if other:
        listing = "\n".join(f"  - {m.name}/ ({m.lang}, {m.total_lines} lines, "
                            f"{len(m.files)} files)" for m in other[:20])
        gen("module-other", f"""Repository map (context):
{repo_map[:2000]}

These smaller directories were consolidated into one page:
{listing}

Write a survey page: one short paragraph per directory — what it contains and when a
reader would care. Cite representative files as [path].""")

    # index page
    idx_page = "# Wiki Index\n\n" + "\n".join(f"- [[{p}]]" for p in pages) + "\n"
    (out_dir / "index.md").write_text(idx_page, encoding="utf-8")
    stats["pages"] += 1

    stats["wall_s"] = round(time.time() - t0, 1)
    stats["llm_calls"] = llm.calls
    stats["cost_usd"] = round(llm.total_cost, 4)
    trajectory.event("run_complete", {"mode": "baseline", **stats})
    return stats
