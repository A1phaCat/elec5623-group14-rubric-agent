"""Rubric ingestion (FR1–FR3).

Three text layouts are recognised without any prompt writing:

1. *Block* — `CRITERION:` / `## Name` headers with `ID:`, `MAX:`, `GRANULARITY:`
   fields and `<score>: <descriptor>` lines.
2. *Table* — a Markdown table whose header contains `Max` and numeric level
   columns (`| ID | Criterion | Max | 0 | 0.5 | 1.0 |`). Descriptor text may
   span several cells; every numeric header becomes one level.
3. *Numbered list* — the layout most course rubrics are pasted in:
   `1. Problem definition (4 marks)` followed by `- 0: ...` / `* 2 – ...` lines.

PDF rubrics are read with pypdf and then treated as text.
"""

from __future__ import annotations

import re
from pathlib import Path

from .errors import RubricParseError
from .schemas import Criterion, Rubric, ScoreDescriptor
from .textutil import normalize

CRITERION_SPLIT = re.compile(r"(?m)^(?:CRITERION:|##)\s+")
FIELD = re.compile(r"(?im)^(ID|MAX|GRANULARITY|NAME)\s*:\s*(.+)$")
DESC = re.compile(r"(?m)^\s*(?:[-*•]\s*)?(-?\d+(?:\.\d+)?)\s*(?::|[-–—])\s*(.+)$")
TABLE_ROW = re.compile(r"^\|(.+)\|$")
NUMBERED = re.compile(
    r"(?m)^\s*(?:(?P<id>[A-Za-z]{0,3}\d+)[.)]|\d+[.)])\s+(?P<name>[^(\n]+?)\s*"
    r"\((?P<max>\d+(?:\.\d+)?)\s*(?:marks?|points?|pts?)\)\s*$"
)


def parse_rubric(source: str | Path, *, rubric_id: str | None = None) -> Rubric:
    path = Path(source) if isinstance(source, Path) or _looks_like_path(source) else None
    if path is not None and path.exists():
        text = _read_any(path)
        default_id = path.stem
        title = path.stem.replace("_", " ")
    else:
        text = str(source)
        default_id = rubric_id or "rubric"
        title = "Untitled rubric"
    text = text.replace("\ufeff", "").replace("\r\n", "\n")
    if not normalize(text):
        raise RubricParseError("empty rubric")
    title_match = re.search(r"(?m)^#\s+(.+)$", text)
    if title_match:
        title = title_match.group(1).strip()

    if re.search(r"(?m)^CRITERION:", text):
        criteria, fmt = _parse_blocks(text), "block"
    elif "|" in text and re.search(r"(?im)^\|.*\bmax\b", text):
        criteria, fmt = _parse_table(text), "table"
    elif NUMBERED.search(text):
        criteria, fmt = _parse_numbered(text), "numbered"
    else:
        criteria, fmt = _parse_blocks(text), "block"
    if not criteria:
        raise RubricParseError("no criteria found")
    _check_ids_unique(criteria)
    return Rubric(id=rubric_id or default_id, title=title, criteria=criteria, source_format=fmt)


def _read_any(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    return path.read_text(encoding="utf-8")


def _looks_like_path(source: str) -> bool:
    return "\n" not in source and len(source) < 512 and any(
        source.endswith(ext) for ext in (".md", ".txt", ".rubric", ".pdf")
    )


def _check_ids_unique(criteria: list[Criterion]) -> None:
    seen = set()
    for c in criteria:
        if c.id in seen:
            raise RubricParseError(f"duplicate criterion id {c.id}")
        seen.add(c.id)


def _parse_blocks(text: str) -> list[Criterion]:
    parts = CRITERION_SPLIT.split(text)
    criteria: list[Criterion] = []
    index = 1
    for part in parts[1:]:
        lines = [ln.rstrip() for ln in part.splitlines() if ln.strip()]
        if not lines:
            continue
        name = re.sub(r"\|.*$", "", lines[0]).strip()
        fields: dict[str, str] = {}
        descriptors: list[ScoreDescriptor] = []
        for line in lines[1:]:
            fm = FIELD.match(line)
            dm = DESC.match(line)
            if fm:
                fields[fm.group(1).upper()] = fm.group(2).strip()
            elif dm:
                descriptors.append(ScoreDescriptor(score=float(dm.group(1)), text=dm.group(2).strip()))
        cid = fields.get("ID") or f"C{index}"
        if "MAX" not in fields:
            raise RubricParseError(f"criterion {cid} has no MAX")
        max_mark = float(fields["MAX"])
        gran = float(fields.get("GRANULARITY") or _infer_granularity(descriptors, max_mark))
        if fields.get("NAME"):
            name = fields["NAME"]
        criteria.append(_make(cid, name, max_mark, gran, descriptors))
        index += 1
    return criteria


def _parse_table(text: str) -> list[Criterion]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        raw = line.strip()
        if not TABLE_ROW.match(raw):
            continue
        cells = [c.strip() for c in raw.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", c or "") for c in cells):
            continue
        rows.append(cells)
    if len(rows) < 2:
        return []
    header = [h.lower() for h in rows[0]]
    criteria: list[Criterion] = []
    for i, row in enumerate(rows[1:], start=1):
        data = {header[j]: row[j] for j in range(min(len(header), len(row)))}
        name = data.get("criterion") or data.get("name") or row[0]
        max_raw = data.get("max") or data.get("max mark") or data.get("marks") or row[1]
        max_mark = float(re.sub(r"[^0-9.]", "", max_raw))
        descriptors = []
        for key, value in data.items():
            if re.fullmatch(r"-?\d+(?:\.\d+)?", key) and value:
                descriptors.append(ScoreDescriptor(score=float(key), text=value))
        gran = _infer_granularity(descriptors, max_mark)
        criteria.append(_make(data.get("id") or f"C{i}", name, max_mark, gran, descriptors))
    return criteria


def _parse_numbered(text: str) -> list[Criterion]:
    matches = list(NUMBERED.finditer(text))
    criteria: list[Criterion] = []
    for idx, m in enumerate(matches, start=1):
        end = matches[idx].start() if idx < len(matches) else len(text)
        body = text[m.end():end]
        descriptors = [
            ScoreDescriptor(score=float(d.group(1)), text=d.group(2).strip())
            for d in DESC.finditer(body)
        ]
        max_mark = float(m.group("max"))
        cid = m.group("id") or f"C{idx}"
        if re.fullmatch(r"\d+", cid):
            cid = f"C{cid}"
        criteria.append(_make(cid, m.group("name").strip(), max_mark, _infer_granularity(descriptors, max_mark), descriptors))
    return criteria


def _make(cid: str, name: str, max_mark: float, gran: float, descriptors: list[ScoreDescriptor]) -> Criterion:
    for d in descriptors:
        if d.score < 0 or d.score > max_mark:
            raise RubricParseError(f"descriptor level {d.score} outside 0..{max_mark} for {cid}")
    return Criterion(id=cid, name=name, max_mark=max_mark, granularity=gran, descriptors=sorted(descriptors, key=lambda d: d.score))


def _infer_granularity(descriptors: list[ScoreDescriptor], max_mark: float) -> float:
    scores = sorted({d.score for d in descriptors} | {0.0, max_mark})
    steps = [round(scores[i + 1] - scores[i], 4) for i in range(len(scores) - 1) if scores[i + 1] > scores[i]]
    return min(steps) if steps else 1.0
