# Judge v3: video (x-ai/grok-4.6)
_2026-08-31 13:18 UTC_

**Structurally: yes. As a video a tired judge will sit through 200 of: no.**

It hits the rubric in order and clocks ~4:55. That is the only compliment.

---

### Rubric checklist
| Required | Present? | Actually lands? |
|---|---|---|
| Problem + baseline first | Yes, 0:00–1:00 | Problem is generic onboarding copy. Baseline is a command tail + “true, but coarse.” |
| ONE realistic execution, end-to-end | Slot exists, 1:00–2:50 | This is a factory tour, not a run. |
| Final comparison | Yes, 2:50–3:40 | Spreadsheet walk. |
| Changelog | Yes, 3:40–4:20 | Recap of things already implied. |
| Biggest win + one killed experiment | Yes, 4:20–4:55 | Three ideas in 35s after the judge has checked out. |

Order is correct. **Pacing is a 110-second trough with the product moment buried in it, then two recap segments.**

---

### What a tired judge remembers
“Another repo-wiki. Citations. A table. Cost went up.”

They will **not** remember: cite-by-symbol, fail-closed drop, scorer almost lying, embeddings killed, fastapi metaprogramming. Those are five distinct claims, none given a single unmissable visual.

Commodity framing at 0:00 (“new engineer, two weeks of archaeology”) guarantees you are filed with the other 40 doc-gen videos.

---

### Strongest 15 seconds — and it is too late
**~2:05–2:20:** “watch the verifier reject it — this is the product.”

That is the only moment that is not interchangeable with every other submission. It currently sits **inside a 1:50 pipeline narration**, after plan → agents → cite resolution. If attention is already gone at 1:20 (it will be), the product never happens.

Second-best unused 15s, sitting in CHANGELOG and **not in the script:** baseline saying “FaultState enum” (it’s a class) / “combinatorial testing” (it isn’t). That is the lie. “True, but coarse” is a shrug. A wrong claim with a file-level cite that still looks green is the demo.

Put the lie or the reject in the **first 75 seconds**. Not minute two.

---

### Pacing autopsy (where attention dies)

| Time | What happens | Judge brain |
|---|---|---|
| 0:00–0:25 | README + archaeology | Heard it. Mild hold if “citations that can’t lie” is the first sentence, not the second. |
| 0:25–1:00 | Baseline command, tail, one page | Holds **only** if you show a *wrong* claim. “True but coarse” = drop starts. |
| **1:00–1:45** | **plan → per-module agents → cites scrolling** | **Dead. This is 45s of process. You lose ~40% of judges here.** |
| 1:45–2:20 | Repair (the actual product) | Spike, if they’re still watching. |
| 2:20–2:50 | Mermaid data-flow | Pretty, generic. Every docs tool has a diagram. |
| 2:50–3:40 | Walk `evals/report.md` delta column | Second death. Tables after a 2-min tour feel like appendix. |
| 3:40–4:20 | Changelog, three entries | Third death. You already showed the numbers. Reading CHANGELOG.md on camera is homework. |
| 4:20–4:55 | Win + killed experiment + failure mode | Too many, too late. One of three survives, probably none. |

**37% of the video is the advanced “run.”** That is the overrun risk and the boredom risk. Baseline is marked pre-recorded; advanced is not. A 295s generation “as the trajectory scrolls” will blow 5:00 unless it’s a scrubbed recording — **say that in the script or you will go long.**

Changelog after comparison is the same movie twice. Close then adds a third summary. Rubric wants those beats; it does not want them as three consecutive recaps.

---

### Brutal cuts
- Kill the pipeline voiceover. Nobody watching 200 videos wants plan → agents → mermaid.
- Do not “walk the delta column.” Flash **two numbers** (depth 0→0.78, coverage →1.00) and the cost (+2.8x) as a caption. Sit on them for 8s. Stop talking.
- Changelog: **one** honesty story (“the table almost lied”), not three entries. Coverage backfill is not video.
- Close: **one** win, **one** kill. Failure mode is a caption, not a third speech.

---

### Rewrite the weakest beat (1:00–2:50)

Replace the factory tour with a 55s execution that is *one incident*. Steal the leftover ~55s: 20s to move the reject earlier (or show the baseline lie at 0:40), 20s to make comparison a still, 15s so the close isn’t a fire sale.

**1:00–1:55 — One execution (rewritten)**

> **Screen:** split. Left = pre-recorded advanced trajectory, **already scrubbed to the repair event** (do not play plan/agents). Right = the page in the editor, then the source file.
>
> **1:00–1:08** (VO, no pipeline tour): “Same repo, advanced. The model is not allowed to write line numbers. It may only emit `[[sym:…]]`. Watch what happens when it lies.”
>
> **1:08–1:28** (the 15s that must exist): Trajectory: bad symbol in, verifier reject, repair cycle 1. Freeze the reject line. Cursor on it. **Silence for one beat.** “That reject *is* the product. Prompting harder does not do this.”
>
> **1:28–1:42:** Cut to finished page. One sentence, citation rendered `file:start-end`. Split to the actual file, highlight those lines. “Resolver attached the span. If it can’t, the sentence is dropped. Fail-closed. No dangling refs.”
>
> **1:42–1:55:** Data-flow page, mermaid on screen, **do not narrate the diagram**. One line: “Diagrams come along for the ride. They are not the claim.” Smash cut to report.

Do **not** say “plan → per-module agents → cites resolving → mermaid.” If a stage isn’t the reject or the highlighted span, it is not in the video.

---

### If you only change three things
1. Open on the lie or the reject, not onboarding poetry.
2. Cut 1:00–2:50 to the rewrite above; pre-record and scrub it.
3. Comparison = three numbers on screen, 20s. Changelog = scorer-honesty only. Close = “removed the model’s ability to invent coordinates” + “killed embedding retrieval for reproducibility.” Stop.

As written, a judge at video #147 will remember a wiki and a table. The thing you built that the other 199 did not — **coordinates the model cannot invent, and a verifier that throws them out** — is currently a subordinate clause at 2:10.