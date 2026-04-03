"""Token-based auth with role tiers for GrapplingMap MCP tools."""
from __future__ import annotations

import json
from typing import Any

from config import TOKENS_FILE, get_tool_tier


ROLE_TIERS = {
    "viewer": 1,
    "contributor": 2,
    "operator": 3,
    "admin": 4,
}


def load_tokens(path: str = TOKENS_FILE) -> dict[str, dict[str, Any]]:
    """Load bearer tokens from tokens.json keyed by token string."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}

    tokens = payload.get("tokens", [])
    if not isinstance(tokens, list):
        return {}

    loaded: dict[str, dict[str, Any]] = {}
    for item in tokens:
        if isinstance(item, dict) and item.get("token"):
            loaded[str(item["token"])] = item
    return loaded


def check_auth(
    tool_name: str,
    *,
    ctx: Any | None = None,
    authorization: str | None = None,
    tokens_path: str = TOKENS_FILE,
) -> tuple[bool, str, dict[str, Any]]:
    """Return (allowed, role, token_info) for a tool call.

    Tier 1 tools are public and do not require a token.
    For Tier 2+ tools, bearer auth is read from the explicit authorization string
    or the FastMCP request context when available.
    """
    required_tier = get_tool_tier(tool_name) or 1
    if required_tier <= 1:
        return True, "viewer", {}

    token = extract_bearer_token(ctx=ctx, authorization=authorization)
    if not token:
        return False, "none", {}

    token_info = load_tokens(tokens_path).get(token)
    if not token_info:
        return False, "invalid", {}

    role = str(token_info.get("role", "viewer"))
    role_tier = ROLE_TIERS.get(role, 0)
    return role_tier >= required_tier, role, token_info


def extract_bearer_token(*, ctx: Any | None = None, authorization: str | None = None) -> str | None:
    """Extract the bearer token from an auth header or FastMCP context."""
    header_value = authorization
    if header_value is None and ctx is not None:
        request = getattr(getattr(ctx, "request_context", None), "request", None)
        headers = getattr(request, "headers", None)
        if headers is not None:
            header_value = headers.get("authorization")

    if not header_value or not isinstance(header_value, str):
        return None

    parts = header_value.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None
