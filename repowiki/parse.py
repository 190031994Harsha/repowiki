"""Parse code files into symbols, imports and call edges.

Python: real `ast` parse (accurate line ranges, docstrings, intra-module call edges).
Other languages: careful regex scanners (structure only, no call edges).
Everything degrades gracefully — an unparseable file contributes its path and nothing else.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field


@dataclass
class Symbol:
    name: str          # simple name, e.g. "create_order"
    qualname: str      # dotted, e.g. "orders.create_order" or "Engine.remediate"
    kind: str          # module | class | function | method | constant
    file: str          # repo-relative path
    line_start: int
    line_end: int
    signature: str = ""
    docstring: str = ""


@dataclass
class FileParse:
    path: str
    lang: str
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)       # module paths as written
    calls: list[tuple[str, str]] = field(default_factory=list)  # (caller_qualname, callee_name)
    error: str = ""


# ---------------------------------------------------------------- python (ast)

def parse_python(path: str, content: str) -> FileParse:
    fp = FileParse(path=path, lang="Python")
    module = path[:-3].replace("/", ".").replace(".__init__", "")
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        fp.error = f"SyntaxError: {e}"
        return fp

    fp.symbols.append(Symbol(module.split(".")[-1], module, "module", path, 1,
                             content.count("\n") + 1,
                             docstring=(ast.get_docstring(tree) or "")[:400]))

    def visit(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "method" if prefix else "function"
                qual = f"{prefix}.{child.name}" if prefix else f"{module}.{child.name}"
                try:
                    sig = ast.unparse(child.args)[:200]
                except Exception:
                    sig = ""
                fp.symbols.append(Symbol(
                    child.name, qual, kind, path, child.lineno,
                    getattr(child, "end_lineno", child.lineno) or child.lineno,
                    signature=f"({sig})",
                    docstring=(ast.get_docstring(child) or "")[:400]))
                # intra-file call edges
                for sub in ast.walk(child):
                    if isinstance(sub, ast.Call):
                        callee = None
                        if isinstance(sub.func, ast.Name):
                            callee = sub.func.id
                        elif isinstance(sub.func, ast.Attribute):
                            callee = sub.func.attr
                        if callee:
                            fp.calls.append((qual, callee))
                visit(child, qual.split(".", 1)[-1] if False else None)  # no nested fn qualnames
            elif isinstance(child, ast.ClassDef):
                qual = f"{module}.{child.name}" if not prefix else f"{prefix}.{child.name}"
                bases = []
                for b in child.bases:
                    try:
                        bases.append(ast.unparse(b))
                    except Exception:
                        pass
                fp.symbols.append(Symbol(
                    child.name, qual, "class", path, child.lineno,
                    getattr(child, "end_lineno", child.lineno) or child.lineno,
                    signature=f"({', '.join(bases)})" if bases else "",
                    docstring=(ast.get_docstring(child) or "")[:400]))
                visit(child, qual)
            elif isinstance(node, ast.Module) and isinstance(child, (ast.Import, ast.ImportFrom)):
                if isinstance(child, ast.Import):
                    fp.imports.extend(a.name for a in child.names)
                else:
                    base = child.module or ""
                    fp.imports.append(base)
                    # "from app import util" may mean app/util.py, not just app/
                    fp.imports.extend(f"{base}.{a.name}" for a in child.names)

    visit(tree, None)
    return fp


# ------------------------------------------------------- regex fallback parsers

def _scan(path: str, content: str, lang: str, import_rx, def_rx) -> FileParse:
    fp = FileParse(path=path, lang=lang)
    lines = content.split("\n")
    module = path.rsplit(".", 1)[0].replace("/", ".")
    fp.symbols.append(Symbol(path.rsplit("/", 1)[-1], module, "module", path, 1, len(lines)))
    for i, line in enumerate(lines, 1):
        for m in import_rx.finditer(line):
            fp.imports.append(m.group(1))
        for m in def_rx.finditer(line):
            kind, name = m.group(1), m.group(2)
            fp.symbols.append(Symbol(name, f"{module}.{name}", kind, path, i, i))
    return fp


def parse_jsts(path: str, content: str) -> FileParse:
    import_rx = re.compile(r"""(?:import\s+.*?\s+from\s+|require\()\s*['"]([^'"]+)['"]""")
    def_rx = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(class|function)\s+([A-Za-z_$][\w$]*)"
                        r"|^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(")
    fp = _scan(path, content, "TypeScript" if path.endswith((".ts", ".tsx")) else "JavaScript",
               import_rx, def_rx)
    # normalize: group(3) arrow fns land as kind None -> fix
    for s in fp.symbols:
        if s.kind not in ("class", "function", "module"):
            s.kind = "function"
    return fp


def parse_go(path: str, content: str) -> FileParse:
    import_rx = re.compile(r"""^\s*"([a-zA-Z0-9_./-]+)"\s*$""")
    def_rx = re.compile(r"^func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(")
    fp = _scan(path, content, "Go", import_rx, re.compile(r"$^"))
    for i, line in enumerate(content.split("\n"), 1):
        m = def_rx.match(line)
        if m:
            name = m.group(1)
            fp.symbols.append(Symbol(name, f"{path.rsplit('.',1)[0].replace('/','.')}.{name}",
                                     "function", path, i, i))
    return fp


def parse_rust(path: str, content: str) -> FileParse:
    import_rx = re.compile(r"^use\s+([\w:]+)")
    def_rx = re.compile(r"^\s*(?:pub\s+)?(fn|struct|enum|trait|impl)\s+([A-Za-z_]\w*)")
    fp = _scan(path, content, "Rust", import_rx, def_rx)
    kind_map = {"fn": "function", "struct": "class", "enum": "class", "trait": "class",
                "impl": "class"}
    for s in fp.symbols:
        if s.kind in kind_map:
            s.kind = kind_map[s.kind]
    return fp


def parse_java(path: str, content: str) -> FileParse:
    import_rx = re.compile(r"^import\s+([\w.]+)")
    def_rx = re.compile(r"^\s*(?:public|private|protected|static|final|abstract|\s)*"
                        r"(class|interface|enum)\s+([A-Za-z_]\w*)")
    fp = _scan(path, content, "Java", import_rx, def_rx)
    meth_rx = re.compile(r"^\s+(?:public|private|protected|static|final|\s)+[\w<>\[\]]+\s+"
                         r"([a-zA-Z_]\w*)\s*\([^)]*\)\s*(?:throws[\w, ]+)?\{")
    for i, line in enumerate(content.split("\n"), 1):
        m = meth_rx.match(line)
        if m and m.group(1) not in ("if", "for", "while", "switch", "catch", "return", "new"):
            name = m.group(1)
            fp.symbols.append(Symbol(name, f"{path.rsplit('.',1)[0].replace('/','.')}.{name}",
                                     "method", path, i, i))
    return fp


PARSERS = {
    "Python": parse_python,
    "JavaScript": parse_jsts,
    "TypeScript": parse_jsts,
    "Go": parse_go,
    "Rust": parse_rust,
    "Java": parse_java,
}


def parse_file(path: str, lang: str, content: str) -> FileParse:
    parser = PARSERS.get(lang)
    if not parser or not content:
        fp = FileParse(path=path, lang=lang)
        fp.symbols.append(Symbol(path.rsplit("/", 1)[-1],
                                 path.rsplit(".", 1)[0].replace("/", "."),
                                 "module", path, 1, content.count("\n") + 1))
        return fp
    try:
        return parser(path, content)
    except Exception as e:
        fp = FileParse(path=path, lang=lang, error=repr(e))
        return fp
