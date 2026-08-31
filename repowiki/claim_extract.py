"""Extract (claim, cited-span) pairs from a generated page body.

Shared by the in-generator verifier agent (advanced.py) and the offline scorer
(evals/claim_support.py). A claim is the sentence carrying a rendered citation;
the span is the (file, a, b) the resolver attached.
"""
from __future__ import annotations

import re

# rendered symbol cite: `Name` (`path:a-b`)  OR legacy bare `path:a-b`
CITE_RX = re.compile(r"(?:`([A-Za-z_][\w.]*)`\s*)?\(`?([A-Za-z0-9_\-./]+\.\w+):(\d+)-(\d+)`?\)"
                     r"|`([A-Za-z0-9_\-./]+\.\w+):(\d+)-(\d+)`")


def claims_from_body(body: str) -> list[dict]:
    out = []
    body_nc = re.sub(r"```.*?```", " ", body, flags=re.S)
    for m in CITE_RX.finditer(body_nc):
        if m.group(2):  # new format: `Name` (`path:a-b`)
            path, a, b = m.group(2), int(m.group(3)), int(m.group(4))
        else:           # legacy: `path:a-b`
            path, a, b = m.group(5), int(m.group(6)), int(m.group(7))
        # the sentence ending at this citation
        start = max(body_nc.rfind(".", 0, m.start()), body_nc.rfind("\n", 0, m.start())) + 1
        end = body_nc.find(".", m.end())
        end = end if end != -1 else min(len(body_nc), m.end() + 120)
        full = body_nc[start:end + 1].strip()
        claim = re.sub(r"^[-*#\d.\s]+", "", full).strip()
        if len(claim) >= 20:
            out.append({"claim": claim, "full": full, "file": path, "a": a, "b": b})
    return out
