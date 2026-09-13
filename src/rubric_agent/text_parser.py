"""Submission ingestion (FR4).

Plain text and text-based PDF are supported (Constraint C4: no OCR). Page
boundaries are kept, line structure inside a page is preserved so that the
chunker can find headings and paragraphs, and every page carries the section
heading that was current when the page started.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .errors import SubmissionParseError
from .textutil import normalize

MARKDOWN_HEADING = re.compile(r"^\s*(?:#{1,3}\s+|SECTION:\s+)(.+?)\s*$")
NUMBERED_HEADING = re.compile(r"^\s*(?:Appendix\s+[A-Z]|\d{1,2}(?:\.\d{1,2}){0,2})\.?\s+([A-Z][^.!?\n]{2,80}?)\s*$")
CAPS_HEADING = re.compile(r"^\s*([A-Z][A-Z0-9 ,&/\-]{3,60})\s*$")
PAGE_MARKER = re.compile(r"(?m)^===\s*PAGE\s+\d+\s*===\s*$")


@dataclass(frozen=True)
class ParsedPage:
    page: int
    text: str
    section: str


def parse_submission(source: str | Path) -> list[ParsedPage]:
    if isinstance(source, Path) or _is_existing_path(source):
        path = Path(source)
        if not path.exists():
            raise SubmissionParseError(f"missing submission: {path}")
        if path.suffix.lower() == ".pdf":
            return _parse_pdf(path)
        return _parse_text(path.read_text(encoding="utf-8", errors="replace"))
    return _parse_text(str(source))


def heading_of(line: str) -> str | None:
    """Return the heading text if `line` looks like a section heading."""
    m = MARKDOWN_HEADING.match(line)
    if m:
        return m.group(1).strip()
    if len(line.strip()) > 90:
        return None
    m = NUMBERED_HEADING.match(line)
    if m:
        text = m.group(1).strip()
        # Reject list items that merely start with a number ("3 marks", "2 out of 5").
        if len(text.split()) >= 1 and not re.match(r"^(marks?|points?|out of|of)\b", text, re.I):
            return text
    m = CAPS_HEADING.match(line)
    if m:
        words = [w for w in re.split(r"[ ,&/\-]+", m.group(1)) if w]
        letters = sum(len(w) for w in words if w.isalpha())
        if 1 <= len(words) <= 8 and letters >= 6 and not any(re.match(r"^[A-Z]{1,4}\d+$", w) for w in words):
            return m.group(1).title()
    return None


def _is_existing_path(source: object) -> bool:
    return isinstance(source, str) and "\n" not in source and len(source) < 1024 and Path(source).exists()


def _parse_pdf(path: Path) -> list[ParsedPage]:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # noqa: BLE001 - pypdf raises many types
        raise SubmissionParseError(f"cannot open PDF: {exc}") from exc
    pages: list[ParsedPage] = []
    current_section = "body"
    for i, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        text = _clean_pdf_text(raw)
        pages.append(ParsedPage(page=i, text=text, section=current_section))
        for line in text.splitlines():
            h = heading_of(line)
            if h:
                current_section = h
    if not any(normalize(p.text) for p in pages):
        raise SubmissionParseError("PDF contained no extractable text (scanned or image-only PDFs are out of scope)")
    return pages


def _clean_pdf_text(raw: str) -> str:
    lines = [ln.rstrip() for ln in raw.replace("\r", "").split("\n")]
    out: list[str] = []
    for ln in lines:
        if re.fullmatch(r"\s*(?:Page\s+)?\d{1,3}(?:\s*/\s*\d{1,3})?\s*", ln):  # bare page numbers
            continue
        out.append(re.sub(r"[ \t]+", " ", ln))
    return "\n".join(out).strip()


def _parse_text(text: str) -> list[ParsedPage]:
    raw = text.replace("\r\n", "\n").replace("\ufeff", "")
    if not normalize(raw):
        raise SubmissionParseError("empty submission")
    blocks = raw.split("\f") if "\f" in raw else _split_page_markers(raw)
    pages: list[ParsedPage] = []
    current_section = "body"
    for i, block in enumerate(blocks, start=1):
        block = block.strip("\n")
        pages.append(ParsedPage(page=i, text=block.strip(), section=current_section))
        for line in block.splitlines():
            h = heading_of(line)
            if h:
                current_section = h
    return pages


def _split_page_markers(text: str) -> list[str]:
    parts = PAGE_MARKER.split(text)
    parts = [p for p in parts if normalize(p)]
    return parts or [text]
