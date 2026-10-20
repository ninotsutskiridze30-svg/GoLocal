"""Load and chunk the reviewed Markdown event corpus."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit


MAX_CHARS = 1200
OVERLAP_CHARS = 180
SOURCE_RE = re.compile(r"^- Source: (https://\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    title: str
    section: str
    source_url: str
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def _windows(text: str, size: int = MAX_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    """Bound long sections, preferring paragraph/word boundaries."""
    if not 0 <= overlap < size:
        raise ValueError("Overlap must be smaller than chunk size")
    text = text.strip()
    windows = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n\n", start + size // 2, end),
                           text.rfind(" ", start + size // 2, end))
            if boundary > start:
                end = boundary
        windows.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return windows


def chunks_for_document(path: Path, corpus_root: Path) -> list[Chunk]:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"Missing title: {path.name}")
    title = lines[0][2:].strip()
    source = SOURCE_RE.search(raw)
    if not source:
        raise ValueError(f"Missing source URL: {path.name}")
    url = source.group(1)
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
        raise ValueError(f"Invalid source URL: {path.name}")
    doc_id = path.relative_to(corpus_root).with_suffix("").as_posix()
    sections: list[tuple[str, str]] = []
    heading = "Overview"
    body: list[str] = []
    for line in lines[1:]:
        if line.startswith("## "):
            if any(item.strip() for item in body):
                sections.append((heading, "\n".join(body).strip()))
            heading = line[3:].strip()
            body = []
        else:
            body.append(line)
    if any(item.strip() for item in body):
        sections.append((heading, "\n".join(body).strip()))
    chunks = []
    for section, content in sections:
        for part in _windows(content):
            chunks.append(Chunk(f"{doc_id}#{len(chunks) + 1}", doc_id, title,
                                section, url, f"{title} | {section}\n{part}"))
    if not chunks:
        raise ValueError(f"Empty document: {path.name}")
    return chunks


def load_corpus(corpus_root: Path) -> tuple[list[Chunk], dict[str, str]]:
    paths = sorted(corpus_root.rglob("*.md"))
    if not paths:
        raise ValueError("No Markdown corpus documents")
    chunks: list[Chunk] = []
    hashes = {}
    for path in paths:
        relative = path.relative_to(corpus_root).as_posix()
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        chunks.extend(chunks_for_document(path, corpus_root))
    return chunks, hashes
