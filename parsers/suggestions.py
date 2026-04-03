from __future__ import annotations

import os
import re
from typing import Any

from config import SCHEMA_VERSION


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")


def parse_markdown_tables(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    tables: list[dict[str, Any]] = []
    section = ""
    subsection = ""
    index = 0

    while index < len(lines):
        stripped = lines[index].strip()
        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading = heading_match.group(2).strip()
            if level == 2:
                section = heading
                subsection = ""
            elif level == 3:
                subsection = heading
            index += 1
            continue

        if (
            stripped.startswith("|")
            and index + 1 < len(lines)
            and TABLE_SEPARATOR_RE.match(lines[index + 1].strip())
        ):
            table_lines = [stripped, lines[index + 1].strip()]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            table = _parse_table_lines(table_lines)
            tables.append(
                {
                    "section": section,
                    "subsection": subsection,
                    "headers": table["headers"],
                    "rows": table["rows"],
                }
            )
            continue

        index += 1

    return tables


def parse_suggestions_file(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {
            "path": path,
            "schema_version": SCHEMA_VERSION,
            "already_shipped": [],
            "suggestions": [],
            "sections": [],
            "count": 0,
        }

    text = _read_text(path)
    tables = parse_markdown_tables(text)
    shipped = _parse_already_shipped(text)
    suggestions: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []

    for table in tables:
        normalized_rows = [_normalize_suggestion_row(row, table["section"], table["subsection"]) for row in table["rows"]]
        sections.append(
            {
                "section": table["section"],
                "subsection": table["subsection"],
                "items": normalized_rows,
                "count": len(normalized_rows),
            }
        )
        suggestions.extend(normalized_rows)

    return {
        "path": path,
        "schema_version": SCHEMA_VERSION,
        "already_shipped": shipped,
        "suggestions": suggestions,
        "sections": sections,
        "count": len(suggestions),
    }


def find_suggestion_by_id(path: str, suggestion_id: str) -> dict[str, Any]:
    parsed = parse_suggestions_file(path)
    for item in parsed["suggestions"]:
        if item.get("id") == suggestion_id:
            return item
    return {}


def _parse_table_lines(lines: list[str]) -> dict[str, Any]:
    headers = [_normalize_header(value) for value in _split_table_row(lines[0])]
    rows = []
    for line in lines[2:]:
        values = _split_table_row(line)
        row = {headers[index]: values[index] if index < len(values) else "" for index in range(len(headers))}
        rows.append(row)
    return {"headers": headers, "rows": rows}


def _split_table_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def _normalize_header(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "#":
        return "id"
    if normalized == "suggestion":
        return "title"
    return normalized.replace(" ", "_")


def _normalize_suggestion_row(row: dict[str, str], section: str, subsection: str) -> dict[str, Any]:
    title = row.get("title") or row.get("item") or row.get("description") or ""
    suggestion_id = row.get("id") or _extract_id_from_title(title)
    status = row.get("status", "")

    return {
        "id": suggestion_id,
        "title": title,
        "source": row.get("source", ""),
        "safety": row.get("safety", ""),
        "effort": row.get("effort", ""),
        "status": status,
        "category": subsection or section,
        "area": _infer_area(title),
        "raw": row,
    }


def _extract_id_from_title(title: str) -> str:
    match = re.match(r"^([A-Z]{1,4}\d+)\b", title)
    return match.group(1) if match else ""


def _infer_area(title: str) -> str:
    if ":" in title:
        head = title.split(":", 1)[0]
        return _slugify(head)
    words = re.findall(r"[A-Za-z0-9]+", title)
    if not words:
        return ""
    return _slugify(words[0])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug


def _parse_already_shipped(text: str) -> list[str]:
    match = re.search(
        r"^## Already Shipped This Session\s*\n(.*?)(?:\n## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        return []

    body = " ".join(line.strip() for line in match.group(1).splitlines() if line.strip())
    parts = [part.strip().rstrip(".") for part in body.split(",")]
    return [part for part in parts if part]


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
