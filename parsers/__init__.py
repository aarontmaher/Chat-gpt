from __future__ import annotations

from typing import Any

from config import (
    AUDIT_STATE_FILE,
    AUTOMATION_ACCEPTED_FILE,
    AUTOMATION_NEXT_FILE,
    AUTOMATION_NOW_FILE,
    AUTOMATION_SUGGESTIONS_FILE,
    AUTOMATION_SUGGESTIONS_INBOX_FILE,
    HANDOFF_LATEST_FILE,
    PROJECT_BATCHES_DIR,
    PROJECT_IMPLEMENTATION_DIR,
    SCHEMA_VERSION,
    WORK_STATUS_FILE,
)
from parsers.automation import (
    list_batches,
    read_audit_state,
    read_automation_next,
    read_automation_now,
    read_batch,
    read_implementation,
    read_work_status,
    update_work_status_file,
)
from parsers.handoff import parse_handoff_file
from parsers.suggestions import find_suggestion_by_id, parse_suggestions_file


def read_suggestions(path: str = AUTOMATION_SUGGESTIONS_FILE) -> dict[str, Any]:
    """Read and normalize the main suggestions markdown file."""
    return parse_suggestions_file(path)


def read_suggestions_inbox(path: str = AUTOMATION_SUGGESTIONS_INBOX_FILE) -> dict[str, Any]:
    """Read and normalize the suggestions inbox markdown file."""
    return parse_suggestions_file(path)


def read_accepted_suggestions(path: str = AUTOMATION_ACCEPTED_FILE) -> dict[str, Any]:
    """Read and normalize the accepted suggestions markdown file."""
    return parse_suggestions_file(path)


def read_automation_state(path: str = AUDIT_STATE_FILE) -> dict[str, Any]:
    """Read the current automation state JSON."""
    return read_audit_state(path)


def read_batches(directory: str = PROJECT_BATCHES_DIR) -> list[dict[str, Any]]:
    """Read the list of available batch files."""
    return list_batches(directory)


def list_pending_suggestions(path: str = AUTOMATION_SUGGESTIONS_FILE) -> dict[str, Any]:
    """List normalized pending suggestions from the automation suggestions markdown."""
    parsed = parse_suggestions_file(path)
    items = [item for item in parsed["suggestions"] if "pending" in item.get("status", "").lower()]
    return {"tool": "list_pending_suggestions", "items": items, "count": len(items), "schema_version": SCHEMA_VERSION}


def get_suggestion(suggestion_id: str, path: str = AUTOMATION_SUGGESTIONS_FILE) -> dict[str, Any]:
    """Get one normalized suggestion by suggestion id."""
    item = find_suggestion_by_id(path, suggestion_id)
    return {"tool": "get_suggestion", "item": item, "found": bool(item), "schema_version": SCHEMA_VERSION}


def list_automation_batches(directory: str = PROJECT_BATCHES_DIR) -> dict[str, Any]:
    """List automation batch files with extracted loop numbers where possible."""
    items = list_batches(directory)
    return {"tool": "list_automation_batches", "items": items, "count": len(items), "schema_version": SCHEMA_VERSION}


def get_automation_state(path: str = AUDIT_STATE_FILE) -> dict[str, Any]:
    """Get the current automation audit state."""
    return {"tool": "get_automation_state", "item": read_audit_state(path), "schema_version": SCHEMA_VERSION}


def get_preview_status(now_path: str = AUTOMATION_NOW_FILE, next_path: str = AUTOMATION_NEXT_FILE) -> dict[str, Any]:
    """Get current and next automation preview markdown status."""
    return {
        "tool": "get_preview_status",
        "item": {
            "now": read_automation_now(now_path),
            "next": read_automation_next(next_path),
        },
        "schema_version": SCHEMA_VERSION,
    }


def get_handoff(path: str = HANDOFF_LATEST_FILE) -> dict[str, Any]:
    """Get the latest structured handoff summary."""
    return {"tool": "get_handoff", "item": parse_handoff_file(path), "schema_version": SCHEMA_VERSION}


def read_handoff(path: str = HANDOFF_LATEST_FILE) -> dict[str, Any]:
    """Read the latest handoff artifact."""
    return parse_handoff_file(path)


def get_work_status(path: str = WORK_STATUS_FILE) -> dict[str, Any]:
    """Get current work status for all coding agents — what each is working on, branch, last commit, and blockers."""
    return {"tool": "get_work_status", "item": read_work_status(path), "schema_version": SCHEMA_VERSION}


def update_work_status(
    agent: str,
    task: str,
    status: str,
    branch: str | None,
    summary: str,
    commit: str | None,
    path: str = WORK_STATUS_FILE,
) -> dict[str, Any]:
    """Update work status for a coding agent. Called after meaningful task completion."""
    item = update_work_status_file(agent, task, status, branch, summary, commit, path=path)
    return {"tool": "update_work_status", "item": item, "schema_version": SCHEMA_VERSION}


__all__ = [
    "get_automation_state",
    "get_handoff",
    "get_preview_status",
    "get_suggestion",
    "get_work_status",
    "list_automation_batches",
    "list_pending_suggestions",
    "read_accepted_suggestions",
    "read_audit_state",
    "read_automation_state",
    "read_batch",
    "read_batches",
    "read_implementation",
    "read_handoff",
    "read_suggestions",
    "read_suggestions_inbox",
    "read_work_status",
    "update_work_status",
    "update_work_status_file",
]
