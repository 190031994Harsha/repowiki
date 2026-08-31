# Judge v3: exec (openai/gpt-5.6-sol)
_2026-08-31 13:17 UTC_

**PoC A — FIXED**

Proof:

> `rendered: B.run returns 2. \`[ops.py::run]\` *(unresolved citation)*`  
> `statuses: [('ops.py::run', 'unresolved')]`

Both `ops.A.run` and `ops.B.run` match `run` in `ops.py`, so the resolver correctly fails closed instead of selecting one arbitrarily.

**PoC B — FIXED**

Proof:

> `rendered: uses \`[[sym:foo.Bar]]\` *(unresolved citation)*`

Both `src.foo.Bar` and `lib.foo.Bar` are alias candidates for `foo.Bar`; the resolver correctly rejects the ambiguity.

Thus, the two tested v2 ambiguity holes are closed. “Unresolved” is the intended safe result here, not evidence that the ambiguity exploit succeeded.

### New adversarial input: Unicode symbol name

Create:

```python
# unicode_names.py
def café():
    return 1
```

Generate this citation:

```markdown
Calls [[sym:unicode_names.café]].
```

Likely failure: `SYMBOL_CITE_RX` only permits `[A-Za-z0-9_.]+`, so it will not recognize the citation at all. `resolve_all()` may leave it untouched, while `validate()` extracts zero citations and can return:

```python
{"total": 0, "ok": 0, "validity": 1.0, "problems": []}
```

That would bypass fail-closed validation: an unresolved citation-like token remains in emitted text but is reported as fully valid.