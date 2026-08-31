"""Judge panel v2 — deeper, distinct lenses, fresh evidence.

Differences from v1 (which all 8 judges read the same bundle and converged on F1-F5):
  - each judge gets a DIFFERENT evidence bundle tuned to its lens
  - integrity judge gets a runnable PoC target (resolver source) to break
  - user judge gets a full generated wiki, not the README's claims about it
  - claim-audit judge gets the README's own assertive sentences to verify against code

Run:    python docs/judges/panel_v2.py
Watch:  python docs/judges/panel_v2.py --status
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / "v2"
OUT.mkdir(exist_ok=True)
STATUS = OUT / "status.json"
_lock = threading.Lock()


def _set(mid, **kw):
    with _lock:
        s = json.loads(STATUS.read_text()) if STATUS.exists() else {}
        s.setdefault(mid, {}).update(kw)
        STATUS.write_text(json.dumps(s, indent=1))


def _read(rel, cap=9000):
    p = ROOT / rel
    return f"\n===== {rel} =====\n{p.read_text(encoding='utf-8')[:cap]}" if p.exists() else f"\n(missing: {rel})"


def _wiki_sample(repo="requests", mode="advanced", pages=("overview.md", "module-src-requests.md")):
    parts = []
    for pg in pages:
        p = ROOT / "evals" / "wikis" / f"{repo}-{mode}" / pg
        if p.exists():
            parts.append(f"\n--- generated page: {pg} ---\n{p.read_text(encoding='utf-8')[:6000]}")
    return "\n".join(parts)


def _readme_claims():
    """The README's own assertive sentences, for claim-by-claim verification."""
    import re
    txt = (ROOT / "README.md").read_text(encoding="utf-8")
    sents = re.findall(r"^\s*[-*]?\s*\*\*([A-Z][^*\n]{20,200})\*\*", txt, re.M)
    sents += [l.strip("- ") for l in txt.split("\n")
              if "cannot" in l.lower() or "guarantee" in l.lower() or "100%" in l]
    return "\n".join(f"- {s}" for s in dict.fromkeys(sents))[:4000]


COMMON = _read("README.md", 6000) + _read("evals/report.md", 6000)

PANEL = [
    {"id": "integrity", "model": "openai/gpt-5.6-sol", "max_tokens": 16000,
     "bundle": _read("repowiki/citations.py", 8000) + _read("repowiki/index.py", 7000)
               + _read("evals/report.md", 5000),
     "prompt": """Red-team the citation contract. I want a CONCRETE proof-of-concept failure, not a vibe.

Given citations.py and index.py, construct a specific input (a generated sentence + citation) where
the resolver returns status=ok with a WRONG-but-valid line range, or where score_wiki inflates a metric.
Trace the exact code path. If you claim degrade-to-file or alias-binding is exploitable, show the inputs.
Then say whether the post-fix system (fail-closed, resolver teeth) actually closes it.

End with: INTEGRITY VERDICT — does any path still emit a wrong-but-valid citation? yes/no + the path."""},

    {"id": "agentic", "model": "anthropic/claude-fable-5", "max_tokens": 16000,
     "bundle": _read("repowiki/advanced.py", 9000) + _read("docs/DESIGN.md", 5000)
               + _read("repowiki/baseline.py", 3000),
     "prompt": """Judge the AGENTIC depth, not the prose. The rubric's 30 points reward agents that plan,
use tools, remember, verify, and orchestrate.

Is this a real multi-agent system or a batch pipeline with extra steps? Specifically:
- Does the planner actually plan, or is the output predetermined by backfill + fixed core pages?
- Do the per-module 'agents' share state / build on each other, or are they N independent calls?
- Is there real verification-driven iteration, or a fixed 3-retry loop?
- What is the strongest agentic capability ABSENT that a winning submission would have?
Score Agent Solution & Engineering /30 with specific line references. Then name the ONE orchestration
upgrade that would most change your score."""},

    {"id": "rubric", "model": "anthropic/claude-opus-5", "max_tokens": 16000,
     "bundle": COMMON + _read("docs/CHANGELOG.md", 7000) + _read("docs/REPRODUCE.md", 3000),
     "prompt": """Score all 6 rubric criteria with the OFFICIAL points (15/30/20/15/15/5). This is v2 of the
submission — the v1 judge critiques (cherry-picked table, missing fastapi baseline, no claim-support
measurement, fail-open citations, all-Python eval) were shown to the authors and fixed. Verify each fix
is REAL in the bundle, not just claimed in the changelog. For each: fixed / partially / not addressed +
evidence. Then a calibrated total /100 and the cheapest remaining points."""},

    {"id": "user", "model": "google/gemini-3.1-pro-preview", "max_tokens": 14000,
     "bundle": _wiki_sample() + _read("README.md", 3000),
     "prompt": """You are the intended user: a new engineer who inherited the 'requests' codebase. You are
NOT reading marketing — you are reading the ACTUAL generated wiki pages below.

Use them as your only reference. Would you trust this enough to make your first commit? Does it answer:
where do I start, what are the load-bearing pieces, what breaks if I change Session.send? What's the most
useful page? What's missing that you need on day one? Score End-to-End Quality /20 as a user.
Be concrete about which specific pages/sentences helped or failed you."""},

    {"id": "correctness", "model": "deepseek/deepseek-v4-pro", "max_tokens": 16000,
     "bundle": _read("repowiki/parse.py", 7000) + _read("repowiki/index.py", 5000)
               + _read("repowiki/quality.py", 6000),
     "prompt": """You are a static-analysis expert auditing the deterministic layer for correctness bugs that
the LLM judges would miss. Trace the actual logic:

- parse.py: where does the Python ast parser silently drop symbols or call edges? What about nested
  functions, lambdas, decorators, async, classmethods? Find a concrete case it mis-parses.
- index.py: is module clustering by directory correct for nested src layouts? When does resolve() return
  the WRONG symbol (not just None)?
- quality.py: find a specific input that makes a metric report a wrong-but-confident number.
Give me 3 concrete bugs with the exact line + input that triggers each, ranked by severity."""},

    {"id": "claimaudit", "model": "moonshotai/kimi-k3", "max_tokens": 16000,
     "bundle": _readme_claims() + _read("repowiki/advanced.py", 4000) + _read("repowiki/citations.py", 4000),
     "prompt": """Claim-by-claim audit. Below are the README's assertive sentences. For EACH, verify against
the provided source whether it is literally true, technically-true-but-misleading, or false. Pay special
attention to absolute claims (cannot, guarantee, every, never, 100%).

Then: which single README sentence would a hostile judge quote to disqualify this submission, and why?"""},

    {"id": "winstrategy", "model": "x-ai/grok-4.6", "max_tokens": 14000,
     "bundle": COMMON + _read("docs/CHANGELOG.md", 6000) + _read("AGENTS.md", 2000),
     "prompt": """Forget scoring. Tell me how this WINS first prize and the 50 paid opportunities.

The field will be full of RAG doc-generators and 'AI explains code' wrappers. What does this submission
have that they don't, and what is it missing that the winner will have? Be specific about the ONE
differentiating move available in the remaining ~24h that most separates this from the field — something
that makes a judge say 'I have not seen that before.' Consider: what's the demo moment, the one-liner,
the artifact a judge screenshots?"""},

    {"id": "skeptic2", "model": "qwen/qwen3-max-thinking", "max_tokens": 16000,
     "bundle": COMMON + _read("evals/report.md", 5000) + _read("docs/CHANGELOG.md", 5000),
     "prompt": """Hostile re-review of v2. The authors CLAIM to have fixed the v1 critiques. Assume they are
overstating the fixes. Find: (a) a fix that is claimed but doesn't actually hold up under the code,
(b) a NEW problem introduced by the fixes (fail-closed dropping sentences, grep-upgrade baseline,
claim-support LLM judge), and (c) the most gameable remaining metric. Verify against evals/report.md
numbers, not the changelog's self-report."""},
]


