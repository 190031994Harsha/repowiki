# Judge v2: integrity (openai/gpt-5.6-sol)
_2026-08-31 12:15 UTC_

## Concrete PoC 1: ambiguous symbol within the cited file

Create this indexed file:

```python
# ops.py
class A:
    def run(self):
        return "A"

class B:
    def run(self):
        return "B"
```

The relevant index state is:

```python
idx.symbols = {
    "ops.A.run": Symbol(
        name="run", qualname="ops.A.run", file="ops.py",
        kind="function", line_start=2, line_end=3,
    ),
    "ops.B.run": Symbol(
        name="run", qualname="ops.B.run", file="ops.py",
        kind="function", line_start=6, line_end=7,
    ),
}
idx.by_name = {
    "run": ["ops.A.run", "ops.B.run"],
}
```

The exact `Symbol` constructor may contain additional fields, but those shown are the fields used by the resolver.

Generated input:

```markdown
`B.run` returns the string `"B"`. [ops.py::run]
```

### Exact code path

1. `resolve_all()` applies `PATH_SYMBOL_RX`:

   ```python
   r"\[([A-Za-z0-9_\-./]+\.\w+)::([A-Za-z0-9_.]+)\]"
   ```

   It extracts:

   ```python
   Citation(
       raw="[ops.py::run]",
       ref="ops.py::run",
       kind="path_symbol",
   )
   ```

2. `resolve()` splits the reference:

   ```python
   path, name = c.ref.split("::", 1)
   # path == "ops.py"
   # name == "run"
   ```

3. It iterates all simple-name matches:

   ```python
   for qual in idx.by_name.get(name, []):
       if idx.symbols[qual].file == path:
           sym = idx.symbols[qual]
           break
   ```

4. The first candidate is `ops.A.run`. It is in `ops.py`, so the loop immediately stops. It never checks that there is another `run` in the same file and never requires uniqueness.

5. Resolution succeeds:

   ```python
   c.status = "ok"
   c.file = "ops.py"
   c.line_start = 2
   c.line_end = 3
   ```

6. `resolve_all()` emits:

   ```markdown
   `B.run` returns the string `"B"`. `ops.py:2-3`
   ```

That range is valid but wrong: lines 2–3 are `A.run`, while the sentence specifically claims something about `B.run`, which is at lines 6–7.

### Why post-hoc validation also accepts it

`validate()` no longer knows the original symbol reference. It sees:

```markdown
`ops.py:2-3`
```

The rendered-range validator only checks:

```python
n = idx.file_lines("ops.py")  # 7
a < 1                         # false
b > n + 5                     # 3 > 12, false
a > b                         # false
```

It therefore increments `n_ok`, producing:

```python
{
    "total": 1,
    "ok": 1,
    "validity": 1.0,
    "problems": [],
}
```

It does not verify that `2-3` is the range for `B.run`, or even that the range corresponds to any symbol.

---

## Concrete PoC 2: src/lib alias ambiguity silently chooses `src`

This demonstrates the remaining alias-binding issue.

Repository:

```python
# src/foo.py
class Bar:
    origin = "src"
```

```python
# lib/foo.py
class Bar:
    origin = "lib"
```

Relevant index state:

```python
idx.symbols = {
    "src.foo.Bar": Symbol(
        name="Bar", qualname="src.foo.Bar",
        file="src/foo.py", kind="class",
        line_start=1, line_end=2,
    ),
    "lib.foo.Bar": Symbol(
        name="Bar", qualname="lib.foo.Bar",
        file="lib/foo.py", kind="class",
        line_start=1, line_end=2,
    ),
}
idx.by_name = {
    "Bar": ["src.foo.Bar", "lib.foo.Bar"],
}
```

Generated input:

```markdown
The library implementation of `foo.Bar` identifies itself as `"lib"`. [[sym:foo.Bar]]
```

### Exact code path

