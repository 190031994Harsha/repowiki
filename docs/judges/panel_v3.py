"""Judge panel v3 — empirical, not rhetorical.

v1 = same bundle, 8 opinions.  v2 = distinct lenses, fresh evidence.
v3 = judges that DO things: execute the code on adversarial inputs, diff the two
     generators line-by-line, recompute every published number, audit every absolute
     claim, grade the video script against the rubric's own wording.

Run:    python docs/judges/panel_v3.py
Watch:  python docs/judges/panel_v3.py --status
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import os
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / "v3"
OUT.mkdir(exist_ok=True)
STATUS = OUT / "status.json"
_lock = threading.Lock()
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")


def _set(mid, **kw):
    with _lock:
        s = json.loads(STATUS.read_text()) if STATUS.exists() else {}
        s.setdefault(mid, {}).update(kw)
        STATUS.write_text(json.dumps(s, indent=1))


def _read(rel, cap=9000):
    p = ROOT / rel
    return f"\n===== {rel} =====\n{p.read_text(encoding='utf-8')[:cap]}" if p.exists() else f"\n(missing: {rel})"


def _run_snippet(code: str) -> str:
    """Execute a PoC a judge proposed, return stdout/stderr. This is what makes v3
    empirical: a claimed bug is CONFIRMED or REFUTED by running it."""
    try:
        r = subprocess.run([PY, "-c", code], cwd=ROOT, capture_output=True, text=True,
                           timeout=60)
        return (r.stdout + r.stderr).strip()[:1500]
    except Exception as e:
        return f"EXEC ERROR: {e}"


# Pre-computed empirical facts we hand to the judges so they argue from data, not vibes.
def _empirical_facts() -> str:
    facts = []
    # F1: does the resolver still bind wrong-but-valid on ambiguous same-file symbols?
    code1 = '''
import sys; sys.path.insert(0, ".")
from repowiki.parse import parse_python
from repowiki.ingest import Repo, RepoFile
from repowiki.index import build_index
from repowiki.citations import resolve_all
from pathlib import Path
import tempfile, os
d = tempfile.mkdtemp()
Path(d, "ops.py").write_text("class A:\\n    def run(self):\\n        return 1\\nclass B:\\n    def run(self):\\n        return 2\\n")
repo = Repo(source=d, root=Path(d), name="t")
repo.files = [RepoFile("ops.py", "Python", 100, 6, Path(d,"ops.py").read_text())]
idx = build_index(repo)
print("symbols:", sorted(idx.symbols))
text = "B.run returns 2. [ops.py::run]"
rendered, cites = resolve_all(text, idx)
print("rendered:", rendered)
print("statuses:", [(c.ref, c.status) for c in cites])
'''
    facts.append("PoC A (same-file ambiguity):\n" + _run_snippet(code1))
    # F2: src/lib alias
    code2 = '''
import sys; sys.path.insert(0, ".")
from repowiki.ingest import Repo, RepoFile
from repowiki.index import build_index
from repowiki.citations import resolve_all
from pathlib import Path
import tempfile
d = tempfile.mkdtemp()
Path(d, "src").mkdir(); Path(d, "lib").mkdir()
Path(d,"src/foo.py").write_text("class Bar:\\n    origin=1\\n")
Path(d,"lib/foo.py").write_text("class Bar:\\n    origin=2\\n")
repo = Repo(source=d, root=Path(d), name="t")
repo.files = [RepoFile("src/foo.py","Python",50,2,Path(d,"src/foo.py").read_text()),
              RepoFile("lib/foo.py","Python",50,2,Path(d,"lib/foo.py").read_text())]
idx = build_index(repo)
print("symbols:", sorted(idx.symbols))
rendered, cites = resolve_all("uses [[sym:foo.Bar]]", idx)
print("rendered:", rendered)
'''
    facts.append("PoC B (src/lib alias):\n" + _run_snippet(code2))
    return "\n\n".join(facts)


FACTS = _empirical_facts()

PANEL = [
    {"id": "exec", "model": "openai/gpt-5.6-sol", "max_tokens": 16000,
     "bundle": _read("repowiki/citations.py", 8000) + _read("repowiki/index.py", 6000),
     "prompt": f"""Adversarial execution. I RAN two exploit PoCs against the current resolver. Real output:

{FACTS}

Analyze the ACTUAL output: did the v2 fixes close the ambiguity holes? For each PoC say
CONFIRMED-STILL-BROKEN or FIXED, with the line of output that proves it. Then propose ONE
new adversarial input (different mechanism: unicode names, deeply nested classes, re-exported
symbols, circular imports) most likely to still break it. Be concrete."""},

    {"id": "fairness", "model": "deepseek/deepseek-v4-pro", "max_tokens": 16000,
     "bundle": _read("repowiki/baseline.py", 5000) + _read("repowiki/advanced.py", 6000)
               + _read("evals/report.md", 5000),
     "prompt": """Diff-audit the baseline vs advanced. The measured-improvement claim rests on the
baseline being a FAIR 'reasonable basic approach', not a strawman. Line-by-line:

- Does baseline get the same model, same file contents, same symbol access? (grep for what each sees)
- Is the baseline's system prompt written to fail (e.g. told to cite file-level only while advanced
  is told to cite symbols)?
