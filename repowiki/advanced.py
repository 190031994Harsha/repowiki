"""Advanced generator — deep-index, cite-by-symbol, verify-and-repair.

Pipeline:
  1. PLAN     — repo map -> page plan (JSON) tailored to THIS repo's structure
  2. GENERATE — per-page agents that see actual file contents and must cite by symbol
                ([[sym:qual.name]]); line ranges are attached deterministically
  3. VERIFY   — every citation resolved through the index; pages with unresolvable
                citations are sent back for repair (bounded); consistency checks run
  4. LINK     — cross-links + backlinks + orphan detection + wiki index page
  5. EXTRAS   — data-flow page built from the real call graph, glossary, onboarding path

The LLM's job is judgment (what matters, how to explain it). Every factual anchor —
paths, line ranges, symbol existence — comes from the deterministic index.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from .citations import resolve_all, validate
from .index import RepoIndex, render_repo_map
from .llm import LLM
from .trajectory import Trajectory

ADV_SYSTEM = """You are a staff engineer documenting a codebase for new team members.

GROUND RULES (violations waste a repair cycle):
- Cite code ONLY as [[sym:qual.name]] for symbols (classes/functions) or [path/to/file.py]
  for whole files. NEVER write line numbers — they are attached automatically.
- Every non-obvious claim about behavior must carry a citation. No citation, no claim.
- Use ONLY symbols and paths from the provided context. If you can't cite it, don't say it.
- Markdown, short paragraphs, concrete names, no filler, no marketing voice."""


def _excerpt(idx: RepoIndex, path: str, max_chars: int = 6000) -> str:
    """Key file content for prompts: full if small, else symbol skeleton + key bodies."""
    content = ""
    for f in idx.repo.files:
        if f.path == path:
            content = f.content
            break
    if not content:
        return "(file not found)"
    if len(content) <= max_chars:
        return content
    # large file: send the symbol skeleton + head
    lines = content.split("\n")
    keep = set(range(0, 40))
    for qual in idx.by_file.get(path, []):
        s = idx.symbols[qual]
        keep.update(range(s.line_start - 1, min(s.line_start + 3, len(lines))))
    body = "\n".join(f"{i+1}: {lines[i]}" for i in sorted(keep) if i < len(lines))
    return body[:max_chars] + "\n... (truncated: symbol map above covers the rest)"


def _module_context(idx: RepoIndex, module) -> str:
    parts = [f"## Files in {module.name}/"]
    for path in module.files[:6]:
        parts.append(f"\n### {path}\n```\n{_excerpt(idx, path)}\n```")
    syms = []
    for qual in module.public_symbols[:30]:
        s = idx.symbols[qual]
        doc = f" — {s.docstring[:80]}" if s.docstring else ""
        parts_str = f"  - {qual}{s.signature}{doc}"
        syms.append(parts_str)
    parts.append("\n## Symbol table (cite these as [[sym:...]])\n" + "\n".join(syms))
    return "\n".join(parts)


def _page_links(page: str, all_pages: list[str], backlinks: dict[str, list[str]]) -> str:
    others = [p for p in all_pages if p != page][:8]
    bl = backlinks.get(page, [])
    out = "\n\n---\n## See also\n" + "\n".join(f"- [[{p}]]" for p in others)
    if bl:
        out += "\n\n## Referenced by\n" + "\n".join(f"- [[{p}]]" for p in bl[:8])
    return out + "\n"


def _plan(idx: RepoIndex, llm: LLM) -> list[dict]:
    repo_map = render_repo_map(idx)
    modules = "\n".join(f"- {m.name}/ ({m.lang}, {m.total_lines} lines, "
                        f"{len(m.public_symbols)} public symbols)" for m in idx.modules)
    resp = llm.chat(
        ADV_SYSTEM,
        f"""Repository map:
{repo_map}

Modules:
{modules}