`RepoIndex.resolve("foo.Bar")` executes:

```python
if ref in self.symbols:
```

False: there is no exact `foo.Bar`.

```python
if ref in self.by_name and len(self.by_name[ref]) == 1:
```

False: `by_name` is keyed by the simple name `"Bar"`, not `"foo.Bar"`.

Then:

```python
for prefix in ("src.", "lib.", "app."):
    if not ref.startswith(prefix) and (prefix + ref) in self.symbols:
        return self.symbols[prefix + ref]
```

The first iteration finds:

```python
"src." + "foo.Bar" == "src.foo.Bar"
```

and returns it immediately. The resolver never checks whether `lib.foo.Bar` also exists.

The citation consequently gets:

```python
status = "ok"
file = "src/foo.py"
line_start = 1
line_end = 2
```

Rendered output:

```markdown
The library implementation of `foo.Bar` identifies itself as `"lib"`. `src/foo.py:1-2`
```

Again, the coordinates are valid, but they point at the wrong implementation. This is deterministic: prefix order hard-codes `src` ahead of `lib`.

The later suffix matcher does not repair this because execution has already returned.

---

## Residual degrade-to-file input

The missing-symbol fallback was removed for `path_symbol`, so this now correctly fails:

```markdown
[ops.py::does_not_exist]
```

Its path is:

```python
idx.by_name.get("does_not_exist", [])  # []
sym = None
c.status = "unresolved"
```

However, `symbol` resolution still explicitly accepts a path and converts it to the file’s module symbol:

```markdown
`B.run` performs the operation. [[sym:ops.py]]
```

Assuming the index contains a module symbol for `ops.py`, `RepoIndex.resolve("ops.py")` eventually reaches:

```python
path = ref.split(":")[0]  # "ops.py"
for qual, sym in self.symbols.items():
    if sym.file == path and sym.kind == "module":
        return sym
```

That returns the module span, typically `ops.py:1-7`, with `status="ok"`. Thus symbol syntax can still silently become a whole-file/module range. It is not the removed `[path::missing]` fallback, but it is a remaining degrade-to-file path.

---

## Independent validator inflation

Even without passing through symbolic resolution, this emitted page:

```markdown
`B.run` returns `"B"`. `ops.py:1-1`
```

receives citation validity `1.0` from `validate()` as long as `ops.py` exists and has at least one line. The validator treats any syntactically valid in-bounds rendered range as a valid citation. It does not require that the range was produced by the resolver or matches an indexed symbol.

The provided evidence does not include `score_wiki`, so its exact call path cannot be proven here. The inflation is proven at the `validate()` result consumed by any scorer using that result.

## Does the post-fix system close these?

No.

- **Fail-closed generation** only helps citations whose status is `unresolved`. Both ambiguity PoCs return `status="ok"`, so no repair or sentence dropping is triggered.
- **The path-symbol “teeth” fix** closes only the missing-symbol-to-whole-file behavior for `[path::symbol]`.
- It does **not** reject multiple same-name symbols in one file.
- `RepoIndex.resolve()` still chooses the first matching layout prefix rather than rejecting `src`/`lib` ambiguity.
- Symbol resolution still has the explicit path-to-module fallback.
- Post-hoc validation still checks coordinate bounds rather than provenance or symbol identity.

Required fixes include:

1. For `[path::name]`, collect all candidates in that file and resolve only when exactly one exists.
2. For layout aliases, collect all `src.`, `lib.`, and `app.` candidates and resolve only when exactly one exists.
3. Remove or separate the path-to-module fallback from `[[sym:...]]`.
4. Preserve resolved citation metadata, or re-resolve against an exact symbol identity during validation; do not accept arbitrary rendered ranges merely because they are in bounds.

INTEGRITY VERDICT — does any path still emit a wrong-but-valid citation? yes — `[ops.py::run]` silently binds the first of multiple same-file `run` symbols and emits its valid range with `status=ok`.