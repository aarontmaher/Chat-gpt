"""Append-only audit logging for MCP tool calls."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from config import AUDIT_LOG_FILE


def log_tool_call(
    tool: str,
    client: str,
    user: str,
    params: dict[str, Any],
    result: Any,
    changes: list[str],
    path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    """Append one JSONL entry for a tool call and return the entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "tool": tool,
        "client": client,
        "user": user,
        "params": params,
        "result": result,
        "changes": changes,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    return entry