Plan a wiki for this repository. Return ONLY a JSON array of pages:
[{{"name": "overview", "kind": "core", "focus": "..."}},
 {{"name": "architecture", "kind": "core", "focus": "..."}},
 {{"name": "module-<dir-with-dashes>", "kind": "module", "module": "<dir>", "focus": "..."}},
 {{"name": "data-flow", "kind": "core", "focus": "..."}},
 {{"name": "onboarding", "kind": "core", "focus": "..."}}]
Include: overview, architecture, data-flow, onboarding, one module page per directory
cluster above (skip trivial clusters <30 lines), and a glossary. JSON only.""",
        purpose="advanced:plan")
    m = re.search(r"\[.*\]", resp.text, re.S)
    plan = []
    if m:
        try:
            plan = json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    if not plan:  # fallback: deterministic plan
        plan = [{"name": "overview", "kind": "core", "focus": "project purpose"},
                {"name": "architecture", "kind": "core", "focus": "component structure"},
                {"name": "data-flow", "kind": "core", "focus": "how data moves"},
                {"name": "onboarding", "kind": "core", "focus": "new engineer path"},
                {"name": "glossary", "kind": "core", "focus": "terms"}]
        plan += [{"name": f"module-{m.name.replace('/', '-')}", "kind": "module",
                  "module": m.name, "focus": ""}
                 for m in idx.modules if m.total_lines >= 30]
    return plan


def _gen_with_repair(idx: RepoIndex, llm: LLM, traj: Trajectory,
                     name: str, prompt: str, stats: dict) -> tuple[str, list]:
    """Generate a page; if citations don't resolve, send problems back for repair."""
    body = ""
    for attempt in range(3):
        resp = llm.chat(ADV_SYSTEM, prompt if attempt == 0 else
                        prompt + "\n\nPREVIOUS DRAFT HAD UNRESOLVABLE CITATIONS:\n" +
                        "\n".join(f"  - {p['cite']}: {p['why']}" for p in problems) +
                        "\nRewrite using ONLY symbols/paths from the context.",
                        purpose=f"advanced:{name}:attempt{attempt}")
        body, cites = resolve_all(resp.text, idx, traj)
        problems = [p for p in validate(resp.text, idx)["problems"]]
        stats.setdefault("repairs", 0)
        if not problems:
            break
        stats["repairs"] += 1
        traj.event("repair", {"page": name, "attempt": attempt,
                              "problems": len(problems)})
    return body, cites


