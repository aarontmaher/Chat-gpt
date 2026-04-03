from __future__ import annotations

import os
import re
from typing import Any

from config import HANDOFF_LATEST_FILE, SCHEMA_VERSION
from parsers.suggestions import parse_markdown_tables


def parse_handoff_file(path: str = HANDOFF_LATEST_FILE) -> dict[str, Any]:
    if not os.path.exists(path):
        return {
            "path": path,
            "schema_version": SCHEMA_VERSION,
            "date": "",
            "current_state": "",
            "commits": [],
            "suggestion_status": [],
            "smoke_tests": "",
            "remaining": [],
        }

    text = _read_text(path)
    status_rows = []
    for table in parse_markdown_tables(text):
        if "Final Status" in (table["subsection"] or table["section"]):
            status_rows.extend(table["rows"])

    return {
        "path": path,
        "schema_version": SCHEMA_VERSION,
        "date": _extract_metadata(text, "Date"),
        "current_state": _extract_section_body(text, "Current State").strip(),
        "commits": _parse_commits(_extract_section_body(text, "Today's Commits")),
        "suggestion_status": status_rows,
        "smoke_tests": _extract_section_body(text, "Smoke Tests").strip(),
        "remaining": _parse_bullets(_extract_section_body(text, "Remaining — Aaron Only")),
    }


def _extract_metadata(text: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_section_body(text: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_commits(text: str) -> list[dict[str, str]]:
    commits = []
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"^\d+\.\s+`([^`]+)`\s+[—-]\s+(.*)$", stripped)
        if match:
            commits.append({"commit": match.group(1), "summary": match.group(2).strip()})
    return commits


def _parse_bullets(text: str) -> list[str]:
    items = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
