"""Ingest a repository: clone (or use a local dir), inventory files, detect languages,
secret-scan, and read contents.

The analyzed repo is NEVER mutated: clones land in a temp/cache dir, local dirs are
only read.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .secrets import scan_files

# files we never read into context
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".tar",
              ".whl", ".so", ".dll", ".exe", ".pyc", ".class", ".jar", ".woff", ".woff2",
              ".mp4", ".mp3", ".db", ".sqlite"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
             ".next", ".tox", ".mypy_cache", ".pytest_cache", "target", "vendor"}
LANG_BY_EXT = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".java": "Java", ".go": "Go", ".rs": "Rust",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".c": "C", ".h": "C/C++ header",
    ".hpp": "C++ header", ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".kt": "Kotlin",
    ".swift": "Swift", ".md": "Markdown", ".yaml": "YAML", ".yml": "YAML",
    ".json": "JSON", ".toml": "TOML", ".sql": "SQL", ".sh": "Shell",
}
CODE_LANGS = {"Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "C",
              "Ruby", "PHP", "C#", "Kotlin", "Swift"}
MAX_FILE_BYTES = 200_000       # skip very large files from content (still counted)
MAX_TOTAL_BYTES = 4_000_000    # cap total content ingested


@dataclass
class RepoFile:
    path: str          # repo-relative, forward slashes
    lang: str
    size: int
    lines: int
    content: str = ""  # empty for binary/skipped/oversized


@dataclass
class Repo:
    source: str                    # original URL or path
    root: Path                     # local working copy
    name: str
    files: list[RepoFile] = field(default_factory=list)
    secret_findings: dict = field(default_factory=dict)
    is_git: bool = False
    head_sha: str = ""

    @property
    def languages(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.files:
            if f.lang in CODE_LANGS:
                counts[f.lang] = counts.get(f.lang, 0) + f.lines
        return dict(sorted(counts.items(), key=lambda kv: -kv[1]))

    @property
    def code_files(self) -> list[RepoFile]:
        return [f for f in self.files if f.lang in CODE_LANGS and f.content]

    def file_map(self) -> dict[str, str]:
        return {f.path: f.content for f in self.files if f.content}


def ingest(source: str, cache_dir: Path | None = None) -> Repo:
    """Clone if URL, else use local path read-only. Inventory + secret scan."""
    cache_dir = cache_dir or Path(tempfile.gettempdir()) / "repowiki-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    if re.match(r"^(https?://|git@)", source):
        name = re.sub(r"\.git$", "", source.rstrip("/")).split("/")[-1]
        dest = cache_dir / name
        if dest.exists():
            # Windows: git pack files are read-only -> rmtree needs a writable-fix handler
            def _fix_readonly(func, p, _exc):
                os.chmod(p, 0o666)
                func(p)
            shutil.rmtree(dest, onexc=_fix_readonly)
        subprocess.run(["git", "clone", "--depth", "1", source, str(dest)],
                       check=True, capture_output=True, text=True)
        root = dest
    else:
        root = Path(source).resolve()
        if not root.is_dir():
            raise ValueError(f"not a directory or git URL: {source}")
        name = root.name

    repo = Repo(source=source, root=root, name=name)
    git_dir = root / ".git"
    repo.is_git = git_dir.exists()
    if repo.is_git:
        try:
            repo.head_sha = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            pass

    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            full = Path(dirpath) / fn
            rel = full.relative_to(root).as_posix()
            ext = full.suffix.lower()
            try:
                size = full.stat().st_size
            except OSError:
                continue
            lang = LANG_BY_EXT.get(ext, "Other")
            content = ""
            lines = 0
            if ext not in BINARY_EXT and size <= MAX_FILE_BYTES and total < MAX_TOTAL_BYTES:
                try:
                    content = full.read_text(encoding="utf-8", errors="replace")
                    lines = content.count("\n") + (1 if content else 0)
                    total += size
                except OSError:
                    content = ""
            repo.files.append(RepoFile(path=rel, lang=lang, size=size, lines=lines,
                                       content=content))
    repo.files.sort(key=lambda f: f.path)

    repo.secret_findings = scan_files(repo.file_map())
    return repo