def generate_advanced(idx: RepoIndex, out_dir: Path, llm: LLM,
                      traj: Trajectory) -> dict:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = {"pages": 0, "citations": 0, "unresolved": 0, "repairs": 0}

    repo_map = render_repo_map(idx)
    plan = _plan(idx, llm)
    # coverage by construction: any non-trivial module the planner skipped gets a page
    planned_modules = {p.get("module") for p in plan if p.get("kind") == "module"}
    for m in idx.modules:
        if m.total_lines >= 30 and m.name not in planned_modules:
            plan.append({"name": f"module-{m.name.replace('/', '-')}", "kind": "module",
                         "module": m.name, "focus": "the essentials"})
            traj.event("plan_backfill", {"module": m.name})
    traj.event("plan", {"pages": [p["name"] for p in plan]})
    page_names = [p["name"] for p in plan]
    written: dict[str, str] = {}

    readme = ""
    for f in idx.repo.files:
        if f.path.lower() in ("readme.md", "readme.rst", "readme.txt"):
            readme = f.content[:3000]
            break

    for spec in plan:
        name, kind = spec["name"], spec.get("kind", "core")
        if kind == "module":
            mod = next((m for m in idx.modules
                        if m.name == spec.get("module")), None)
            if not mod:
                continue
            prompt = f"""Repository map (context):
{repo_map[:2500]}

{_module_context(idx, mod)}

Write the deep-dive page for the {mod.name}/ module: responsibility, key files, the
important classes/functions and how they interact, connections to other modules.
Cite with [[sym:qual.name]] and [path]. Focus: {spec.get('focus','') or 'the essentials'}."""
        elif name == "overview":
            prompt = f"""Repository map:
{repo_map}

README (excerpt):
{readme or '(none)'}

Write overview.md: what the project does, who it's for, top-level structure, quick
start. Cite entry points with [[sym:...]] and [path]."""
        elif name == "architecture":
            edges = "\n".join(f"  {f} -> {', '.join(e)}"
                              for f, e in sorted(idx.import_graph.items()) if e)
            prompt = f"""Repository map:
{repo_map}

Import graph (file -> files it imports):
{edges[:3000]}

Write architecture.md: components, boundaries, dependency direction, key abstractions.
Cite with [[sym:...]] and [path]."""
        elif name == "data-flow":
            edges = []
            for caller, callees in sorted(idx.call_graph.items()):
                for c in callees[:4]:
                    edges.append(f"  {caller} -> {c}")
            prompt = f"""Repository map:
{repo_map[:2500]}

Call graph (caller -> callee, from static analysis):
{chr(10).join(edges[:250])}

Write data-flow.md: trace the main flows through the system (e.g. a request's path from
entry point to response, or data from input to storage). Use the call graph edges; cite
every hop with [[sym:...]]. Include one ```mermaid flowchart LR diagram."""
        elif name == "onboarding":
            prompt = f"""Repository map:
{repo_map}

Write onboarding.md: the reading path for a new engineer (which pages/files first),
how to run the project, the first good issue-sized area to explore, common gotchas
visible in the code. Cite with [[sym:...]] and [path]."""
        elif name == "glossary":
            terms = [q for q in idx.symbols
                     if idx.symbols[q].kind in ("class",) and not q.split(".")[-1].startswith("_")][:40]
            prompt = f"""Classes and key types in this repo:
{chr(10).join('  - ' + t for t in terms)}

Write glossary.md: domain terms and key abstractions, one line each, each citing its
defining symbol as [[sym:...]. Only define terms grounded in the code."""
        else:
            prompt = f"""Repository map:
{repo_map}

Write {name}.md. Focus: {spec.get('focus','')}. Cite with [[sym:...]] and [path]."""

        body, cites = _gen_with_repair(idx, llm, traj, name, prompt, stats)
        written[name] = body
        stats["citations"] += len(cites)
        stats["unresolved"] += sum(1 for c in cites if c.status != "ok")

    # ---- linking pass: detect [[page]] refs, compute backlinks, emit files ----
    backlinks: dict[str, list[str]] = {}
    for name, body in written.items():
        for ref in re.findall(r"\[\[([a-z0-9\-]+)\]\]", body):
            if ref in written and ref != name:
                backlinks.setdefault(ref, []).append(name)

    all_pages = sorted(written)
    orphans = []
    for name, body in written.items():
        linked = name in backlinks or name == "overview"
        if not linked:
            orphans.append(name)
        page = f"# {name.replace('-', ' ').title()}\n\n{body}" \
               + _page_links(name, all_pages, backlinks)
        (out_dir / f"{name}.md").write_text(page, encoding="utf-8")
        stats["pages"] += 1
        traj.event("page", {"name": name, "mode": "advanced", "chars": len(page)})

    index_page = "# Wiki Index\n\n"
    for kind_label, pred in [("Core", lambda n: not n.startswith("module-")),
                             ("Module deep-dives", lambda n: n.startswith("module-"))]:
        index_page += f"\n## {kind_label}\n" + "\n".join(
            f"- [[{n}]]" for n in all_pages if pred(n)) + "\n"
    (out_dir / "index.md").write_text(index_page, encoding="utf-8")
    stats["pages"] += 1
    stats["orphans"] = orphans

    stats["wall_s"] = round(time.time() - t0, 1)
    stats["llm_calls"] = llm.calls
    stats["cost_usd"] = round(llm.total_cost, 4)
    traj.event("run_complete", {"mode": "advanced",
                                **{k: v for k, v in stats.items() if k != "orphans"},
                                "orphans": orphans})
    return stats
