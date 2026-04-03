from __future__ import annotations

import json

from parsers import (
    get_automation_state,
    get_handoff,
    get_preview_status,
    get_suggestion,
    get_work_status,
    list_automation_batches,
    list_pending_suggestions,
    update_work_status,
)


def test_list_pending_suggestions_contract(tmp_path):
    path = tmp_path / "AUTOMATION_SUGGESTIONS.md"
    path.write_text(
        """# AUTOMATION SUGGESTIONS
## Pending Suggestions
### Product Direction
| # | Suggestion | Source | Safety | Effort | Status |
|---|------------|--------|--------|--------|--------|
| P1 | Graph detail panel: names | Chat | safe | medium | pending |
| P2 | Completed item | Chat | safe | medium | done |
""",
        encoding="utf-8",
    )

    result = list_pending_suggestions(str(path))

    assert result["tool"] == "list_pending_suggestions"
    assert result["count"] == 1
    assert result["items"][0]["id"] == "P1"


def test_get_suggestion_contract(tmp_path):
    path = tmp_path / "AUTOMATION_SUGGESTIONS.md"
    path.write_text(
        """# AUTOMATION SUGGESTIONS
## Pending Suggestions
### Product Direction
| # | Suggestion | Source | Safety | Effort | Status |
|---|------------|--------|--------|--------|--------|
| P1 | Graph detail panel: names | Chat | safe | medium | pending |
""",
        encoding="utf-8",
    )

    result = get_suggestion("P1", str(path))

    assert result["tool"] == "get_suggestion"
    assert result["found"] is True
    assert result["item"]["area"] == "graph-detail-panel"


def test_list_batches_and_state_contracts(tmp_path):
    batch_dir = tmp_path / "batches"
    batch_dir.mkdir()
    (batch_dir / "approved_batch_loop_003.json").write_text(json.dumps({"issues": []}), encoding="utf-8")
    state_path = tmp_path / "AUDIT_STATE.json"
    state_path.write_text(json.dumps({"phase": "verify", "loop": 3}), encoding="utf-8")

    batches = list_automation_batches(str(batch_dir))
    state = get_automation_state(str(state_path))

    assert batches["tool"] == "list_automation_batches"
    assert batches["items"][0]["loop"] == "3"
    assert state["tool"] == "get_automation_state"
    assert state["item"]["phase"] == "verify"


def test_preview_handoff_and_work_status_contracts(tmp_path):
    now_path = tmp_path / "AUTOMATION_NOW.md"
    now_path.write_text("# AUTOMATION NOW\n## Batch G next\n", encoding="utf-8")
    next_path = tmp_path / "AUTOMATION_NEXT.md"
    next_path.write_text("# AUTOMATION NEXT\nUpdated: 2026-03-29\n", encoding="utf-8")
    handoff_path = tmp_path / "HANDOFF_LATEST.md"
    handoff_path.write_text("# LATEST HANDOFF\nDate: 2026-04-02\n", encoding="utf-8")
    work_status_path = tmp_path / "WORK_STATUS.json"

    preview = get_preview_status(str(now_path), str(next_path))
    handoff = get_handoff(str(handoff_path))
    work_status = get_work_status(str(work_status_path))

    assert preview["tool"] == "get_preview_status"
    assert preview["item"]["now"]["title"] == "AUTOMATION NOW"
    assert handoff["tool"] == "get_handoff"
    assert handoff["item"]["date"] == "2026-04-02"
    assert work_status["tool"] == "get_work_status"
    assert work_status["item"]["agents"]["cowork"]["status"] == "idle"


def test_update_work_status_contract(tmp_path):
    path = tmp_path / "WORK_STATUS.json"

    result = update_work_status(
        "codex",
        "grapplingmap MCP server",
        "done",
        "codex/mcp-parser-lane",
        "building parsers and tests",
        "01b034a",
        path=str(path),
    )

    assert result["tool"] == "update_work_status"
    assert result["item"]["agents"]["codex"]["status"] == "done"
    assert result["item"]["agents"]["codex"]["last_commit"] == "01b034a"
