from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from zipfile import ZipFile

from lxml import etree, html

_WHITESPACE_RE = re.compile(r"[ \t\r\n\u00a0]+")


def normalize_ws(text: str) -> str:
    """Collapse whitespace while preserving human-readable punctuation."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def html_to_text(path: Path) -> str:
    """Extract text from a Word-exported HTML file."""
    raw = path.read_bytes()
    try:
        doc = html.fromstring(raw)
        text = doc.text_content()
    except Exception:
        text = raw.decode("utf-8", errors="replace")
    return normalize_ws(unescape(text))


def odt_to_text(path: Path) -> str:
    """Extract visible-ish text from content.xml in an ODT package."""
    with ZipFile(path) as zf:
        xml = zf.read("content.xml")
    root = etree.fromstring(xml)
    pieces = [t for t in root.itertext() if t and t.strip()]
    return normalize_ws(" ".join(pieces))


def find_first(pattern: str, text: str, default: str | None = None, flags: int = re.I | re.S) -> str | None:
    m = re.search(pattern, text, flags)
    if not m:
        return default
    if m.lastindex:
        return normalize_ws(m.group(1))
    return normalize_ws(m.group(0))


def contains_any(text: str, phrases: list[str]) -> bool:
    lower = text.lower()
    return any(p.lower() in lower for p in phrases)
