"""Secret scanning + redaction.

Runs at ingest time, BEFORE any file content can reach an LLM prompt. Matches the
competition requirement: no secret-bearing content leaves the machine, and secrets are
redacted from any artifact we emit.
"""
from __future__ import annotations

import re

PATTERNS = [
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("aws_secret_key", re.compile(r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]")),
    ("github_token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("generic_bearer", re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-.]{20,}")),
    ("generic_password", re.compile(r"(?i)(password|passwd|api[_-]?key|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
]


def scan_text(text: str) -> list[dict]:
    """Return list of {kind, line} findings."""
    findings = []
    for kind, rx in PATTERNS:
        for m in rx.finditer(text):
            findings.append({"kind": kind, "line": text.count("\n", 0, m.start()) + 1})
    return findings


def redact_text(text: str) -> str:
    for kind, rx in PATTERNS:
        text = rx.sub(f"[REDACTED:{kind}]", text)
    return text


def scan_files(files: dict[str, str]) -> dict[str, list[dict]]:
    """files: relpath -> content. Returns {relpath: findings} for files with hits."""
    out = {}
    for path, content in files.items():
        hits = scan_text(content)
        if hits:
            out[path] = hits
    return out
