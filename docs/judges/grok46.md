# Judge: grok46 (x-ai/grok-4.6)
_Role: red-team · 2026-08-31 05:37 UTC_

# Red-team critique: `repowiki`

**Reproducibility: 6/15.** Gate most likely to DQ: **Integrity (measurement honesty / citation contract)** — not “didn’t use an agent.”

---

## 1. Verdict

The cite-by-symbol idea is the right engineering split, but the submitted contract is already broken: the resolver will emit **wrong-but-valid** line ranges, the scorer can be gamed into a lying comparison table, the 10-repo eval is **19/20 runs** with a missing fastapi baseline, and this bundle cannot reproduce the claimed system (truncated generator, no `secrets.py` / ingest / parse / baseline / runner, no trajectories).

---

## 2. Score breakdown (with evidence)

Assumed challenge-shaped rubric. Harsh on gates, not on taste.

| Axis | Score | Evidence |
|---|---|---|
| Problem fit / wiki completeness | 10/15 | Page types map the brief (overview, architecture, modules, data-flow, onboarding, glossary). fastapi module coverage **0.04** after the 12-cluster cap — the “challenging” repo is the one they chose not to document. |
| Grounding / citation contract | 6/20 | Design says the model never emits coordinates and unresolved cites cannot ship. Code does the opposite on three paths (degrade-to-file, suffix/simple-name aliasing, repair gives up after 3). click advanced **validity 0.78**. |
| Baseline vs advanced (measured Δ) | 8/15 | Depth +0.69–0.83 is real and the interesting number. Validity Δ is **not** uniformly positive (click −0.18, httpx −0.05). README headline **+0.04 validity / 0.96** averages away regressions. Readability collapses on httpx/packaging to **0.00** and is buried. |
| Eval design (≥10, one hard, deterministic scorer) | 7/15 | 10 repos, fastapi called out, no LLM-as-judge — good. Then: **19 runs not 20**, fastapi baseline absent, scorer substring/`backtick` holes, `validate()` in the repair loop scores **raw** text not the emitted page. |
| Integrity / safety | 4/15 | `secrets.py` is **not in the bundle**. Secret-scan-before-prompt is an unfalsifiable claim here. Resolver + scorer both mint “valid” citations that are not the cited fact. |
| Trajectories / audit | 5/10 | Schema is described well (`llm_call`, `citation`, `repair`). **No `trajectories/*.jsonl` in the bundle.** Coding-agent transcript claimed, not present. Claims are not inspectable. |
| **Reproducibility** | **6/15** | See below. |
| Docs / narrative | 11/15 | DESIGN/CHANGELOG/REPRODUCE are unusually self-aware (harness bugs, src-layout). That credit is spent by overclaiming (“cannot contain a hallucinated path or range”) after the eval proves it can. |

### Reproducibility 6/15 — why not higher

**What they got right**
- Stdlib `ast`, no tree-sitter wheels for judges.
- Model slug + date + temp 0 in `evals/report.md`.
- Deterministic scorer *in principle*.
- Honest-ish limitations (Python-deep, 4 MB cap, under-claim on metaprogramming).

**What breaks a clean-room rerun**
1. **Bundle is not the product.** `advanced.py` ends mid-prompt (`Write architecture.md: c`). Missing: `ingest.py`, `parse.py`, `secrets.py`, `baseline.py`, `llm.py`, `evals/runner.py`, `requirements.txt`, `.env.example`. A judge cannot run `python -m repowiki generate`.
2. **Time/cost instructions are false as written.** `docs/REPRODUCE.md` lead: “full evaluation in **~20 minutes**”, “**< $0.50**”. Summing *their* table: sequential wall ≈ **2.25 hours**; cost ≈ **$0.58** even without fastapi baseline. Section 5 quietly shrinks “full eval” to two repos. That’s a reproducibility footgun: judges will either timeout or think they failed setup.
3. **19 ≠ 20.** README: “10 public repos × 2 modes (20 runs)”. Report: “19 runs”. fastapi baseline gone, no sentence why. You cannot reproduce the published comparison for the designated hard case.
4. **Nondeterminism is waved through.** They tell you numbers “will wobble” at temp 0. No pinned prompts-as-artifacts, no example wikis, no `report.json`, no trajectory hashes. Direction-of-delta is the only reproducible claim — and even that fails on validity for click/httpx.
5. **Placeholder in the official repro command:** `<starter-repo-url>`.
6. **Trajectories are non-falsifiable from this packet.** “Every in-product LLM call” is a property of files that are not here.

A 6 is “serious attempt, not a judge-runnable submission.”

---

## 3. The 3 most likely reasons this loses (ranked)

### 1) Integrity DQ: the citation contract does not hold (and the scorer will not catch it)

**Wrong-but-valid citation (resolver).** In `citations.resolve` for `path_symbol`:

```python
elif path in have:
    c.status, c.file = "ok", path   # degrade gracefully to file-level
    c.line_start, c.line_end = 1, idx.file_lines(path)
```

Then `Citation.render()` for *any* ok `symbol` / `path_symbol`:

```python
return f"`{self.file}:{self.line_start}-{self.line_end}`"
```

So `[src/orders/main.py::create_order]` when `create_order` is missing still ships as `` `src/orders/main.py:1-847` ``. Looks like a precise span. Validator treats `1 <= a <= b <= n+5` as success. Repair loop never fires. **This is the exact failure mode they said they structurally eliminated.**

**Wrong-but-valid citation (index aliases).** `RepoIndex.resolve`:

- unique **simple name** → that one symbol, even if the LLM meant a different `run`/`get`/`app`;
- `q.endswith("." + ref)` unique suffix → `[[sym:api.request]]` can bind a different package’s `*.api.request`;
- leftover path fallback maps a cite onto the **module** symbol (usually the whole file) and still renders a range.

