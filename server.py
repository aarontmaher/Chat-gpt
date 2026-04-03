#!/usr/bin/env python3
"""GrapplingMap System MCP Server."""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from audit import log_tool_call
from auth import check_auth
from config import (
    AUDIT_LOG_FILE,
    AUDIT_STATE_PATH,
    AUTOMATION_ACCEPTED_PATH,
    AUTOMATION_NEXT_PATH,
    AUTOMATION_SUGGESTIONS_INBOX_PATH,
    AUTOMATION_SUGGESTIONS_PATH,
    BATCHES_DIR,
    HANDOFF_LATEST_PATH,
    IMPLEMENTATION_RESULTS_DIR,
    ORCHESTRATE_SCRIPT,
    PROJECT_HANDOFF_ARTIFACTS_DIR,
    TOKENS_FILE,
    WORK_STATUS_FILE,
)
from parsers import (
    read_accepted_suggestions,
    read_automation_state,
    read_batch,
    read_batches,
    read_handoff,
    read_suggestions,
    read_suggestions_inbox,
)
from parsers.automation import read_implementation, read_work_status, update_work_status_file
from parsers.suggestions import find_suggestion_by_id
from parsers.whoop_proxy import get_normalized_daily


mcp = FastMCP("GrapplingMap System", host="127.0.0.1", port=3847)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _auth_result(
    tool_name: str,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    tokens_path: str = TOKENS_FILE,
) -> tuple[bool, str, dict[str, Any], str, str]:
    allowed, role, token_info = check_auth(
        tool_name,
        ctx=ctx,
        authorization=authorization,
        tokens_path=tokens_path,
    )
    client = str(token_info.get("client") or getattr(ctx, "client_id", None) or "anonymous")
    user = str(token_info.get("client") or role)
    return allowed, role, token_info, client, user


def _unauthorized_response(tool_name: str, role: str) -> dict[str, Any]:
    return {
        "ok": False,
        "tool": tool_name,
        "error": "unauthorized",
        "role": role,
    }


