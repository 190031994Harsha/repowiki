"""repowiki CLI.

  python -m repowiki generate <repo-url-or-path> --mode baseline|advanced --out wiki/
  python -m repowiki index <repo>          # print the repo map (no LLM)
  python -m repowiki render <traj.jsonl>   # render a trajectory
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .baseline import generate_baseline
from .index import build_index, render_repo_map
from .ingest import ingest
from .llm import LLM
from .trajectory import Trajectory, render_file

ROOT = Path(__file__).resolve().parents[1]


def _load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                import os
                os.environ.setdefault(k.strip(), v.strip())


def main():
    _load_env()
    ap = argparse.ArgumentParser(prog="repowiki")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate")
    g.add_argument("repo")
    g.add_argument("--mode", choices=["baseline", "advanced"], default="advanced")
    g.add_argument("--out", default=None)
    g.add_argument("--model", default=None)

    i = sub.add_parser("index")
    i.add_argument("repo")

    r = sub.add_parser("render")
    r.add_argument("trajectory")

    args = ap.parse_args()
    if args.cmd == "render":
        print(render_file(args.trajectory))
        return

    print(f"[repowiki] ingesting {args.repo} ...")
    repo = ingest(args.repo)
    if repo.secret_findings:
        print(f"[repowiki] WARNING: secrets found and redacted from prompts: "
              f"{list(repo.secret_findings)}")
    idx = build_index(repo)
    print(f"[repowiki] {len(repo.files)} files, {len(idx.symbols)} symbols, "
          f"{len(idx.modules)} modules")

    if args.cmd == "index":
        print(render_repo_map(idx))
        return

    out = Path(args.out) if args.out else ROOT / "examples" / f"{repo.name}-{args.mode}"
    traj = Trajectory(ROOT / "trajectories", f"{repo.name}-{args.mode}")
    llm = LLM(model=args.model, trajectory=traj)

    if args.mode == "baseline":
        stats = generate_baseline(idx, out, llm, traj)
    else:
        from .advanced import generate_advanced
        stats = generate_advanced(idx, out, llm, traj)

    print(f"[repowiki] wrote {stats['pages']} pages to {out}")
    print(f"[repowiki] {stats['llm_calls']} LLM calls, ${stats['cost_usd']:.4f}, "
          f"{stats['wall_s']}s, citations: {stats.get('citations',0)} "
          f"({stats.get('unresolved',0)} unresolved)")
    print(f"[repowiki] trajectory: {traj.path}")


if __name__ == "__main__":
    main()
