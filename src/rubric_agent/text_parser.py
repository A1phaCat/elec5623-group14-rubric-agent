from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .errors import SubmissionParseError
from .textutil import normalize


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
        return _parse_text(path.read_text(encoding="utf-8"))
    return _parse_text(str(source))


def _is_existing_path(source: object) -> bool:
    return isinstance(source, str) and "\n" not in source and Path(source).exists()


def _parse_pdf(path: Path) -> list[ParsedPage]:
    reader = PdfReader(str(path))
    pages: list[ParsedPage] = []
    current_section = "body"
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        heading = _first_heading(text)
        if heading:
            current_section = heading
        pages.append(ParsedPage(page=i, text=normalize(text), section=current_section))
    if not any(p.text for p in pages):
        raise SubmissionParseError("PDF contained no extractable text")
    return pages


def _parse_text(text: str) -> list[ParsedPage]:
    raw = text.replace("\r\n", "\n").replace("\ufeff", "")
    if not normalize(raw):
        raise SubmissionParseError("empty submission")
    blocks = raw.split("\f") if "\f" in raw else _split_page_markers(raw)
    pages: list[ParsedPage] = []
    current_section = "body"
    for i, block in enumerate(blocks, start=1):
        heading = _first_heading(block)
        if heading:
            current_section = heading
        pages.append(ParsedPage(page=i, text=block.strip(), section=current_section))
    return pages


def _split_page_markers(text: str) -> list[str]:
    import re

    parts = re.split(r"(?m)^===\s*PAGE\s+\d+\s*===\s*$", text)
    parts = [p for p in parts if normalize(p)]
    return parts or [text]


def _first_heading(text: str) -> str | None:
    import re

    match = re.search(r"(?m)^(?:#{1,3}\s+|SECTION:\s+)(.+)$", text)
    return match.group(1).strip() if match else None
