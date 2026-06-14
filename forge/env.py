"""Minimal .env loader (avoids a python-dotenv dependency).

Reads ``KEY=value`` lines into ``os.environ`` with ``setdefault`` semantics, so an
already-exported variable always wins. Lines that are blank, comments, or lack ``=``
are ignored. Used so ``CMC_API_KEY`` in a local ``.env`` lights up the CMC provider.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: Path | str = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8-sig").splitlines():  # utf-8-sig drops any BOM
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if " #" in value:  # strip inline comment
            value = value[: value.index(" #")].rstrip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]  # strip surrounding quotes
        if key:
            os.environ.setdefault(key, value)