def judge(spec, bundle_extra):
    mid = spec["id"]
    _set(mid, status="starting", model=spec["model"], started=time.time())
    prompt = spec["prompt"] + "\n\nEVIDENCE BUNDLE:\n" + spec["bundle"] + bundle_extra
    body = {"model": spec["model"], "messages": [{"role": "user", "content": prompt}],
            "max_tokens": spec["max_tokens"], "temperature": 0.2}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY','')}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/190031994Harsha/repowiki",
                 "X-Title": "repowiki judge panel v2"})
    t0 = time.time()
    try:
        _set(mid, status="waiting_on_api")
        with urllib.request.urlopen(req, timeout=900) as r:
            data = json.load(r)
        msg = data["choices"][0]["message"]
        text = msg.get("content") or ""
        if not text:  # some reasoning models put it elsewhere
            text = msg.get("reasoning", "") or json.dumps(data)[:500]
        (OUT / f"{mid}.md").write_text(
            f"# Judge v2: {mid} ({spec['model']})\n_{time.strftime('%Y-%m-%d %H:%M UTC')}_\n\n{text}",
            encoding="utf-8")
        _set(mid, status="done", wall_s=round(time.time()-t0,1),
             tokens=data.get("usage",{}).get("total_tokens"))
        return {"id": mid, "ok": True, "chars": len(text)}
    except Exception as e:
        _set(mid, status="error", error=repr(e)[:200])
        return {"id": mid, "ok": False, "err": repr(e)[:150]}


def status():
    if not STATUS.exists():
        print("no status"); return
    for mid, v in json.loads(STATUS.read_text()).items():
        line = f"{mid:12s} {v.get('status','?'):16s}"
        if v.get("wall_s"): line += f" {v['wall_s']}s"
        if v.get("tokens"): line += f" {v['tokens']} tok"
        if v.get("error"): line += f" ERR {v['error'][:50]}"
        print(line)


def main():
    import sys
    if "--status" in sys.argv:
        status(); return
    STATUS.write_text("{}")
    extra = _read("docs/judges/SYNTHESIS.md", 4000)  # v1 findings, so v2 verifies fixes not re-finds
    print(f"[panel v2] {len(PANEL)} judges, distinct lenses, parallel")
    with cf.ThreadPoolExecutor(max_workers=len(PANEL)) as ex:
        futs = {ex.submit(judge, s, extra): s["id"] for s in PANEL}
        for f in cf.as_completed(futs):
            r = f.result()
            print(f"[panel v2] {r['id']}: {'OK '+str(r.get('chars',''))+' chars' if r['ok'] else 'FAIL '+r.get('err','')}")
    print("[panel v2] done -> docs/judges/v2/")


if __name__ == "__main__":
    main()
