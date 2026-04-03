from __future__ import annotations

import json

from auth import check_auth, extract_bearer_token, load_tokens
from config import TOOL_TIER_REQUIREMENTS, get_route_auth, get_tool_tier


def test_route_auth_matches_api_contract():
    assert get_route_auth("/api/me/profile") == {
        "path": "/api/me/profile",
        "auth_required": True,
        "auth_type": "bearer",
        "scope": "private",
    }
    assert get_route_auth("/api/aggregate/popular-techniques") == {
        "path": "/api/aggregate/popular-techniques",
        "auth_required": False,
        "auth_type": "none",
        "scope": "public",
    }


def test_graph_and_syllabus_routes_are_public():
    assert get_route_auth("/api/graph/path")["scope"] == "public"
    assert get_route_auth("/api/syllabus/white")["auth_required"] is False


def test_tool_tier_catalog_matches_server_contract():
    assert len(TOOL_TIER_REQUIREMENTS) == 15
    assert get_tool_tier("get_work_status") == 1
    assert get_tool_tier("update_work_status") == 3
    assert get_tool_tier("approve_batch") == 4
    assert get_tool_tier("submit_suggestion") == 2


def test_check_auth_uses_tokens_json_roles(tmp_path):
    tokens_path = tmp_path / "tokens.json"
    tokens_path.write_text(
        json.dumps(
            {
                "tokens": [
                    {"token": "viewer-token", "role": "viewer", "client": "test"},
                    {"token": "operator-token", "role": "operator", "client": "codex"},
                    {"token": "admin-token", "role": "admin", "client": "claude-chat"},
                ]
            }
        ),
        encoding="utf-8",
    )

    loaded = load_tokens(str(tokens_path))
    assert loaded["operator-token"]["role"] == "operator"

    read_allowed, role, _ = check_auth("get_work_status", tokens_path=str(tokens_path))
    assert read_allowed is True
    assert role == "viewer"

    write_denied, denied_role, _ = check_auth("update_work_status", tokens_path=str(tokens_path))
    assert write_denied is False
    assert denied_role == "none"

    write_allowed, operator_role, token_info = check_auth(
        "update_work_status",
        authorization="Bearer operator-token",
        tokens_path=str(tokens_path),
    )
    assert write_allowed is True
    assert operator_role == "operator"
    assert token_info["client"] == "codex"

    admin_allowed, admin_role, _ = check_auth(
        "approve_batch",
        authorization="Bearer admin-token",
        tokens_path=str(tokens_path),
    )
    assert admin_allowed is True
    assert admin_role == "admin"


def test_extract_bearer_token_parses_header():
    assert extract_bearer_token(authorization="Bearer hello") == "hello"
    assert extract_bearer_token(authorization="Token hello") is None
