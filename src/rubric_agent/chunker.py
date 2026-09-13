"""Evidence units (FR5).

Each unit is a run of paragraphs from one page and one section, roughly
`target_words` long, with an ID `E-00N`, a page/section/paragraph locator and
the neighbouring text for in-context display (FR7). Headings start a new
unit; over-long paragraphs (typical of PDF extraction, where blank lines are
lost) are split on sentence boundaries.
"""

from __future__ import annotations

import re

from .schemas import EvidenceUnit
from .text_parser import ParsedPage, heading_of
from .textutil import normalize, sentences

WORD = re.compile(r"\S+")


def chunk_pages(pages: list[ParsedPage], *, target_words: int = 160, max_words: int = 240) -> list[EvidenceUnit]:
    units: list[EvidenceUnit] = []
    serial = 1
    for page in pages:
        blocks = _blocks(page.text, page.section)
        # group consecutive blocks of the same section
        for section, paragraphs in _by_section(blocks):
            groups = _group(paragraphs, target_words, max_words)
            for para_index, group in enumerate(groups):
                before = groups[para_index - 1] if para_index else ""
                after = groups[para_index + 1] if para_index + 1 < len(groups) else ""
                units.append(
                    EvidenceUnit(
                        id=f"E-{serial:03d}",
                        text=group,
                        page=page.page,
                        section=section,
                        paragraph=para_index,
                        adjacent_before=before,
                        adjacent_after=after,
                    )
                )
                serial += 1
    return units


def _blocks(text: str, initial_section: str) -> list[tuple[str, str]]:
    """Split page text into (section, paragraph) pairs, using headings and blank lines."""
    out: list[tuple[str, str]] = []
    section = initial_section
    buf: list[str] = []
    heading_only = False

    def flush() -> None:
        nonlocal heading_only
        para = normalize(" ".join(buf))
        if para:
            out.append((section, para))
        buf.clear()
        heading_only = False

    for line in text.splitlines():
        h = heading_of(line)
        if h:
            if not heading_only:
                flush()  # a heading directly after another heading stays in the same unit
            section = h
            buf.append(line.strip().lstrip("#").strip())  # keep heading text inside the unit for retrieval
            heading_only = True
            continue
        if not line.strip():
            if not heading_only:
                flush()
            continue
        buf.append(line.strip())
        heading_only = False
    flush()
    return out


def _by_section(blocks: list[tuple[str, str]]) -> list[tuple[str, list[str]]]:
    grouped: list[tuple[str, list[str]]] = []
    for section, para in blocks:
        if grouped and grouped[-1][0] == section:
            grouped[-1][1].append(para)
        else:
            grouped.append((section, [para]))
    return grouped


def _group(paragraphs: list[str], target_words: int, max_words: int) -> list[str]:
    pieces: list[str] = []
    for para in paragraphs:
        if len(WORD.findall(para)) > max_words:
            pieces.extend(_split_long(para, target_words))
        else:
            pieces.append(para)
    groups: list[str] = []
    buf: list[str] = []
    count = 0
    for piece in pieces:
        words = len(WORD.findall(piece))
        if buf and count + words > target_words:
            groups.append("\n\n".join(buf))
            buf = [piece]
            count = words
        else:
            buf.append(piece)
            count += words
    if buf:
        groups.append("\n\n".join(buf))
    # A trailing fragment (e.g. a lone heading or caption) joins the previous unit.
    if len(groups) >= 2 and len(WORD.findall(groups[-1])) < 12:
        groups[-2] = groups[-2] + "\n\n" + groups[-1]
        groups.pop()
    return groups


def _split_long(para: str, target_words: int) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    count = 0
    for sent in sentences(para):
        words = len(WORD.findall(sent))
        if words > target_words:  # no sentence boundaries (tables, lists): hard split on words
            if buf:
                out.append(" ".join(buf))
                buf, count = [], 0
            toks = WORD.findall(sent)
            out.extend(" ".join(toks[i:i + target_words]) for i in range(0, len(toks), target_words))
            continue
        if buf and count + words > target_words:
            out.append(" ".join(buf))
            buf, count = [], 0
        buf.append(sent)
        count += words
    if buf:
        out.append(" ".join(buf))
    return out
