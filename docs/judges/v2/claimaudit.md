# Judge v2: claimaudit (moonshotai/kimi-k3)
_2026-08-31 12:18 UTC_

# Claim-by-Claim Audit

**1. "The engineer who just inherited a codebase."**
**Verdict: Not a falsifiable claim (audience framing).** It's consistent with the source — `ADV_SYSTEM` instructs the model to document "for new team members" — but it asserts nothing about system behavior. Benign.

**2. "The honesty notes a marketing page would omit:"**
**Verdict: Technically true but misleading.** The notes do exist and do concede real weaknesses. But per synthesis F3, the README *table* omits all three regression metrics (validity 0.96→0.78, module coverage on 4 repos, readability 0.87→0.00 / 0.66→0.00), and module coverage appears nowhere in the honesty notes either. The meta-claim performs completeness while omitting the numbers — opus5's "the honesty framing is louder than the honesty" is exactly about this sentence.

**3. "The +0.75 depth delta is partly definitional."**
**Verdict: Technically true but misleading (understatement).** Strictly, "partly" is a weak claim and satisfied. But per `citations.py`'s own docstring, baseline syntax is file-level `[path]` and *cannot express a line range*; only advanced `[[sym:...]]` resolves to `(file, start, end)`. The 0.00 baseline end of the delta is therefore definitional by construction — the baseline was prohibited from producing the measured artifact (F1, flagged by all 8 judges). "Partly" implies a meaningful earned component that the evidence does not support.

**4. "Validity does not reach 1.00."**
**Verdict: Literally true.** `resolve()` sets `status = "unresolved"` for missing paths/symbols, and `Citation.render()` has an explicit branch emitting `` `{self.raw}` *(unresolved citation)* `` — unresolved citations reach the shipped page. Consistent with the reported 0.78/0.96 figures. This honesty note is accurate — and, importantly, it contradicts claim 8.

**5. "Readability regresses."**
**Verdict: Literally true as measured.** The synthesis reports the collapses (httpx 0.87→0.00, packaging 0.66→0.00). Caveat: fix #2 notes the 0.00 is likely a broken instrument (sentence splitter choking on cite-dense prose), so the *magnitude* may be an artifact — but the sentence is an admission against interest, so it cannot mislead in the submission's favor.

**6. "Python is the deep-parse language."**
**Verdict: Literally true per the bundle.** Nothing in the provided source contradicts it, and synthesis fix #6 ("add Go + TS eval repos") confirms deep parsing/eval was Python-only. Two flags: `index.py` is not in the bundle, so it's the least independently verifiable of the true claims; and the phrasing is an absolute ("*the* deep-parse language") — a single non-Python symbol-parse anywhere would falsify it.

**7. "The LLM can still write true-but-unguided prose."**
**Verdict: Literally true.** The VERIFY stage only resolves citations through the index; nothing binds prose to the cited spans. If anything, the sentence *understates* the real failure (F2: false-but-cited claims also score full marks) — but as written, it's accurate.

**8. "The wiki cannot contain a citation the tree doesn't support."**
**Verdict: FALSE.** This absolute is falsified by the shipping code itself. `Citation.render()` contains a dedicated branch for `status != "ok"` that emits the raw citation text annotated `*(unresolved citation)*` — that string can only exist because unresolved citations ship. Per F5, `_gen_with_repair` gives up after bounded retries and renders the page anyway: the system fails *open*. An unresolved citation is precisely "a citation the tree doesn't support," and the wiki contains it. The claim also fails under the stronger reading of "support": even *resolved* citations are only checked for existence, never for whether the span supports the sentence (F2). Notably, the same false absolute is repeated in `citations.py`'s docstring ("so the emitted wiki cannot contain a hallucinated path or range") — this is a believed system property, not a one-off marketing slip.

**9. "The LLM can still write true-but-unguided prose — citations guarantee that claims…"** *(truncated in bundle)*
**Verdict: False under any natural completion; technically-true-but-misleading only under a trivialized one.** The load-bearing word is "guarantee" applied to *claims*. No mechanism in the provided source enforces any guarantee about claims: claim–span support is never checked (F2); "No citation, no claim" is a prompt instruction with no code enforcement; and because of the fail-open path, not even "every claim carries a *valid* citation" is guaranteed (F5). The sentence's own first clause concedes the gap that its second clause then claims to close — the two halves can only be reconciled by watering "guarantee" down to "anchors usually resolve," which is not a claim about claims and is still not a guarantee.

**Scorecard:** 4 literally true (4, 5, 6, 7) · 2 technically-true-but-misleading (2, 3) · 2 false (8, 9) · 1 non-falsifiable framing (1).

---

# The Disqualifying Sentence

> **"The wiki cannot contain a citation the tree doesn't support."**

A hostile judge quotes this one, for five compounding reasons:

1. **Absolutes are the cheapest claims to kill.** "Cannot" requires one counterexample, and the counterexample is one function long: `Citation.render()`'s unresolved branch (`"`{self.raw}` *(unresolved citation)*"`). The judge doesn't need to run anything — the mere existence of that rendering path proves the authors anticipated and shipped the exact artifact the README says cannot exist. The code is the confession.

2. **The failure is designed, not accidental.** F5 documents that repair is bounded (3 attempts) and the page ships anyway. This isn't an edge-case leak; it's the specified behavior. The system fails open precisely where the README claims it fails closed.

3. **The README self-refutes.** The same README's honesty note — "Validity does not reach 1.00" — is a direct admission that unsupported citations ship. The judge needs no external evidence; the submission contradicts itself in adjacent paragraphs.

4. **It's load-bearing for the biggest scoring bucket.** `citations.py`'s docstring declares the citation log "the audit trail for the 30-point grounding criterion." A provably false absolute sitting on the 30-point mechanism — in a submission whose entire brand is measurement honesty — reads as disqualifying rather than sloppy. It converts the project's central asset into the exhibit against it.

5. **No hedge, no defense.** The "guarantee" sentence (9) is the runner-up, but it's prefaced by its own admission ("can still write true-but-unguided prose"), giving the defense a "we disclosed that" out, and refuting it requires the conceptual F2 argument (coordinates vs. claims). Sentence 8 has no hedge, no ambiguity, and a refutation that fits in one `render()` branch — and it appears *twice* (README + `citations.py` docstring), so the judge can frame it as the team misunderstanding its own system's failure mode.

The caption is already written in the synthesis: *"the honesty framing is louder than the honesty."*