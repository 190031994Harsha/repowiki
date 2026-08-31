"""Adversarial judge panel — N frontier models critique repowiki in parallel.

Each model gets the submission bundle (README, DESIGN, CHANGELOG, eval report, key
source files) + a role, and writes a critique doc. A shared status file is updated
live so you can watch progress / spot a stall.

Run:    python docs/judges/panel.py
Watch:  python docs/judges/panel.py --status     (or just read docs/judges/status.json)
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import os
import threading
import time
from pathlib import Path

import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
STATUS = OUT / "status.json"
_status_lock = threading.Lock()

# The panel: one flagship per lab, each with a distinct judge role. Max thinking tokens.
PANEL = [
    {"id": "gpt55",      "model": "openai/gpt-5.5",                "role": "adversarial-lead",  "max_tokens": 16000},
    {"id": "gpt56sol",   "model": "openai/gpt-5.6-sol",            "role": "adversarial-lead",  "max_tokens": 16000},
    {"id": "opus5",      "model": "anthropic/claude-opus-5",       "role": "rubrics-scorer",    "max_tokens": 16000},
    # fable-5 blocked by OpenRouter data policy on this key; gpt-5.5 covers OpenAI flagship
    {"id": "kimik3",     "model": "moonshotai/kimi-k3",            "role": "skeptical-reviewer","max_tokens": 16000},
    {"id": "grok46",     "model": "x-ai/grok-4.6",                 "role": "red-team",          "max_tokens": 16000},
    {"id": "deepseekv4", "model": "deepseek/deepseek-v4-pro",      "role": "skeptical-reviewer","max_tokens": 16000},
    {"id": "gemini31",   "model": "google/gemini-3.1-pro-preview", "role": "enduser-realist",   "max_tokens": 16000},
    {"id": "qwen3max",   "model": "qwen/qwen3-max-thinking",       "role": "rubrics-scorer",    "max_tokens": 16000},
    {"id": "glm53",      "model": "z-ai/glm-5.3",                  "role": "agentic-engineer",  "max_tokens": 16000},
]

ROLES = {
    "adversarial-lead": """You are the LEAD JUDGE trying to REJECT this submission. Your job is to find
the fatal flaw: the thing that makes judges say 'impressive demo, not a real solution.'
Attack the problem choice, the novelty, whether 'improvement' is real or engineered,
and whether the citation-grounding claim survives scrutiny. Be specific, cite the repo.""",
    "agentic-engineer": """You are a senior agentic-systems engineer reviewing a peer's design. Judge the
ARCHITECTURE: is cite-by-symbol + deterministic resolver the right call vs embeddings/RAG?
Are the failure modes real or invented? Is the repair loop sound? What's the single
strongest improvement they DIDN'T make? Score Agent Solution & Engineering /30 honestly.""",
    "skeptical-reviewer": """You are a deeply skeptical technical reviewer who has seen a thousand 'LLM +
deterministic checker' projects. Assume the claims are overstated until proven. Verify:
does the eval actually measure grounding, or something that just correlates? Is the
baseline fair or a strawman? Would the numbers survive a hostile re-run? Score the
Measured Improvement /15 with suspicion.""",
    "rubrics-scorer": """You are a micro1 judge with the rubric. Score each of the 6 criteria out of its
points (15/30/20/15/15/5) with a one-line justification each, then a total. Be
calibrated: 100 means 'best submission I've ever seen', 70 means 'solid, forgettable'.
Identify the cheapest 10 points they're leaving on the table.""",
    "enduser-realist": """You are the intended user: a new engineer who just inherited this codebase. Ignore
the architecture; use ONLY the generated wiki pages. Would you actually read this? Does
it answer your real questions (where do I start, what breaks if I touch X, why is it
built this way)? What page is missing? Score End-to-End Quality /20 as a user, not an engineer.""",
    "red-team": """You are red-teaming this submission for the integrity + reproducibility gates. Try to
break it: Can you make the resolver produce a wrong-but-valid citation? Does the secret
scanner have holes? Can you construct a repo where the eval lies? Are the trajectory
claims falsifiable? Score Reproducibility /15 and name the gate most likely to DQ them.""",
}


