# Judge v3: fairness (deepseek/deepseek-v4-pro)
_2026-08-31 13:18 UTC_

The baseline is **not a fair measuring stick**—it’s a strawman that denies the LLM the very input (code) that makes documentation possible. The single change that would make it fair is **giving the baseline the same file contents (or at least symbol-level code snippets) as the advanced system**. Below is the line-by-line audit.

---

### 1. Same model, same file contents, same symbol access?

**Model:** ✅ Both use the same `LLM` class (same model, same temperature).  
**File contents:** ❌ Baseline *never* includes file contents in prompts. Advanced uses `_excerpt()` to show actual code (up to 6000 chars, with symbol skeleton for large files).  
**Symbol access:** ❌ Baseline only sees a comma-separated list of up to 20 public symbol names (no signatures, no docstrings, no line numbers). Advanced sees the full symbol table with signatures, docstrings, and the corresponding code excerpts.  

**Verdict:** The baseline is blind to the code; the advanced sees the code. That is a fatal asymmetry.

---

### 2. Is the baseline’s system prompt written to fail?

**No.** The prompt is not deliberately sabotaged. It says:
- Cite files as `[path]` and “where you can, name the specific function or class with its approximate line number, e.g. `[path/to/file.py::function_name]`.”
- It does not forbid symbol-level citations; it encourages them.  
The advanced prompt is stricter (*must* cite symbols, never line numbers), but that’s a design choice, not a trap. The problem is not the prompt text—it’s that the baseline LLM has no code to look at, so it cannot produce meaningful symbol citations.

---

### 3. Is `_grep_upgrade` a genuine attempt?

**Partially.** It is a real, deterministic post-processing step that tries to upgrade `[path::name]` to a line range by grepping for `def name` / `class name`. It is honest-naïve—the kind of thing a competent engineer would try first.  
However, it is a token gesture in practice:
- It only works if the model emits `[path::name]` (which it rarely does without code context).
- It fails on decorators, nested definitions, and many language constructs.
- It returns a single line (`line-line`), not a true range.  
The comparison **naïve grep vs. precise index** is fair, but the baseline’s lack of code prevents the model from generating the citations that the grep could upgrade in the first place.

---

### 4. Every asymmetry judged

| Asymmetry | Baseline | Advanced | Judgment |
|-----------|----------|----------|----------|
| **Code content in prompts** | None (only file names, public symbol names) | Full file excerpts + symbol table with signatures | **Unfair.** A “reasonable basic approach” would include the code. Without it, the LLM can only guess. |
| **Symbol details** | List of qualified names (no signatures, docstrings) | Full `idx.symbols` (line numbers, signatures, docstrings) | **Unfair** – same as above; the advanced gets the actual API, the baseline gets only names. |
| **Citation format** | Optional `[path::name]` with approximate line numbers | Mandatory `[[sym:...]]` (lines attached deterministically) | **Justified by design.** The advanced enforces precision; the baseline allows ambiguity. This is a valid differentiator. |
| **Line‑range attachment** | Post-hoc grep (naïve) | Deterministic from index | **Justified.** The comparison is exactly the point: naïve vs. accurate. |
| **Pipeline complexity** | Single pass, template-driven | Plan → Generate → Verify → Repair → Link | **Justified.** The baseline is a simple one-shot; the advanced adds verification—that’s what we’re testing. |
| **Page plan** | Fixed (overview, architecture, module‑*) | LLM‑planned JSON, tailored to repo | **Justified.** The advanced’s plan is a claimed improvement; the baseline’s fixed template is a fair simple baseline. |
| **Module selection** | ≥50 lines, max 12 | ≥30 lines, unlimited | **Minor.** Not a significant fairness issue. |
| **Cross‑linking** | Simple “See also” list | Backlinks, orphan detection | **Justified.** The advanced is intentionally richer; baseline is minimal. |
| **Cost/time** | Lower | Higher | **Inherent.** Not a fairness issue. |

---

### 5. Verdict: Is the baseline a fair measuring stick?

**No.** The baseline is crippled by design: it removes the most crucial input any documentation system needs—the actual source code. The measured “improvement” in depth (0.00 → 0.70+), symbol coverage, and validity is largely because the advanced sees the code, not because of its repair pipeline, verification, or indexing. The current baseline is a strawman.

---

### 6. ONE change to make it fair

**Give the baseline the same code context as the advanced.** Specifically, for every module page, include the full file contents (or the same `_excerpt`-style skeleton) and the symbol table with signatures, just like the advanced does. Keep everything else the same—simple single-pass, template, no repair, no verification, naïve grep. Then the comparison genuinely isolates the value of verification, repair, and deterministic line‑range attachment.