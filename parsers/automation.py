from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from config import (
    AUDIT_STATE_FILE,
    AUTOMATION_NEXT_FILE,
    AUTOMATION_NOW_FILE,
    ISSUES_FILE,
    PROJECT_BATCHES_DIR,
    PROJECT_IMPLEMENTATION_DIR,
    SCHEMA_VERSION,
    WORK_STATUS_FILE,
)
from parsers.suggestions import parse_markdown_tables


def read_audit_state(path: str = AUDIT_STATE_FILE) -> dict[str, Any]:
    return _read_json_file(path)


def read_issues(path: str = ISSUES_FILE) -> list[dict[str, Any]]:
    payload = _read_json_file(path)
    issues = payload.get("issues")
    return issues if isinstance(issues, list) else []


def list_batches(directory: str = PROJECT_BATCHES_DIR) -> list[dict[str, Any]]:
    if not os.path.isdir(directory):
        return []

    items = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        items.append(
            {
                "loop": _extract_loop_number(name),
                "filename": name,
                "path": os.path.join(directory, name),
            }
        )
    return items


def read_batch(loop: int | str, directory: str = PROJECT_BATCHES_DIR) -> dict[str, Any]:
    loop_text = str(loop)
    for item in list_batches(directory):
        if item["loop"] == loop_text:
            payload = _read_json_file(item["path"])
            payload["loop"] = loop_text
            payload["path"] = item["path"]
            return payload
    return {}


def read_implementation(loop: int | str, directory: str = PROJECT_IMPLEMENTATION_DIR) -> dict[str, Any]:
    if not os.path.isdir(directory):
        return {}

    loop_text = str(loop)
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        if _extract_loop_number(name) == loop_text:
            payload = _read_json_file(os.path.join(directory, name))
            payload["loop"] = loop_text
            payload["path"] = os.path.join(directory, name)
            return payload
    return {}


def read_automation_next(path: str = AUTOMATION_NEXT_FILE) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    text = _read_text(path)
    return {
        "path": path,
        "title": _extract_title(text),
        "updated": _extract_metadata_value(text, "Updated"),
        "sections": _parse_table_sections(text),
    }


def read_automation_now(path: str = AUTOMATION_NOW_FILE) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    text = _read_text(path)
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("# ")]
    return {
        "path": path,
        "title": _extract_title(text),
        "lines": lines,
        "summary": lines[0] if lines else "",
    }


def read_work_status(path: str = WORK_STATUS_FILE) -> dict[str, Any]:
    default = _default_work_status()
    payload = _read_json_file(path)
    if not payload:
        return default

    agents = payload.get("agents")
    if not isinstance(agents, dict):
        return default

    merged = default
    for agent_name, agent_data in agents.items():
        if isinstance(agent_data, dict):
            merged["agents"][agent_name] = _normalize_agent_status(agent_data)
    merged["updated_at"] = payload.get("updated_at")
    return merged


def update_work_status_file(
    agent: str,
    task: str,
    status: str,
    branch: str | None,
    summary: str,
    commit: str | None,
    path: str = WORK_STATUS_FILE,
) -> dict[str, Any]:
    payload = read_work_status(path)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload.setdefault("agents", {})
    payload["agents"][agent] = {
        "task": task,
        "status": status,
        "branch": branch,
        "commit": commit,
        "last_commit": commit,
        "summary": summary,
        "updated_at": now,
    }
    payload["updated_at"] = now

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return payload


def _read_json_file(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def _extract_loop_number(filename: str) -> str:
    match = re.search(r"loop[_-]?(\d+)", filename, flags=re.IGNORECASE)
    if not match:
        return ""
    return str(int(match.group(1)))


def _extract_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _extract_metadata_value(text: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _parse_table_sections(text: str) -> list[dict[str, Any]]:
    sections = []
    for table in parse_markdown_tables(text):
        sections.append(
            {
                "section": table["subsection"] or table["section"],
                "rows": table["rows"],
                "count": len(table["rows"]),
            }
        )
    return sections


def _default_work_status() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "agents": {
            "claude_code": {
                "task": None,
                "status": "idle",
                "branch": None,
                "commit": None,
                "last_commit": None,
                "summary": None,
                "updated_at": None,
            },
            "codex": {
                "task": None,
                "status": "idle",
                "branch": None,
                "commit": None,
                "last_commit": None,
                "summary": None,
                "updated_at": None,
            },
            "cowork": {
                "task": None,
                "status": "idle",
                "branch": None,
                "commit": None,
                "last_commit": None,
                "summary": None,
                "updated_at": None,
            },
        },
        "updated_at": None,
    }


def _normalize_agent_status(agent_data: dict[str, Any]) -> dict[str, Any]:
    commit = agent_data.get("commit", agent_data.get("last_commit"))
    return {
        "task": agent_data.get("task"),
        "status": agent_data.get("status", "idle"),
        "branch": agent_data.get("branch"),
        "commit": commit,
        "last_commit": commit,
        "summary": agent_data.get("summary"),
        "updated_at": agent_data.get("updated_at"),
    }
