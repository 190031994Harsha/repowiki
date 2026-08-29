"""Evaluation runner: baseline + advanced over N repos, deterministic scoring, report.

Usage: python -m evals.runner [--repos URL1,URL2] [--modes baseline,advanced]
Writes evals/report.md + evals/report.json. Reproduces with the same seed inputs;
LLM nondeterminism is the only variance (temperature 0; models pinned by slug).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repowiki.advanced import generate_advanced          # noqa: E402
from repowiki.baseline import generate_baseline          # noqa: E402
from repowiki.index import build_index                   # noqa: E402
from repowiki.ingest import ingest                       # noqa: E402
from repowiki.llm import LLM                             # noqa: E402
from repowiki.quality import score_wiki                  # noqa: E402
from repowiki.trajectory import Trajectory               # noqa: E402

# 10 public repos spanning sizes, languages and styles. H07 is the deliberately
# challenging case: FastAPI is metaprogramming-heavy (decorator-registered routes,
# dependency injection), which is where our static call graph is weakest.
DEFAULT_REPOS = [
    "https://github.com/psf/requests",            # mid Python, canonical structure
    "https://github.com/pallets/click",           # mid Python, decorator-driven CLI
    "https://github.com/encode/httpx",            # mid Python, async
    "https://github.com/tiangolo/fastapi",        # CHALLENGING: heavy metaprogramming
    "https://github.com/pallets/flask",           # small-mid Python, blueprints
    "https://github.com/kennethreitz/records",    # small Python, single-module-ish
    "https://github.com/agronholm/anyio",         # mid Python, structured concurrency
    "https://github.com/pypa/packaging",          # small-mid Python, parsers
    "https://github.com/python-jsonschema/jsonschema",  # mid Python, registry patterns
    "https://github.com/tartley/colorama",        # small Python, thin wrapper
]


def run_one(repo_src: str, mode: str, model: str | None) -> dict:
    t0 = time.time()
    repo = ingest(repo_src)
    idx = build_index(repo)
    out = ROOT / "evals" / "wikis" / f"{repo.name}-{mode}"
    traj = Trajectory(ROOT / "trajectories", f"eval-{repo.name}-{mode}")
    llm = LLM(model=model, trajectory=traj)
    gen = generate_baseline if mode == "baseline" else generate_advanced
    stats = gen(idx, out, llm, traj)
    scores = score_wiki(out, idx)
    return {
        "repo": repo.name, "source": repo_src, "mode": mode,
        "head_sha": repo.head_sha, "secrets_found": list(repo.secret_findings),
        "files": len(repo.files), "code_files": len(repo.code_files),
        "symbols": len(idx.symbols), "modules": len(idx.modules),
        "gen": stats, "scores": scores,
        "wall_s": round(time.time() - t0, 1),
        "trajectory": str(traj.path),
    }


def comparison_table(results: list[dict]) -> str:
    """Baseline-vs-advanced per repo: the table the rubric asks for."""
    lines = []
    by_repo: dict[str, dict[str, dict]] = {}
    for r in results:
        by_repo.setdefault(r["repo"], {})[r["mode"]] = r
    metrics = [("citation_validity", "Citation validity"),
               ("citation_depth", "Citations w/ line ranges"),
               ("module_coverage", "Module coverage"),
               ("symbol_coverage", "Symbol coverage"),
               ("link_health", "Link health"),
               ("readability", "Readability")]
    for repo, modes in by_repo.items():
        b, a = modes.get("baseline"), modes.get("advanced")
        if not (b and a):
            continue
        lines.append(f"\n### {repo} ({b['files']} files, {b['symbols']} symbols)\n")
        lines.append("| Metric | Baseline | Advanced | Delta |")
        lines.append("|---|---|---|---|")
        for key, label in metrics:
            bv = b["scores"].get(key, 0)
            av = a["scores"].get(key, 0)
            d = av - bv
            lines.append(f"| {label} | {bv:.2f} | {av:.2f} | {'+' if d>=0 else ''}{d:.2f} |")
        lines.append(f"| Pages | {b['gen']['pages']} | {a['gen']['pages']} | "
                     f"+{a['gen']['pages']-b['gen']['pages']} |")
        lines.append(f"| LLM cost (USD) | ${b['gen']['cost_usd']:.4f} | "
                     f"${a['gen']['cost_usd']:.4f} | "
                     f"${a['gen']['cost_usd']-b['gen']['cost_usd']:+.4f} |")
        lines.append(f"| Wall time (s) | {b['wall_s']} | {a['wall_s']} | "
                     f"{a['wall_s']-b['wall_s']:+.0f} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", default=",".join(DEFAULT_REPOS))
    ap.add_argument("--modes", default="baseline,advanced")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    results = []
    for repo_src in args.repos.split(","):
        for mode in args.modes.split(","):
            print(f"[eval] {repo_src} / {mode}")
            r = run_one(repo_src.strip(), mode.strip(), args.model)
            results.append(r)
            print(f"[eval]   -> validity={r['scores']['citation_validity']}, "
                  f"depth={r['scores']['citation_depth']}, "
                  f"cost=${r['gen']['cost_usd']:.4f}, {r['wall_s']}s")

    (ROOT / "evals" / "report.json").write_text(json.dumps(results, indent=1))

    report = ["# Evaluation Report\n",
              f"Generated: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
              f"Model: {args.model or 'env default'} | Temperature 0\n",
              "\n## Summary\n",
              "| Repo | Mode | Pages | Citation validity | w/ line ranges | Module cov | "
              "Symbol cov | Cost | Wall s |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        s, g = r["scores"], r["gen"]
        report.append(f"| {r['repo']} | {r['mode']} | {g['pages']} | "
                      f"{s['citation_validity']:.2f} | {s['citation_depth']:.2f} | "
                      f"{s['module_coverage']:.2f} | {s['symbol_coverage']:.2f} | "
                      f"${g['cost_usd']:.4f} | {r['wall_s']} |")
    report.append("\n## Baseline vs Advanced\n")
    report.append(comparison_table(results))
    (ROOT / "evals" / "report.md").write_text("\n".join(report))
    print(f"[eval] wrote evals/report.md ({len(results)} runs)")


if __name__ == "__main__":
    main()