def _set(mid: str, **kw):
    with _status_lock:
        s = json.loads(STATUS.read_text()) if STATUS.exists() else {}
        s.setdefault(mid, {}).update(kw)
        STATUS.write_text(json.dumps(s, indent=1))


def _read_bundle() -> str:
    """The submission as the judge sees it: docs + eval + key source, capped."""
    parts = []
    for rel in ["README.md", "docs/DESIGN.md", "docs/CHANGELOG.md", "docs/REPRODUCE.md",
                "AGENTS.md", "evals/report.md",
                "repowiki/citations.py", "repowiki/index.py", "repowiki/advanced.py",
                "repowiki/quality.py"]:
        p = ROOT / rel
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            parts.append(f"\n\n===== {rel} ({len(txt)} chars) =====\n{txt[:9000]}")
    return "\n".join(parts)


def judge(spec: dict, bundle: str) -> dict:
    mid = spec["id"]
    _set(mid, status="starting", model=spec["model"], started=time.time())
    prompt = f"""{ROLES[spec['role']]}

You are reviewing 'repowiki', a submission to the micro1 Agentic Workflows Hackathon
(Aug 2026). The full submission bundle follows. Read it critically, then write a
structured critique markdown doc with:

1. **Verdict** — one sentence, unsparing.
2. **Score breakdown** against the rubric, with evidence.
3. **The 3 most likely reasons this loses** — ranked, specific.
4. **The 3 highest-leverage fixes** — what would change your score most.
5. **What would make this WIN** — the gap between this and a first-prize submission.

Submission bundle:
{bundle}
"""
    body = {
        "model": spec["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": spec["max_tokens"],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY','')}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/190031994Harsha/repowiki",
                 "X-Title": "repowiki judge panel"})
    t0 = time.time()
    try:
        _set(mid, status="waiting_on_api")
        with urllib.request.urlopen(req, timeout=900) as r:
            data = json.load(r)
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        out = OUT / f"{mid}.md"
        out.write_text(f"# Judge: {mid} ({spec['model']})\n_Role: {spec['role']} · "
                       f"{time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}_\n\n{text}",
                       encoding="utf-8")
        _set(mid, status="done", wall_s=round(time.time() - t0, 1),
             tokens=usage.get("total_tokens"), out=str(out))
        return {"id": mid, "ok": True, "chars": len(text), "wall_s": round(time.time()-t0,1)}
    except Exception as e:
        _set(mid, status="error", error=repr(e)[:300], wall_s=round(time.time()-t0,1))
        return {"id": mid, "ok": False, "err": repr(e)[:200]}


def status_snapshot():
    if not STATUS.exists():
        print("no status yet")
        return
    s = json.loads(STATUS.read_text())
    for mid, v in s.items():
        line = f"{mid:10s} {v.get('status','?'):16s}"
        if v.get("wall_s"):
            line += f" {v['wall_s']}s"
        if v.get("tokens"):
            line += f" {v['tokens']} tok"
        if v.get("error"):
            line += f" ERR {v['error'][:60]}"
        print(line)


def main():
    if "--status" in os.sys.argv:
        status_snapshot()
        return
    OUT.mkdir(parents=True, exist_ok=True)
    STATUS.write_text("{}")
    bundle = _read_bundle()
    print(f"[panel] bundle {len(bundle)} chars, {len(PANEL)} judges in parallel")
    with cf.ThreadPoolExecutor(max_workers=len(PANEL)) as ex:
        futs = {ex.submit(judge, spec, bundle): spec["id"] for spec in PANEL}
        for fut in cf.as_completed(futs):
            r = fut.result()
            print(f"[panel] {r['id']}: {'OK' if r['ok'] else 'FAIL'} "
                  f"{r.get('chars','')}{' chars' if r['ok'] else r.get('err','')}")
    print("[panel] done. docs in docs/judges/")


if __name__ == "__main__":
    main()
