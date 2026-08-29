"""Parallel eval: shard repos × modes across N worker processes.

Each worker runs a disjoint set of (repo, mode) pairs via evals.runner internals;
results merge into evals/report.json + report.md. 4x wall-clock speedup at the cost of
parallel API load — deepseek tolerates it.
"""
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evals.runner import DEFAULT_REPOS, comparison_table  # noqa: E402


def one_job(repo: str, mode: str) -> dict:
    """Subprocess per (repo, mode) — isolates LLM clients, crashes don't kill the pool."""
    code = (
        "import json,sys; sys.path.insert(0, r'%s');"
        "from evals.runner import run_one;"
        "r = run_one(%r, %r, None);"
        "print('RESULT_JSON:' + json.dumps(r))"
    ) % (str(ROOT), repo, mode)
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                         capture_output=True, text=True, timeout=1800)
    for line in out.stdout.splitlines():
        if line.startswith("RESULT_JSON:"):
            return json.loads(line[len("RESULT_JSON:"):])
    raise RuntimeError(f"no result for {repo}/{mode}: {out.stderr[-500:]}")


def main(workers: int = 4):
    jobs = [(r, m) for r in DEFAULT_REPOS for m in ("baseline", "advanced")]
    results = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(one_job, r, m): (r, m) for r, m in jobs}
        for fut in as_completed(futs):
            r, m = futs[fut]
            try:
                res = fut.result()
                results.append(res)
                s, g = res["scores"], res["gen"]
                print(f"[done {len(results)}/{len(jobs)}] {res['repo']}/{m}: "
                      f"validity={s['citation_validity']:.2f} depth={s['citation_depth']:.2f} "
                      f"cost=${g['cost_usd']:.4f} {res['wall_s']}s", flush=True)
            except Exception as e:
                print(f"[FAIL] {r}/{m}: {e}", flush=True)
    results.sort(key=lambda x: (x["repo"], x["mode"]))
    (ROOT / "evals" / "report.json").write_text(json.dumps(results, indent=1))

    report = ["# Evaluation Report\n",
              f"Generated: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
              f"Model: deepseek/deepseek-chat-v3-0324 (temp 0) | "
              f"{len(DEFAULT_REPOS)} repos x 2 modes | parallel x{workers}\n",
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
    print(f"[eval] {len(results)}/{len(jobs)} ok in {time.time()-t0:.0f}s -> evals/report.md")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
