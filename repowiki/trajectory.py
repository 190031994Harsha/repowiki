"""Trajectory logging for in-product agents.

One JSONL file per run in trajectories/. Records every agent decision, LLM call,
citation resolution, and verification result — the submission's required
agent-trajectory evidence for the product's own agents. (The coding-agent trajectory
is the Claude Code session transcript, disclosed separately in AGENTS.md.)
"""
from __future__ import annotations

import json
import time
from pathlib import Path


class Trajectory:
    def __init__(self, out_dir: Path, run_name: str):
        out_dir.mkdir(parents=True, exist_ok=True)
        self.path = out_dir / f"{run_name}-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
        self.t0 = time.time()
        self._n = 0

    def event(self, kind: str, data: dict):
        self._n += 1
        rec = {"seq": self._n, "t": round(time.time() - self.t0, 2), "kind": kind, **data}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def render(self) -> str:
        """Human-readable rendering of this trajectory."""
        lines = []
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            r = json.loads(raw)
            k = r["kind"]
            if k == "llm_call":
                lines.append(f"[{r['t']:7.1f}s] LLM {r.get('purpose','')} "
                             f"({r.get('input_tokens',0)}->{r.get('output_tokens',0)} tok, "
                             f"${r.get('cost_usd',0):.4f})")
            elif k == "citation":
                lines.append(f"[{r['t']:7.1f}s] cite {r.get('ref','')} -> {r.get('status','')}")
            else:
                summary = {k2: v for k2, v in r.items() if k2 not in
                           ("seq", "t", "kind", "system", "user", "response")}
                lines.append(f"[{r['t']:7.1f}s] {k}: {json.dumps(summary)[:200]}")
        return "\n".join(lines)


def render_file(path: str | Path) -> str:
    t = Trajectory.__new__(Trajectory)
    t.path = Path(path)
    return t.render()
