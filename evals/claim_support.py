"""Claim-support evaluation — measures whether cited code SUPPORTS the prose claim.

This is the metric the resolver alone can't provide: not "does the span exist" but
"does the span back the sentence." A claim is extracted from the generated wiki, paired
with the exact cited lines, and judged SUPPORTED / PARTIAL / UNSUPPORTED / CONTRADICTED
by a model that sees ONLY the claim + the excerpt — never the generator's code, so the
generator can't grade itself.

Two modes:
  --mode llm    a second model judges each (claim, excerpt) pair  [default]
  --mode audit  emit a sampling sheet for blind human labeling

Usage:
  python -m evals.claim_support --wiki evals/wikis/requests-advanced --repo <url> \
      --sample 40 --judge-model anthropic/claude-opus-5
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repowiki.index import build_index       # noqa: E402
from repowiki.ingest import ingest           # noqa: E402
from repowiki.llm import LLM                 # noqa: E402
from repowiki.trajectory import Trajectory   # noqa: E402

# a rendered symbol-level citation `path:a-b` sitting at the end of a sentence
SENT_CITE_RX = re.compile(r"([^.!?\n][^.\n]*?)`([A-Za-z0-9_\-./]+\.\w+):(\d+)-(\d+)`")

JUDGE_SYSTEM = """You are a meticulous fact-checker. You are given ONE factual claim about a codebase
and the EXACT source-code excerpt its author cited as evidence. Judge only whether the
excerpt supports the claim — not whether the claim is interesting or well-written.

Answer with EXACTLY one JSON object:
{"verdict": "SUPPORTED" | "PARTIAL" | "UNSUPPORTED" | "CONTRADICTED", "reason": "<=20 words"}

- SUPPORTED: the excerpt directly establishes the claim.
- PARTIAL: related evidence, but the claim is broader/more specific than shown.
- UNSUPPORTED: the excerpt does not establish the claim (real code, wrong referent).
- CONTRADICTED: the excerpt shows the claim is false."""


def extract_claims(wiki_dir: Path) -> list[dict]:
    """Pull (sentence, cited file, a, b) tuples from generated pages."""
    claims = []
    for page in sorted(wiki_dir.glob("*.md")):
        text = page.read_text(encoding="utf-8")
        # strip fences so diagram syntax isn't mined as claims
        text = re.sub(r"```.*?```", " ", text, flags=re.S)
        for m in SENT_CITE_RX.finditer(text):
            sentence = m.group(1).strip(" -*#`\t")
            if len(sentence) < 25:   # too short to be a real claim
                continue
            claims.append({"page": page.stem, "claim": sentence,
                           "file": m.group(2),
                           "a": int(m.group(3)), "b": int(m.group(4))})
    return claims


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--sample", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260829)
    ap.add_argument("--mode", choices=["llm", "audit"], default="llm")
    ap.add_argument("--judge-model", default="deepseek/deepseek-chat-v3-0324")
    args = ap.parse_args()

    idx = build_index(ingest(args.repo))
    claims = extract_claims(Path(args.wiki))
    rng = random.Random(args.seed)
    sample = rng.sample(claims, min(args.sample, len(claims)))
    print(f"[claim-support] {len(claims)} claims found, sampling {len(sample)}")

    def excerpt(c):
        lines = idx.content_at(c["file"], c["a"], c["b"])
        if len(lines) > 1800:  # big class spans: head + tail
            lines = lines[:900] + "\n...\n" + lines[-600:]
        return lines

    if args.mode == "audit":
        out = ROOT / "evals" / "claim_audit_sheet.md"
        rows = ["# Blind claim-support audit sheet\n",
                "Label each SUPPORTED / PARTIAL / UNSUPPORTED / CONTRADICTED.\n"]
        for i, c in enumerate(sample):
            rows.append(f"\n## Claim {i+1} ({c['page']})\n> {c['claim']}\n\n"
                        f"Cited: `{c['file']}:{c['a']}-{c['b']}`\n```\n{excerpt(c)}\n```\n"
                        "Verdict: ")
        out.write_text("\n".join(rows))
        print(f"[claim-support] wrote audit sheet -> {out}")
        return

    llm = LLM(model=args.judge_model,
              trajectory=Trajectory(ROOT / "trajectories", "claim-support-judge"))
    verdicts = []
    for i, c in enumerate(sample):
        user = f"CLAIM:\n{c['claim']}\n\nCITED EXCERPT ({c['file']}:{c['a']}-{c['b']}):\n```\n{excerpt(c)}\n```"
        resp = llm.chat(JUDGE_SYSTEM, user, max_tokens=200, purpose=f"claim{i}")
        m = re.search(r"\{.*\}", resp.text, re.S)
        v = {"verdict": "PARSE_ERROR", "reason": resp.text[:80]}
        if m:
            try:
                v = json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        verdicts.append({**c, **v})
        print(f"[{i+1}/{len(sample)}] {v['verdict']:12s} {c['claim'][:60]}")

    from collections import Counter
    tally = Counter(v["verdict"] for v in verdicts)
    n = len(verdicts)
    precision = (tally.get("SUPPORTED", 0) + 0.5 * tally.get("PARTIAL", 0)) / max(1, n)
    out = {
        "wiki": args.wiki, "repo": args.repo, "judge_model": args.judge_model,
        "n": n, "tally": dict(tally),
        "claim_support_precision": round(precision, 3),
        "verdicts": verdicts,
    }
    out_path = ROOT / "evals" / "claim_support.json"
    out_path.write_text(json.dumps(out, indent=1))
    print(f"\n[claim-support] precision {precision:.2f} over {n} claims "
          f"(SUPPORTED {tally.get('SUPPORTED',0)}, PARTIAL {tally.get('PARTIAL',0)}, "
          f"UNSUPPORTED {tally.get('UNSUPPORTED',0)}, CONTRADICTED {tally.get('CONTRADICTED',0)})")
    print(f"[claim-support] wrote {out_path}")


if __name__ == "__main__":
    main()
