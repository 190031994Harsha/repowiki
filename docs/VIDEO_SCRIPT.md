# Demo Video Script (≤5:00)

Terminal left, generated wiki (Obsidian/VS Code markdown preview) right. 1080p, font ≥16pt.
No secrets on screen. Rehearse twice; record in one take per segment.

| Time | Beat | Screen |
|---|---|---|
| 0:00–0:25 | **Problem.** "New engineer inherits a repo: two weeks of archaeology. We generate the wiki — with citations that can't lie about where the code is." | README top |
| 0:25–1:00 | **Baseline.** `python -m repowiki generate <repo> --mode baseline` on the starter repo (pre-recorded run; show tail output + one page). Point at a file-level citation: "true, but coarse." | terminal + baseline page |
| 1:00–2:50 | **One full advanced run, end to end.** Same repo, `--mode advanced`. Narrate the pipeline as the trajectory scrolls: plan → per-module agents → `[[sym:...]]` cites resolving to `file:a-b` → one repair cycle firing on a bad symbol ("watch the verifier reject it — this is the product") → data-flow page with the mermaid diagram. | terminal + trajectory render + finished wiki |
| 2:50–3:40 | **The comparison.** `evals/report.md`: both repos, both modes. Walk the delta column: citation depth 0→0.78, symbol coverage →1.00, cost +2.8x. | report table |
| 3:40–4:20 | **Changelog.** Three entries: why symbol citations (baseline's plausible-but-wrong claims), scorer-honesty fix ("the table almost lied"), coverage backfill. | docs/CHANGELOG.md |
| 4:20–4:55 | **Close.** Biggest lever: removing the model's ability to invent coordinates. Experiment removed: embedding-based retrieval (killed for reproducibility — DESIGN.md). Main failure mode: metaprogrammed repos under-report call edges. | DESIGN.md |
