# Judge v2: correctness (deepseek/deepseek-v4-pro)
_2026-08-31 12:15 UTC_

**1. [HIGH] `parse.py` – nested functions are flattened to module-level symbols**  
**Line:** `visit(child, qual.split(".", 1)[-1] if False else None)`  
**Why it’s wrong:** The condition `if False` is *always* false, so the `prefix` passed to the recursive `visit` is always `None`. Every nested function (a `def` inside another `def`, regardless of depth) is registered as a top-level function of the module, with qualname `module.<name>`. This loses the true nesting structure, creates duplicate qualnames for same-named inner functions, and misattributes all call edges found inside them.  
**Input to trigger:**  
```python
# file: example.py
def outer():
    def inner():
        pass
```  
`parse_python("example.py", ...)` will produce a `Symbol` with `qualname="example.inner"` (should be `example.outer.inner` or at least nested) and `kind="function"`, as if `inner` were defined at module scope.

---

**2. [MEDIUM] `index.py` – `resolve()` returns the first prefix-matched symbol, not the intended one**  
**Lines:**  
```python
for prefix in ("src.", "lib.", "app."):
    if not ref.startswith(prefix) and (prefix + ref) in self.symbols:
        return self.symbols[prefix + ref]
```  
**Why it’s wrong:** The loop tries prefixes in a fixed order and returns the *first* match. If a repo happens to have two distinct symbols with the same dotted path under different top‑level directories (e.g., `src.utils.helpers` and `lib.utils.helpers`), a citation of `"utils.helpers"` will always resolve to `src.utils.helpers`, even if the writer intended `lib.utils.helpers`. The function silently picks an arbitrary symbol.  
**Input to trigger:**  
A repo containing:  
- `src/utils/helpers.py` with a function `def do(): pass`  
- `lib/utils/helpers.py` with a different function `def undo(): pass`  
Both are indexed, giving `"src.utils.helpers.do"` and `"lib.utils.helpers.undo"`. A citation `"utils.helpers"` (not in `self.symbols` as a bare qualname) will hit the prefix loop and always return the `src.` variant, even if the user meant the `lib.` one.

---

**3. [LOW] `quality.py` – readability score bottoms out at 0.00 for text with no sentence‑ending punctuation**  
**Lines:**  
```python
sentences = len(re.findall(r"[.!?](?:\s|$)", prose))
avg_sent = words / max(1, sentences)
readability = 1.0 - min(abs(avg_sent - 18) / 30, 1.0)
```  
**Why it’s wrong:** The sentence‑splitter looks only for `.`, `!`, `?` followed by whitespace. A page that consists of a single long paragraph without any of those characters yields `sentences = 0`, so `avg_sent = words / 1 = words`. If `words ≥ 30`, the readability becomes `1.0 - min(words/30, 1.0) = 0.00`. The metric reports a perfectly readable text as completely unreadable, with full confidence.  
**Input to trigger:**  
A wiki page (`some-page.md`) containing:  
```
This is a test of the emergency broadcast system this is only a test repeat this is a test of the emergency broadcast system
```  
(no periods, exclamation marks, or question marks, and at least 30 words). The scorer will output `readability: 0.0` while the actual prose is simple and fluent.