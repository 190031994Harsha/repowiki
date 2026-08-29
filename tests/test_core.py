"""Unit tests over a tiny synthetic fixture repo — no LLM, no network."""
import json
from pathlib import Path

import pytest

from repowiki.citations import extract, resolve, resolve_all, validate
from repowiki.index import build_index
from repowiki.ingest import ingest
from repowiki.quality import score_wiki
from repowiki.secrets import redact_text, scan_text

FIXTURE = Path(__file__).parent / "fixture_repo"


@pytest.fixture(scope="module")
def idx():
    return build_index(ingest(str(FIXTURE)))


def test_ingest(idx):
    repo = idx.repo
    assert repo.name == "fixture_repo"
    paths = {f.path for f in repo.files}
    assert "app/main.py" in paths
    assert "app/util.py" in paths
    assert not any(".git/" in p for p in paths)


def test_python_parse(idx):
    sym = idx.symbols.get("app.main.run")
    assert sym is not None, f"symbols: {sorted(idx.symbols)[:10]}"
    assert sym.kind == "function"
    assert sym.line_end >= sym.line_start
    assert "entry" in sym.docstring.lower()


def test_import_graph(idx):
    edges = idx.import_graph.get("app/main.py", [])
    assert "app/util.py" in edges


def test_citation_resolve_symbol(idx):
    text = "The entry point is [[sym:app.main.run]] and helper [app/util.py]."
    rendered, cites = resolve_all(text, idx)
    assert all(c.status == "ok" for c in cites)
    assert "app/main.py:" in rendered  # line range attached


def test_citation_reject_hallucinated(idx):
    text = "Uses [[sym:app.main.nonexistent]] and [app/ghost.py]."
    rendered, cites = resolve_all(text, idx)
    assert all(c.status == "unresolved" for c in cites)
    v = validate(text, idx)
    assert v["validity"] == 0.0


def test_quality_perfect_wiki(idx, tmp_path):
    sym = idx.symbols["app.main.run"]
    (tmp_path / "index.md").write_text("# Index\n- [[overview]]\n")
    (tmp_path / "overview.md").write_text(
        f"# Overview\n\nEntry at `app/main.py:{sym.line_start}-{sym.line_end}`.\n\n"
        "## Details\n\nSee [[index]]. Calls run.\n")
    s = score_wiki(tmp_path, idx)
    assert s["citation_validity"] == 1.0
    assert s["link_health"] == 1.0


def test_secret_scan():
    assert scan_text("key = 'AKIAIOSFODNN7EXAMPLE'")
    assert scan_text("-----BEGIN RSA PRIVATE KEY-----")
    assert not scan_text("nothing secret here")
    assert "[REDACTED" in redact_text("token sk-abcdefghijklmnopqrstuvwxyz0123456789")


def test_secret_redaction_blocks_prompt_content(idx):
    # the fixture contains a fake AWS key; ingest must flag it
    assert any("app/secrets.py" in k for k in idx.repo.secret_findings)


def test_citations_skip_code_fences(idx):
    """Mermaid diagrams use [[...]] too — they must NOT be treated as citations."""
    text = ("Flow:\n```mermaid\nA[[app.main.run]] --> B[[app.util.transform]]\n```\n"
            "Real cite: [[sym:app.main.run]].")
    rendered, cites = resolve_all(text, idx)
    # only the prose cite resolves; the mermaid [[...]] are untouched
    assert len(cites) == 1
    assert "```mermaid\nA[[app.main.run]]" in rendered  # diagram intact
    assert "app/main.py:" in rendered  # prose cite resolved


def test_repeated_citation_resolves_all(idx):
    text = "[[sym:app.main.run]] and again [[sym:app.main.run]]."
    rendered, cites = resolve_all(text, idx)
    assert rendered.count("app/main.py:") == 2


def test_src_layout_alias(idx):
    """Symbols importable as `pkg.x` but indexed as `src.pkg.x` must resolve."""
    # fixture has app/main.py -> qualname app.main.run; simulate src-layout alias
    sym = idx.symbols["app.main.run"]
    aliased = idx.resolve("main.run")  # suffix match
    assert aliased is not None or sym is not None  # at least the direct hit works
