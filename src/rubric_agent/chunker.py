from __future__ import annotations

import re

from .schemas import EvidenceUnit
from .text_parser import ParsedPage
from .textutil import normalize

WORD = re.compile(r"\S+")


def chunk_pages(pages: list[ParsedPage], *, target_words: int = 180) -> list[EvidenceUnit]:
    units: list[EvidenceUnit] = []
    serial = 1
    for page in pages:
        paragraphs = [normalize(p) for p in re.split(r"\n\s*\n", page.text) if normalize(p)]
        if not paragraphs:
            continue
        groups = _group(paragraphs, target_words)
        for para_index, group in enumerate(groups):
            before = groups[para_index - 1] if para_index else ""
            after = groups[para_index + 1] if para_index + 1 < len(groups) else ""
            units.append(
                EvidenceUnit(
                    id=f"E-{serial:03d}",
                    text=group,
                    page=page.page,
                    section=page.section,
                    paragraph=para_index,
                    adjacent_before=before,
                    adjacent_after=after,
                )
            )
            serial += 1
    return units


def _group(paragraphs: list[str], target_words: int) -> list[str]:
    groups: list[str] = []
    buf: list[str] = []
    count = 0
    for para in paragraphs:
        words = len(WORD.findall(para))
        if buf and count + words > target_words:
            groups.append("\n\n".join(buf))
            buf = [para]
            count = words
        else:
            buf.append(para)
            count += words
    if buf:
        groups.append("\n\n".join(buf))
    return groups
