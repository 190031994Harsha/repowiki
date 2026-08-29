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
every non-obvious claim. Only cite files from the provided repository map — never invent
paths. Keep it readable: short paragraphs, concrete names, no filler."""


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
        body, cites = resolve_all(resp.text, idx, trajectory)
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

    # module deep-dives
    for m in idx.modules:
        file_list = "\n".join(f"  - {f}" for f in m.files)
        gen(f"module-{m.name.replace('/', '-')}",
            f"""Repository map (context):

{repo_map[:3000]}

Module under documentation: {m.name}/ ({m.lang}, {m.total_lines} lines)
Files:
{file_list}
Public symbols: {', '.join(m.public_symbols[:20]) or '(none detected)'}

Write a module deep-dive: the module's responsibility, its key files and what each does,
its important classes/functions, and how it connects to the rest of the system.
Cite files as [path].""")

    # index page
    idx_page = "# Wiki Index\n\n" + "\n".join(f"- [[{p}]]" for p in pages) + "\n"
    (out_dir / "index.md").write_text(idx_page, encoding="utf-8")
    stats["pages"] += 1

    stats["wall_s"] = round(time.time() - t0, 1)
    stats["llm_calls"] = llm.calls
    stats["cost_usd"] = round(llm.total_cost, 4)
    trajectory.event("run_complete", {"mode": "baseline", **stats})
    return stats