- Is _grep_upgrade a genuine attempt at line ranges or a token gesture?
- List every asymmetry between the two paths and judge each: justified-by-design or unfair?
Verdict: is the baseline a fair measuring stick, and if not, what's the ONE change that makes it fair?"""},

    {"id": "repro", "model": "google/gemini-3.1-pro-preview", "max_tokens": 14000,
     "bundle": _read("README.md", 6000) + _read("docs/REPRODUCE.md", 5000)
               + _read("requirements.txt", 500) + _read("Makefile", 1000),
     "prompt": """Blind reproducibility audit. You have ONLY the README + REPRODUCE + requirements.txt a
judge would see. You cannot run anything.

Walk the exact steps a judge would follow from a clean machine. At each step, name what could fail or
confuse: missing prerequisites, wrong commands, placeholders, assumed knowledge, OS-specific assumptions,
cost surprises, time surprises. Does the README's own eval command actually work as written? Does the
claimed output match what the commands produce? Score Reproducibility /15 and list every friction point
in order a judge would hit them."""},

    {"id": "absolutes", "model": "moonshotai/kimi-k3", "max_tokens": 14000,
     "bundle": _read("README.md", 7000) + _read("AGENTS.md", 2500),
     "prompt": """Absolute-claim audit. Extract EVERY absolute or near-absolute claim in the README and
AGENTS.md — every 'cannot', 'never', 'every', 'guarantee', 'no hallucination', 'verifiable', 'cannot
silently drift', 'exact'. For each: is it literally true given how the code works, technically-true-but-
misleading, or false? The project just got bitten by one false absolute ('cannot contain a citation the
tree doesn't support' while render() had an unresolved branch). Find the NEXT one a hostile judge kills
them with. Quote it exactly."""},

    {"id": "linereview", "model": "anthropic/claude-opus-5", "max_tokens": 16000,
     "bundle": _read("repowiki/parse.py", 7000) + _read("repowiki/claim_extract.py", 2500)
               + _read("repowiki/quality.py", 6000),
     "prompt": """Line-by-line engineering review of the deterministic core, as a staff engineer doing a
merge review. Not 'is it clever' — 'would you approve this PR'. Find concrete bugs: off-by-ones in line
ranges, silent exception swallowing, regex edge cases, state leaks between runs, thread-safety, integer
overflow on huge files, encoding issues. For each: file:line, the triggering input, the wrong output.
Rank by severity. The goal is a list a judge could verify in 5 minutes."""},

    {"id": "video", "model": "x-ai/grok-4.6", "max_tokens": 12000,
     "bundle": _read("docs/VIDEO_SCRIPT.md", 3000) + _read("README.md", 4000)
               + _read("docs/CHANGELOG.md", 4000),
     "prompt": """Grade the 5-minute video script as a judge who will watch 200 of these. The rubric says:
begin with problem+baseline, walk ONE realistic execution end-to-end, show the final comparison, explain
the changelog, highlight the biggest win + one removed experiment.

Does this script DO those things, in that order, in 5 minutes? What will a tired judge remember at the
end? What's the single strongest 15 seconds — and is it early enough? Rewrite the weakest beat. Be brutal
about pacing: where does attention drop?"""},

    {"id": "win2", "model": "qwen/qwen3-max-thinking", "max_tokens": 14000,
     "bundle": _read("README.md", 5000) + _read("docs/judges/v2/SYNTHESIS.md", 5000)
               + _read("docs/DESIGN.md", 4000),
     "prompt": """You scored this 87/100 in v1 — the highest by far. The other 7 judges scored 43-67.
Defend or retract: was 87 naive (you read claims, they read code)? Now with the v2 fixes (readable
citations, verifier agent, showcase, corrected aggregates), what's your honest score and the single
biggest remaining gap to a 95+ first-prize submission? If you still score higher than the pack, explain
what you're seeing that they missed."""},
]


def judge(spec):
    mid = spec["id"]
    _set(mid, status="starting", model=spec["model"], started=time.time())
    prompt = spec["prompt"] + "\n\nEVIDENCE:\n" + spec["bundle"]
    body = {"model": spec["model"], "messages": [{"role": "user", "content": prompt}],
            "max_tokens": spec["max_tokens"], "temperature": 0.2}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY','')}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/190031994Harsha/repowiki",
                 "X-Title": "repowiki judge panel v3"})
    t0 = time.time()
    try:
        _set(mid, status="waiting_on_api")
        with urllib.request.urlopen(req, timeout=900) as r:
            data = json.load(r)
        msg = data["choices"][0]["message"]
        text = msg.get("content") or msg.get("reasoning", "") or json.dumps(data)[:500]
        (OUT / f"{mid}.md").write_text(
            f"# Judge v3: {mid} ({spec['model']})\n_{time.strftime('%Y-%m-%d %H:%M UTC')}_\n\n{text}",
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
    print(f"[panel v3] {len(PANEL)} empirical judges, parallel")
    print("[panel v3] PoC facts pre-computed:")
    print(FACTS[:600])
    with cf.ThreadPoolExecutor(max_workers=len(PANEL)) as ex:
        futs = {ex.submit(judge, s): s["id"] for s in PANEL}
        for f in cf.as_completed(futs):
            r = f.result()
            print(f"[panel v3] {r['id']}: {'OK '+str(r.get('chars',''))+' chars' if r['ok'] else 'FAIL '+r.get('err','')}")
    print("[panel v3] done -> docs/judges/v3/")


if __name__ == "__main__":
    main()