def _log_and_return(
    tool: str,
    *,
    client: str,
    user: str,
    params: dict[str, Any],
    result: dict[str, Any],
    changes: list[str],
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    log_tool_call(tool, client, user, params, result, changes, path=audit_log_path)
    return result


def list_pending_suggestions_impl(
    filter_source: str | None = None,
    filter_effort: str | None = None,
    filter_status: str | None = None,
) -> dict[str, Any]:
    parsed = read_suggestions(AUTOMATION_SUGGESTIONS_PATH)
    items = list(parsed.get("suggestions", []))

    if filter_source:
        items = [item for item in items if filter_source.lower() in item.get("source", "").lower()]
    if filter_effort:
        items = [item for item in items if filter_effort.lower() in item.get("effort", "").lower()]
    if filter_status:
        items = [item for item in items if filter_status.lower() in item.get("status", "").lower()]
    else:
        items = [item for item in items if "pending" in item.get("status", "").lower()]

    return {"ok": True, "tool": "list_pending_suggestions", "count": len(items), "items": items}


def get_suggestion_impl(suggestion_id: str) -> dict[str, Any]:
    for path in (AUTOMATION_SUGGESTIONS_PATH, AUTOMATION_NEXT_PATH, AUTOMATION_ACCEPTED_PATH):
        item = find_suggestion_by_id(path, suggestion_id)
        if item:
            return {"ok": True, "tool": "get_suggestion", "item": item, "found": True}
    return {"ok": False, "tool": "get_suggestion", "item": {}, "found": False}


def list_automation_batches_impl(limit: int = 10) -> dict[str, Any]:
    items = read_batches(BATCHES_DIR)[:limit]
    return {"ok": True, "tool": "list_automation_batches", "count": len(items), "items": items}


def get_automation_state_impl() -> dict[str, Any]:
    return {"ok": True, "tool": "get_automation_state", "item": read_automation_state(AUDIT_STATE_PATH)}


def get_preview_status_impl(loop: int) -> dict[str, Any]:
    item = read_implementation(loop, IMPLEMENTATION_RESULTS_DIR)
    return {"ok": bool(item), "tool": "get_preview_status", "loop": loop, "item": item}


def get_handoff_impl() -> dict[str, Any]:
    return {"ok": True, "tool": "get_handoff", "item": read_handoff(HANDOFF_LATEST_PATH)}


def get_daily_performance_object_impl(date: str, tokens_path: str | None = None) -> dict[str, Any]:
    item = get_normalized_daily(date, tokens_path=tokens_path or os.path.expanduser("~/whoop-integration/whoop_tokens.json"))
    return {"ok": "error" not in item, "tool": "get_daily_performance_object", "item": item}


def get_work_status_impl(work_status_path: str = WORK_STATUS_FILE) -> dict[str, Any]:
    return {"ok": True, "tool": "get_work_status", "item": read_work_status(work_status_path)}


def submit_suggestion_impl(
    title: str,
    detail: str,
    source: str,
    area: str,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    inbox_path: str = AUTOMATION_SUGGESTIONS_INBOX_PATH,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("submit_suggestion", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"title": title, "detail": detail, "source": source, "area": area}
    if not allowed:
        return _log_and_return(
            "submit_suggestion",
            client=client,
            user=user,
            params=params,
            result=_unauthorized_response("submit_suggestion", role),
            changes=[],
            audit_log_path=audit_log_path,
        )

    _ensure_inbox_file(inbox_path)
    line = f"- Source: {source} | Title: {title} | Area: {area or 'general'} | Detail: {detail}\n"
    with open(inbox_path, "a", encoding="utf-8") as handle:
        handle.write(line)

    result = {"ok": True, "tool": "submit_suggestion", "submitted_at": _now_iso(), "title": title}
    return _log_and_return(
        "submit_suggestion",
        client=client,
        user=user,
        params=params,
        result=result,
        changes=[f"{inbox_path}: appended suggestion '{title}'"],
        audit_log_path=audit_log_path,
    )


def approve_suggestion_for_preview_impl(
    suggestion_id: str,
    reviewer: str,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    suggestions_path: str = AUTOMATION_SUGGESTIONS_PATH,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result(
        "approve_suggestion_for_preview",
        ctx=ctx,
        authorization=authorization,
        tokens_path=tokens_path,
    )
    params = {"id": suggestion_id, "reviewer": reviewer}
    if not allowed:
        return _log_and_return(
            "approve_suggestion_for_preview",
            client=client,
            user=user,
            params=params,
            result=_unauthorized_response("approve_suggestion_for_preview", role),
            changes=[],
            audit_log_path=audit_log_path,
        )

    found, before, after = _update_suggestion_status_in_file(suggestions_path, suggestion_id, "approved")
    result = {"ok": found, "tool": "approve_suggestion_for_preview", "id": suggestion_id, "reviewer": reviewer}
    changes = [f"{suggestions_path}: {before} -> {after}"] if found else []
    return _log_and_return(
        "approve_suggestion_for_preview",
        client=client,
        user=user,
        params=params,
        result=result,
        changes=changes,
        audit_log_path=audit_log_path,
    )


def create_handoff_artifact_impl(
    suggestion_ids: list[str],
    instructions: str,
    target_branch: str,
    constraints: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    handoff_dir: str = PROJECT_HANDOFF_ARTIFACTS_DIR,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result(
        "create_handoff_artifact",
        ctx=ctx,
        authorization=authorization,
        tokens_path=tokens_path,
    )
    params = {
        "suggestion_ids": suggestion_ids,
        "instructions": instructions,
        "target_branch": target_branch,
        "constraints": constraints or [],
        "acceptance_criteria": acceptance_criteria or [],
    }
    if not allowed:
        return _log_and_return(
            "create_handoff_artifact",
            client=client,
            user=user,
            params=params,
            result=_unauthorized_response("create_handoff_artifact", role),
            changes=[],
            audit_log_path=audit_log_path,
        )

    os.makedirs(handoff_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact_id = f"handoff-{stamp}"
    artifact_path = os.path.join(handoff_dir, f"{artifact_id}.json")
    artifact = {
        "id": artifact_id,
        "created_at": _now_iso(),
        "suggestion_ids": suggestion_ids,
        "instructions": instructions,
        "target_branch": target_branch,
        "constraints": constraints or [],
        "acceptance_criteria": acceptance_criteria or [],
    }
    with open(artifact_path, "w", encoding="utf-8") as handle:
        json.dump(artifact, handle, indent=2)

    result = {"ok": True, "tool": "create_handoff_artifact", "item": artifact, "path": artifact_path}
    return _log_and_return(
        "create_handoff_artifact",
        client=client,
        user=user,
        params=params,
        result=result,
        changes=[f"{artifact_path}: created handoff artifact"],
        audit_log_path=audit_log_path,
    )


def start_preview_run_impl(
    loop: int,
    agent: str,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    audit_state_path: str = AUDIT_STATE_PATH,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("start_preview_run", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"loop": loop, "agent": agent}
    if not allowed:
        return _log_and_return(
            "start_preview_run",
            client=client,
            user=user,
            params=params,
            result=_unauthorized_response("start_preview_run", role),
            changes=[],
            audit_log_path=audit_log_path,
        )

    state = read_automation_state(audit_state_path) or {}
    implementation = dict(state.get("implementation_status") or {})
    implementation.update(
        {
            "complete": False,
            "agent": agent,
            "loop": loop,
            "status": "in_progress",
            "started_at": _now_iso(),
        }
    )
    state["implementation_status"] = implementation
    with open(audit_state_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)

    result = {"ok": True, "tool": "start_preview_run", "item": implementation}
    return _log_and_return(
        "start_preview_run",
        client=client,
        user=user,
        params=params,
        result=result,
        changes=[f"{audit_state_path}: implementation_status updated for loop {loop}"],
        audit_log_path=audit_log_path,
    )


def advance_phase_impl(
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    orchestrate_script: str = ORCHESTRATE_SCRIPT,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("advance_phase", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params: dict[str, Any] = {}
    if not allowed:
        return _log_and_return(
            "advance_phase",
            client=client,
            user=user,
            params=params,
            result=_unauthorized_response("advance_phase", role),
            changes=[],
            audit_log_path=audit_log_path,
        )

    result = _run_orchestrate(orchestrate_script, "advance")
    return _log_and_return(
        "advance_phase",
        client=client,
        user=user,
        params=params,
        result=result,
        changes=["orchestrate.py advance"],
        audit_log_path=audit_log_path,
    )


def update_work_status_impl(
    agent: str,
    task: str,
    status: str,
    branch: str | None = None,
    summary: str | None = None,
    commit: str | None = None,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    work_status_path: str = WORK_STATUS_FILE,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("update_work_status", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {
        "agent": agent,
        "task": task,
        "status": status,
        "branch": branch,
        "summary": summary,
        "commit": commit,
    }
    if not allowed:
        return _log_and_return(
            "update_work_status",
            client=client,
            user=user,
            params=params,
            result=_unauthorized_response("update_work_status", role),
            changes=[],
            audit_log_path=audit_log_path,
        )

    item = update_work_status_file(agent, task, status, branch, summary, commit, path=work_status_path)
    result = {"ok": True, "tool": "update_work_status", "item": item}
    return _log_and_return(
        "update_work_status",
        client=client,
        user=user,
        params=params,
        result=result,
        changes=[f"{work_status_path}: updated {agent} status"],
        audit_log_path=audit_log_path,
    )


def approve_batch_impl(
    loop: int,
    reviewer: str,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    orchestrate_script: str = ORCHESTRATE_SCRIPT,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("approve_batch", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"loop": loop, "reviewer": reviewer}
    if not allowed:
        return _log_and_return(
            "approve_batch",
            client=client,
            user=user,
            params=params,
            result=_unauthorized_response("approve_batch", role),
            changes=[],
            audit_log_path=audit_log_path,
        )

    result = _run_orchestrate(orchestrate_script, "approve")
    return _log_and_return(
        "approve_batch",
        client=client,
        user=reviewer or user,
        params=params,
        result=result,
        changes=["orchestrate.py approve"],
        audit_log_path=audit_log_path,
    )


def _ensure_inbox_file(path: str) -> None:
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("# AUTOMATION SUGGESTIONS INBOX\n\n## Pending Inbox\n")


def _update_suggestion_status_in_file(path: str, suggestion_id: str, new_status: str) -> tuple[bool, str, str]:
    if not os.path.exists(path):
        return False, "", ""

    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.readlines()

    before = ""
    after = ""
    found = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(f"| {suggestion_id} |"):
            parts = [part.strip() for part in stripped.strip("|").split("|")]
            if len(parts) >= 6:
                before = parts[-1]
                parts[-1] = new_status
                lines[index] = "| " + " | ".join(parts) + " |\n"
                after = new_status
                found = True
                break

    if found:
        with open(path, "w", encoding="utf-8") as handle:
            handle.writelines(lines)
    return found, before, after


def _run_orchestrate(script_path: str, command: str) -> dict[str, Any]:
    if not os.path.exists(script_path):
        return {"ok": False, "error": f"{script_path} not found"}
    try:
        completed = subprocess.run(
            ["python3", script_path, command],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    return {
        "ok": completed.returncode == 0,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": completed.returncode,
    }


@mcp.tool()
def list_pending_suggestions(
    filter_source: str | None = None,
    filter_effort: str | None = None,
    filter_status: str | None = None,
) -> dict[str, Any]:
    """List pending suggestions from the main suggestion queue, optionally filtered by source, effort, or status."""
    return list_pending_suggestions_impl(filter_source, filter_effort, filter_status)


@mcp.tool()
def get_suggestion(id: str) -> dict[str, Any]:
    """Get a single suggestion by ID from suggestions, next queue, or accepted files."""
    return get_suggestion_impl(id)


@mcp.tool()
def list_automation_batches(limit: int = 10) -> dict[str, Any]:
    """List recent automation batch files."""
    return list_automation_batches_impl(limit)


@mcp.tool()
def get_automation_state() -> dict[str, Any]:
    """Get the current automation state from AUDIT_STATE.json."""
    return get_automation_state_impl()


@mcp.tool()
def get_preview_status(loop: int) -> dict[str, Any]:
    """Get the preview or implementation status object for a loop."""
    return get_preview_status_impl(loop)


@mcp.tool()
def get_handoff() -> dict[str, Any]:
    """Get the latest structured handoff artifact."""
    return get_handoff_impl()


@mcp.tool()
def get_daily_performance_object(date: str) -> dict[str, Any]:
    """Get a normalized WHOOP daily performance object for a date."""
    return get_daily_performance_object_impl(date)


@mcp.tool()
def get_work_status() -> dict[str, Any]:
    """Get current work status for all coding agents — what each is working on, branch, last commit, and blockers."""
    return get_work_status_impl()


@mcp.tool()
def submit_suggestion(
    title: str,
    detail: str,
    source: str,
    area: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Submit a suggestion into the inbox for later review."""
    return submit_suggestion_impl(title, detail, source, area, ctx=ctx)


@mcp.tool()
def approve_suggestion_for_preview(id: str, reviewer: str, ctx: Context | None = None) -> dict[str, Any]:
    """Approve a suggestion in the main markdown queue for preview work."""
    return approve_suggestion_for_preview_impl(id, reviewer, ctx=ctx)


@mcp.tool()
def create_handoff_artifact(
    suggestion_ids: list[str],
    instructions: str,
    target_branch: str,
    constraints: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a machine-readable handoff artifact for downstream coding agents."""
    return create_handoff_artifact_impl(
        suggestion_ids,
        instructions,
        target_branch,
        constraints,
        acceptance_criteria,
        ctx=ctx,
    )


@mcp.tool()
def start_preview_run(loop: int, agent: str, ctx: Context | None = None) -> dict[str, Any]:
    """Mark a preview run as started in the automation state."""
    return start_preview_run_impl(loop, agent, ctx=ctx)


@mcp.tool()
def advance_phase(ctx: Context | None = None) -> dict[str, Any]:
    """Advance the automation phase using the shared orchestrate script."""
    return advance_phase_impl(ctx=ctx)


@mcp.tool()
def update_work_status(
    agent: str,
    task: str,
    status: str,
    branch: str | None = None,
    summary: str | None = None,
    commit: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update work status for a coding agent. Called after meaningful task completion."""
    return update_work_status_impl(agent, task, status, branch, summary, commit, ctx=ctx)


@mcp.tool()
def approve_batch(loop: int, reviewer: str, ctx: Context | None = None) -> dict[str, Any]:
    """Approve the current batch for implementation via the shared orchestrate script."""
    return approve_batch_impl(loop, reviewer, ctx=ctx)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