Collision policy is “keep first, drop the rest.” First AST win becomes gospel.

**Repair does not verify the artifact that ships.** `_gen_with_repair` runs `validate(resp.text)` on the **raw** model output, then returns `body` from `resolve_all`. After 3 attempts it **always writes the page**. Unresolved cites become `` `[[sym:nope]]` *(unresolved citation)* ``. click 0.78 is the proof. README/AGENTS: “emitted wiki cannot contain a citation the tree doesn’t support” is false.

### 2) You can construct a repo where the eval lies

`quality.score_wiki` is deterministic and **not honest**.

**Fake citation validity / depth**
- Any inline `` `foo.py` `` whose path exists is counted as a valid file citation (`ok_c += 1`), even if it is not a citation.
- Any `` `path:a-b` `` in backticks counts as a *symbol-level* cite. The degrade-to-whole-file trick above farms **citation_depth**.
- `+5` line slack: `b <= n + 5` is still ok.
- `validate()` / `extract()` skip fenced blocks; the scorer’s rendered-form regex does **not** skip fences. Mermaid/code samples can mint extra “citations.”

**Fake symbol coverage**

```python
if q.split(".")[-1] in all_text:
    cited_pub += 1
```

Substring, no word boundary. Public symbols named `get`, `data`, `app`, `in`, `test` saturate coverage without being cited. A hostile fixture repo of `def data(): ...` / `def get(): ...` plus a wiki that says “the app gets data” prints **symbol_coverage ≈ 1.0**.

**Fake module coverage**
Coverage is filename identity: `module-{dir-with-dashes}` in `pages`. Empty files with the right stems would count. Conversely, the 12-cap makes fastapi **0.04** while baseline (missing!) would likely look like 1.00 from consolidation — an inverted “advanced is worse” story they avoided by omitting the run.

**Headline table is a spin layer.** Mean validity +0.04 with click −0.18 in the same file is not how you survive an integrity pass.

### 3) Reproducibility / completeness: judges cannot audit what you assert

- Secret scanner: **holes are total** in this packet — the module is missing. Classic regex scanners also miss split secrets, unusual prefixes, PEM in “skipped” binaries, JSON fixtures, `.env` if ingest only walks “code files.” You gave us nothing to even regex-audit.
- Trajectories: not attached → “every call logged” is unfalsifiable. That’s the grounding audit trail they pointed at for “30-point grounding.”
- Incomplete eval + truncated source + 20-minute lie = a judge either DQs on packet completeness or burns two hours and still cannot match 20 runs.

---

## 4. The 3 highest-leverage fixes (what would move the score)

1. **Make “ok” mean “this span is the thing named.”** Delete path_symbol file-level degrade (or render it as file-only, never `:1-EOF`). Require exact qualname **or** `(path, name)` hit; unique-suffix / unique-simple-name should be repair hints, not silent binds. Reject on collision. Validate **emitted** markdown (`body`), not `resp.text`. **Do not write the page** if problems remain — drop the claim or the cite. Add unit tests: wrong name + real file; `[[sym:get]]` with two `get`s; suffix collision; cite inside/outside fences.

2. **Rescore like an adversary.** Citations = only resolver-emitted spans, with a provenance map page→cite→symbol (don’t regex backticks). Symbol coverage = qualname or intersecting **recorded** span, not `name in all_text`. Skip fences everywhere. Publish per-repo metrics **without** a cherry-picked mean; include fastapi **baseline**; explain 0.04 module coverage instead of hiding the empty cell. Frozen `examples/` + `trajectories/` + `evals/report.json` hashes.

3. **Ship a judge-runnable packet.** Untruncate `advanced.py`. Include ingest/parse/secrets/baseline/llm/evals. Replace “~20 minutes / full eval” with two-repo smoke (~5 min) vs 10-repo (~2.5 h, ~$0.60). Commit `secrets.py` with tests (AKIA, `ghp_`, PEM, Slack, high-entropy in JSON, secrets in comments, `.env`). Log redaction events in trajectories so the claim is falsifiable.

---

## 5. What would make this WIN

The gap to first prize is not “more pages” or a bigger model. It is **closing the loop they already named in the changelog**: *if the measurement is wrong, the improvement claim is worthless.*

A winning version of this exact idea:

- **A machine-checkable contract with teeth:** LLM outputs only `[[sym:qual]]` / `[path]`; resolver either attaches the *unique index span for that symbol* or the page fails closed. No whole-file ranges dressed as symbol cites. Golden tests on a tiny adversarial repo (duplicate names, src-layout, metaprogramming, planted secrets, backtick filenames, mermaid `[[...]]`).
- **An eval that can lose.** Show click-style validity regressions in the README. Show fastapi baseline. Show that advanced wins on *depth + inspectability*, not a smoothed 0.96. Qualitative excerpts: one claim, one span, `git show` / file snippet in the writeup so a human can see grounding, not just 0.75.
- **Repro as a product:** `python -m evals.runner --fast` (2 repos, cached clones, committed expected metric bands) and `--full` with wall-clock honesty. Trajectories in-tree. `secrets.py` visible. No truncated files.
- **One extra week of substance they already listed:** drift-check CI (re-resolve all cites on HEAD; fail on rot) is the “this is a tool, not a weekend demo” move. Optional tree-sitter can wait; **failed-closed Python** beats **fuzzy five languages**.

Until the resolver cannot bless a wrong span and the scorer cannot be farmed with `def data()` and `` `app.py` ``, this is a strong blog post attached to a leaky harness — and integrity will DQ it before anyone argues about wiki taste.