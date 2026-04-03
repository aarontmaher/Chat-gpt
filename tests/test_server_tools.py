from __future__ import annotations

import json

import server


def _write_tokens(path):
    path.write_text(
        json.dumps(
            {
                "tokens": [
                    {"token": "gm_op_codex", "role": "operator", "client": "codex", "created_at": "2026-04-03"},
                    {"token": "gm_admin_aaron", "role": "admin", "client": "claude-chat", "created_at": "2026-04-03"},
                ]
            }
        ),
        encoding="utf-8",
    )


def test_server_registers_expected_fifteen_tools():
    tool_names = list(server.mcp._tool_manager._tools.keys())

    assert len(tool_names) == 15
    assert "get_work_status" in tool_names
    assert "update_work_status" in tool_names
    assert "approve_batch" in tool_names


def test_read_tool_contracts_return_expected_top_level_keys(tmp_path, monkeypatch):
    suggestions_path = tmp_path / "AUTOMATION_SUGGESTIONS.md"
    suggestions_path.write_text(
        """# AUTOMATION SUGGESTIONS
## Pending Suggestions
### Product Direction
| # | Suggestion | Source | Safety | Effort | Status |
|---|------------|--------|--------|--------|--------|
| P1 | Home screen card | Chat | safe | medium | pending |
""",
        encoding="utf-8",
    )
    batch_dir = tmp_path / "batches"
    batch_dir.mkdir()
    (batch_dir / "approved_batch_loop_002.json").write_text(json.dumps({"issues": []}), encoding="utf-8")
    state_path = tmp_path / "AUDIT_STATE.json"
    state_path.write_text(json.dumps({"phase": "audit", "loop": 2}), encoding="utf-8")
    handoff_path = tmp_path / "HANDOFF_LATEST.md"
    handoff_path.write_text("# LATEST HANDOFF\nDate: 2026-04-02\n", encoding="utf-8")
    impl_dir = tmp_path / "implementation"
    impl_dir.mkdir()
    (impl_dir / "impl_loop_002.json").write_text(json.dumps({"status": "done"}), encoding="utf-8")

    monkeypatch.setattr(server, "AUTOMATION_SUGGESTIONS_PATH", str(suggestions_path))
    monkeypatch.setattr(server, "BATCHES_DIR", str(batch_dir))
    monkeypatch.setattr(server, "AUDIT_STATE_PATH", str(state_path))
    monkeypatch.setattr(server, "HANDOFF_LATEST_PATH", str(handoff_path))
    monkeypatch.setattr(server, "IMPLEMENTATION_RESULTS_DIR", str(impl_dir))
    monkeypatch.setattr(server, "get_normalized_daily", lambda date, tokens_path=None: {"date": date, "recovery": {}, "strain": {}, "sleep": {}, "workouts": []})

    assert server.list_pending_suggestions_impl()["tool"] == "list_pending_suggestions"
    assert server.get_suggestion_impl("P1")["found"] is True
    assert server.list_automation_batches_impl()["tool"] == "list_automation_batches"
    assert server.get_automation_state_impl()["item"]["phase"] == "audit"
    assert server.get_preview_status_impl(2)["item"]["status"] == "done"
    assert server.get_handoff_impl()["item"]["date"] == "2026-04-02"
    assert server.get_daily_performance_object_impl("2026-04-02")["item"]["date"] == "2026-04-02"


def test_write_tools_reject_calls_without_auth_and_log(tmp_path):
    tokens_path = tmp_path / "tokens.json"
    audit_log_path = tmp_path / "audit_log.jsonl"
    inbox_path = tmp_path / "AUTOMATION_SUGGESTIONS_INBOX.md"
    _write_tokens(tokens_path)

    result = server.submit_suggestion_impl(
        "New suggestion",
        "Details",
        "codex",
        "graph",
        tokens_path=str(tokens_path),
        audit_log_path=str(audit_log_path),
        inbox_path=str(inbox_path),
    )

    assert result["ok"] is False
    assert result["error"] == "unauthorized"
    log_lines = audit_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1


def test_write_tools_accept_valid_operator_or_admin_and_append_audit_log(tmp_path):
    tokens_path = tmp_path / "tokens.json"
    audit_log_path = tmp_path / "audit_log.jsonl"
    work_status_path = tmp_path / "WORK_STATUS.json"
    script_path = tmp_path / "orchestrate.py"
    script_path.write_text("import sys\nprint(f'ran {sys.argv[1]}')\n", encoding="utf-8")
    _write_tokens(tokens_path)

    operator_result = server.update_work_status_impl(
        "codex",
        "MCP server build",
        "in_progress",
        "codex/mcp-server",
        "building server layer on parsers",
        None,
        authorization="Bearer gm_op_codex",
        tokens_path=str(tokens_path),
        audit_log_path=str(audit_log_path),
        work_status_path=str(work_status_path),
    )
    admin_result = server.approve_batch_impl(
        2,
        "aaron",
        authorization="Bearer gm_admin_aaron",
        tokens_path=str(tokens_path),
        audit_log_path=str(audit_log_path),
        orchestrate_script=str(script_path),
    )

    assert operator_result["ok"] is True
    assert operator_result["item"]["agents"]["codex"]["status"] == "in_progress"
    assert admin_result["ok"] is True

    log_lines = audit_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 2


def test_get_work_status_returns_safe_template_when_file_missing(tmp_path):
    result = server.get_work_status_impl(str(tmp_path / "WORK_STATUS.json"))

    assert result["ok"] is True
    assert result["item"]["agents"]["claude_code"]["status"] == "idle"
    assert "commit" in result["item"]["agents"]["codex"]
