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
from auth import authenticate_request, can_access_user, check_auth
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
    PROMPT_JOBS_FILE,
    SHARED_MEMORY_FILE,
    PROJECT_HANDOFF_ARTIFACTS_DIR,
    TOKENS_FILE,
    WORK_STATUS_FILE,
)
from parsers import (
    cancel_prompt_job as cancel_prompt_job_parser,
    claim_prompt_job as claim_prompt_job_parser,
    complete_prompt_job as complete_prompt_job_parser,
    create_prompt_job as create_prompt_job_parser,
    fail_prompt_job as fail_prompt_job_parser,
    get_prompt_job as get_prompt_job_parser,
    read_accepted_suggestions,
    read_automation_state,
    read_batch,
    read_batches,
    read_handoff,
    list_prompt_jobs as list_prompt_jobs_parser,
    read_suggestions,
    read_suggestions_inbox,
)
from parsers.automation import read_implementation, read_work_status, update_work_status_file
from parsers.suggestions import find_suggestion_by_id
from parsers.whoop_proxy import get_normalized_daily


mcp = FastMCP("GrapplingMap System", host="0.0.0.0", port=3847)


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


def create_prompt_job_impl(
    target_agent: str,
    prompt: str,
    source_client: str | None = None,
    priority: str = "normal",
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    prompt_jobs_path: str = PROMPT_JOBS_FILE,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, token_info, client, user = _auth_result("create_prompt_job", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"target_agent": target_agent, "prompt": prompt, "source_client": source_client, "priority": priority}
    if not allowed:
        return _log_and_return("create_prompt_job", client=client, user=user, params=params, result=_unauthorized_response("create_prompt_job", role), changes=[], audit_log_path=audit_log_path)
    item = create_prompt_job_parser(target_agent, prompt, source_client or str(token_info.get("client") or client), priority, path=prompt_jobs_path)
    return _log_and_return(
        "create_prompt_job",
        client=client,
        user=user,
        params=params,
        result=item,
        changes=[f"{prompt_jobs_path}: created prompt job {item['item']['id']}"],
        audit_log_path=audit_log_path,
    )


def list_prompt_jobs_impl(
    status: str | None = None,
    target_agent: str | None = None,
    limit: int | None = 50,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    prompt_jobs_path: str = PROMPT_JOBS_FILE,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("list_prompt_jobs", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"status": status, "target_agent": target_agent, "limit": limit}
    if not allowed:
        return _log_and_return("list_prompt_jobs", client=client, user=user, params=params, result=_unauthorized_response("list_prompt_jobs", role), changes=[], audit_log_path=audit_log_path)
    result = list_prompt_jobs_parser(path=prompt_jobs_path, status=status, target_agent=target_agent, limit=limit)
    return _log_and_return("list_prompt_jobs", client=client, user=user, params=params, result=result, changes=[], audit_log_path=audit_log_path)


def get_prompt_job_impl(
    job_id: str,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    prompt_jobs_path: str = PROMPT_JOBS_FILE,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("get_prompt_job", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"id": job_id}
    if not allowed:
        return _log_and_return("get_prompt_job", client=client, user=user, params=params, result=_unauthorized_response("get_prompt_job", role), changes=[], audit_log_path=audit_log_path)
    result = get_prompt_job_parser(job_id, path=prompt_jobs_path)
    return _log_and_return("get_prompt_job", client=client, user=user, params=params, result=result, changes=[], audit_log_path=audit_log_path)


def claim_prompt_job_impl(
    job_id: str,
    claimed_by: str,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    prompt_jobs_path: str = PROMPT_JOBS_FILE,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("claim_prompt_job", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"id": job_id, "claimed_by": claimed_by}
    if not allowed:
        return _log_and_return("claim_prompt_job", client=client, user=user, params=params, result=_unauthorized_response("claim_prompt_job", role), changes=[], audit_log_path=audit_log_path)
    result = claim_prompt_job_parser(job_id, claimed_by, path=prompt_jobs_path)
    changes = [f"{prompt_jobs_path}: claimed prompt job {job_id} by {claimed_by}"] if result["found"] else []
    return _log_and_return("claim_prompt_job", client=client, user=user, params=params, result=result, changes=changes, audit_log_path=audit_log_path)


def complete_prompt_job_impl(
    job_id: str,
    claimed_by: str,
    result_summary: str,
    result_artifact: str | None = None,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    prompt_jobs_path: str = PROMPT_JOBS_FILE,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("complete_prompt_job", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"id": job_id, "claimed_by": claimed_by, "result_summary": result_summary, "result_artifact": result_artifact}
    if not allowed:
        return _log_and_return("complete_prompt_job", client=client, user=user, params=params, result=_unauthorized_response("complete_prompt_job", role), changes=[], audit_log_path=audit_log_path)
    result = complete_prompt_job_parser(job_id, claimed_by, result_summary, result_artifact, path=prompt_jobs_path)
    changes = [f"{prompt_jobs_path}: completed prompt job {job_id}"] if result["found"] else []
    return _log_and_return("complete_prompt_job", client=client, user=user, params=params, result=result, changes=changes, audit_log_path=audit_log_path)


def fail_prompt_job_impl(
    job_id: str,
    claimed_by: str,
    error: str,
    result_summary: str | None = None,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    prompt_jobs_path: str = PROMPT_JOBS_FILE,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("fail_prompt_job", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"id": job_id, "claimed_by": claimed_by, "error": error, "result_summary": result_summary}
    if not allowed:
        return _log_and_return("fail_prompt_job", client=client, user=user, params=params, result=_unauthorized_response("fail_prompt_job", role), changes=[], audit_log_path=audit_log_path)
    result = fail_prompt_job_parser(job_id, claimed_by, error, result_summary, path=prompt_jobs_path)
    changes = [f"{prompt_jobs_path}: failed prompt job {job_id}"] if result["found"] else []
    return _log_and_return("fail_prompt_job", client=client, user=user, params=params, result=result, changes=changes, audit_log_path=audit_log_path)


def cancel_prompt_job_impl(
    job_id: str,
    *,
    ctx: Context | None = None,
    authorization: str | None = None,
    prompt_jobs_path: str = PROMPT_JOBS_FILE,
    tokens_path: str = TOKENS_FILE,
    audit_log_path: str = AUDIT_LOG_FILE,
) -> dict[str, Any]:
    allowed, role, _, client, user = _auth_result("cancel_prompt_job", ctx=ctx, authorization=authorization, tokens_path=tokens_path)
    params = {"id": job_id}
    if not allowed:
        return _log_and_return("cancel_prompt_job", client=client, user=user, params=params, result=_unauthorized_response("cancel_prompt_job", role), changes=[], audit_log_path=audit_log_path)
    result = cancel_prompt_job_parser(job_id, path=prompt_jobs_path)
    changes = [f"{prompt_jobs_path}: cancelled prompt job {job_id}"] if result["found"] else []
    return _log_and_return("cancel_prompt_job", client=client, user=user, params=params, result=result, changes=changes, audit_log_path=audit_log_path)


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
def create_prompt_job(
    target_agent: str,
    prompt: str,
    source_client: str | None = None,
    priority: str = "normal",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a private operator prompt job for remote dispatch to a target AI agent."""
    return create_prompt_job_impl(target_agent, prompt, source_client, priority, ctx=ctx)


@mcp.tool()
def list_prompt_jobs(
    status: str | None = None,
    target_agent: str | None = None,
    limit: int | None = 50,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List private operator prompt jobs for remote dispatch and coordination."""
    return list_prompt_jobs_impl(status, target_agent, limit, ctx=ctx)


@mcp.tool()
def get_prompt_job(id: str, ctx: Context | None = None) -> dict[str, Any]:
    """Get one private operator prompt job by id."""
    return get_prompt_job_impl(id, ctx=ctx)


@mcp.tool()
def claim_prompt_job(id: str, claimed_by: str, ctx: Context | None = None) -> dict[str, Any]:
    """Claim a private operator prompt job for a specific worker or client."""
    return claim_prompt_job_impl(id, claimed_by, ctx=ctx)


@mcp.tool()
def complete_prompt_job(
    id: str,
    claimed_by: str,
    result_summary: str,
    result_artifact: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Mark a private operator prompt job as completed with a result summary."""
    return complete_prompt_job_impl(id, claimed_by, result_summary, result_artifact, ctx=ctx)


@mcp.tool()
def fail_prompt_job(
    id: str,
    claimed_by: str,
    error: str,
    result_summary: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Mark a private operator prompt job as failed with an error summary."""
    return fail_prompt_job_impl(id, claimed_by, error, result_summary, ctx=ctx)


@mcp.tool()
def cancel_prompt_job(id: str, ctx: Context | None = None) -> dict[str, Any]:
    """Cancel a private operator prompt job before completion."""
    return cancel_prompt_job_impl(id, ctx=ctx)


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


# ─── MCP TOOLS: Per-user health + shared memory ─────────────────────────────

@mcp.tool()
def get_user_health_summary(user_id: str, days: int = 30) -> str:
    """Get a per-user health data summary from the normalized multi-provider store."""
    path = os.path.join(os.path.dirname(SHARED_MEMORY_FILE), "user_health", f"health_{user_id}.json")
    data = None
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        pass
    if not data or not data.get("records"):
        return json.dumps({"ok": True, "user_id": user_id, "records": 0, "providers": [], "message": "No health data yet for this user."})
    records = data["records"]
    if days > 0:
        cutoff = (datetime.now(timezone.utc) - __import__('datetime').timedelta(days=days)).strftime("%Y-%m-%d")
        records = [r for r in records if (r.get("date") or "") >= cutoff]
    providers = list({r.get("provider") for r in records if r.get("provider")})
    return json.dumps({"ok": True, "user_id": user_id, "records": len(records), "providers": providers, "latest_date": max((r.get("date") or "") for r in records) if records else None})


@mcp.tool()
def get_user_shared_memory(user_id: str) -> str:
    """Get a per-user shared memory store (facts, context, insights, rules, questions)."""
    path = os.path.join(os.path.dirname(SHARED_MEMORY_FILE), "user_memory", f"memory_{user_id}.json")
    data = None
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        pass
    if not data:
        data = {"schema_version": 1, "user_id": user_id, "facts": [], "context": [], "substance_timeline": [], "insights": [], "open_questions": [], "approved_rules": []}
    data["user_id"] = user_id
    return json.dumps({"ok": True, "item": data})


@mcp.tool()
def list_provider_registry() -> str:
    """List all supported health data providers and their field capabilities."""
    return json.dumps({"ok": True, "providers": [
        {"id": "whoop", "name": "WHOOP", "status": "production"},
        {"id": "polar", "name": "Polar", "status": "supported"},
        {"id": "apple_health", "name": "Apple Health", "status": "planned"},
        {"id": "garmin", "name": "Garmin", "status": "planned"},
        {"id": "cronometer", "name": "Cronometer", "status": "planned"},
        {"id": "manual", "name": "Manual", "status": "production"}
    ]})


# ─── HTTP API endpoints for website Control Centre ──────────────────────────
# These serve live state to the browser without requiring MCP protocol.
# CORS enabled so the website can fetch directly.

from starlette.responses import JSONResponse


def _cors_json(data: dict, status_code: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status_code, headers={"Access-Control-Allow-Origin": "*"})


def _read_json_file(path: str) -> dict | None:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


@mcp.custom_route("/api/work-status", methods=["GET", "OPTIONS"], include_in_schema=False)
async def api_work_status(_request) -> JSONResponse:
    """Live work status for all agents — consumed by website Control Centre."""
    data = _read_json_file(WORK_STATUS_FILE)
    if not data:
        return _cors_json({"ok": False, "error": "work_status_not_found"}, 404)
    return _cors_json({"ok": True, "item": data})


def _write_json_file(path: str, data: Any) -> bool:
    try:
        import tempfile
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
        return True
    except Exception:
        return False


@mcp.custom_route("/api/prompt-jobs", methods=["GET", "POST", "OPTIONS"], include_in_schema=False)
async def api_prompt_jobs(request) -> JSONResponse:
    """Live prompt jobs for operator — consumed by website Control Centre."""
    from starlette.responses import Response
    # CORS preflight
    if request.method == "OPTIONS":
        return Response("", headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        })
    # Read jobs
    data = _read_json_file(PROMPT_JOBS_FILE) or {"items": []}
    items = data if isinstance(data, list) else data.get("items", data.get("jobs", []))
    if not isinstance(items, list):
        items = []
    if request.method == "GET":
        return _cors_json({"ok": True, "items": items})
    # POST: create a new prompt job
    try:
        body = await request.json()
    except Exception:
        return _cors_json({"ok": False, "error": "invalid_json"}, 400)
    if body.get("action") != "create":
        return _cors_json({"ok": False, "error": "unsupported_action"}, 400)
    import secrets as _sec
    job = {
        "id": "PJ-" + str(int(datetime.now(timezone.utc).timestamp() * 1000)) + "-" + _sec.token_hex(3),
        "target_agent": body.get("target_agent", "claude_code"),
        "prompt": body.get("prompt", ""),
        "priority": body.get("priority", "normal"),
        "status": "pending",
        "source_client": body.get("source_client", "website-operator"),
        "claimed_by": None,
        "result_summary": None,
        "result_artifact": None,
        "error": None,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    items.insert(0, job)
    if len(items) > 50:
        items = items[:50]
    _write_json_file(PROMPT_JOBS_FILE, {"items": items})
    return _cors_json({"ok": True, "item": job, "source": "mcp"})


@mcp.custom_route("/api/suggestions", methods=["GET"], include_in_schema=False)
async def api_suggestions(_request) -> JSONResponse:
    """Live suggestion queue — consumed by website Control Centre."""
    data = _read_json_file(AUTOMATION_SUGGESTIONS_PATH)
    if not data:
        return _cors_json({"ok": True, "items": []})
    items = data if isinstance(data, list) else data.get("items", [])
    return _cors_json({"ok": True, "items": items, "count": len(items)})


def _user_memory_path(user_id: str) -> str:
    """Per-user shared memory file. Falls back to global if no user_id."""
    if not user_id or user_id == 'default':
        return SHARED_MEMORY_FILE
    safe_id = "".join(c for c in user_id if c.isalnum() or c in "-_")[:64]
    mem_dir = os.path.join(os.path.dirname(SHARED_MEMORY_FILE), "user_memory")
    os.makedirs(mem_dir, exist_ok=True)
    return os.path.join(mem_dir, f"memory_{safe_id}.json")


def _empty_memory() -> dict:
    return {"schema_version": 1, "updated_at": None, "user_id": None,
            "facts": [], "context": [], "substance_timeline": [],
            "insights": [], "open_questions": [], "approved_rules": []}


@mcp.custom_route("/api/shared-memory", methods=["GET", "POST", "OPTIONS"], include_in_schema=False)
async def api_shared_memory(request) -> JSONResponse:
    """Per-user structured memory — read/write for CC, ChatGPT, Claude."""
    from starlette.responses import Response
    if request.method == "OPTIONS":
        return Response("", headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        })
    if request.method == "GET":
        user_id = request.query_params.get("user_id", "default")
        path = _user_memory_path(user_id)
        data = _read_json_file(path) or _empty_memory()
        data["user_id"] = user_id
        return _cors_json({"ok": True, "item": data, "user_id": user_id})
    # POST: save per-user store (auth + user_id required for writes)
    caller_uid, caller_role, _ = authenticate_request(request)
    if not caller_uid:
        return _cors_json({"ok": False, "error": "auth_required"}, 401)
    try:
        body = await request.json()
    except Exception:
        return _cors_json({"ok": False, "error": "invalid_json"}, 400)
    user_id = body.get("user_id")
    if not user_id or user_id == "default":
        return _cors_json({"ok": False, "error": "user_id required for writes"}, 400)
    if not can_access_user(caller_uid, caller_role, user_id):
        return _cors_json({"ok": False, "error": "forbidden"}, 403)
    item = body.get("item")
    if not item:
        return _cors_json({"ok": False, "error": "missing item"}, 400)
    item["updated_at"] = _now_iso()
    item["user_id"] = user_id
    path = _user_memory_path(user_id)
    _write_json_file(path, item)
    return _cors_json({"ok": True, "saved": True, "user_id": user_id})


def _user_health_path(user_id: str) -> str:
    """Per-user health data file."""
    safe_id = "".join(c for c in (user_id or "default") if c.isalnum() or c in "-_")[:64]
    health_dir = os.path.join(os.path.dirname(SHARED_MEMORY_FILE), "user_health")
    os.makedirs(health_dir, exist_ok=True)
    return os.path.join(health_dir, f"health_{safe_id}.json")


@mcp.custom_route("/api/user-health", methods=["GET", "POST", "OPTIONS"], include_in_schema=False)
async def api_user_health(request) -> JSONResponse:
    """Per-user health data — normalized daily records from any provider."""
    from starlette.responses import Response
    if request.method == "OPTIONS":
        return Response("", headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        })
    user_id = request.query_params.get("user_id", "default")
    path = _user_health_path(user_id)
    if request.method == "GET":
        data = _read_json_file(path) or {"user_id": user_id, "records": [], "providers": []}
        data["user_id"] = user_id
        return _cors_json({"ok": True, "item": data, "user_id": user_id})
    # POST: append or replace health records (auth + ownership enforced)
    caller_uid, caller_role, _ = authenticate_request(request)
    if not caller_uid:
        return _cors_json({"ok": False, "error": "auth_required"}, 401)
    try:
        body = await request.json()
    except Exception:
        return _cors_json({"ok": False, "error": "invalid_json"}, 400)
    uid = body.get("user_id") or user_id
    if not uid or uid == "default":
        return _cors_json({"ok": False, "error": "user_id required for writes"}, 400)
    if not can_access_user(caller_uid, caller_role, uid):
        return _cors_json({"ok": False, "error": "forbidden"}, 403)
    action = body.get("action", "append")
    records = body.get("records", [])
    existing = _read_json_file(_user_health_path(uid)) or {"user_id": uid, "records": [], "providers": []}
    if action == "replace":
        existing["records"] = records
    else:
        # Append, deduplicating by date+provider
        existing_keys = {(r.get("date"), r.get("provider")) for r in existing["records"]}
        for r in records:
            r["user_id"] = uid
            key = (r.get("date"), r.get("provider"))
            if key not in existing_keys:
                existing["records"].append(r)
                existing_keys.add(key)
            else:
                # Update existing record
                for i, er in enumerate(existing["records"]):
                    if (er.get("date"), er.get("provider")) == key:
                        existing["records"][i] = r
                        break
    # Track providers
    providers = list({r.get("provider") for r in existing["records"] if r.get("provider")})
    existing["providers"] = providers
    existing["user_id"] = uid
    existing["updated_at"] = _now_iso()
    _write_json_file(_user_health_path(uid), existing)
    return _cors_json({"ok": True, "user_id": uid, "record_count": len(existing["records"]), "providers": providers})


@mcp.custom_route("/api/providers", methods=["GET"], include_in_schema=False)
async def api_providers(_request) -> JSONResponse:
    """Registry of supported health data providers."""
    return _cors_json({"ok": True, "providers": [
        {"id": "whoop", "name": "WHOOP", "status": "production", "fields": ["recovery","hrv","resting_hr","sleep_detail","strain","spo2","skin_temp","workouts","hr_zones"]},
        {"id": "polar", "name": "Polar", "status": "supported", "fields": ["nightly_recharge","hrv","resting_hr","sleep_stages","training_load","workouts","steps"]},
        {"id": "apple_health", "name": "Apple Health", "status": "planned", "fields": ["hrv","resting_hr","sleep","active_energy","steps","spo2","weight","workouts"]},
        {"id": "garmin", "name": "Garmin", "status": "planned", "fields": ["hrv","resting_hr","sleep","body_battery","stress","steps","spo2","workouts"]},
        {"id": "cronometer", "name": "Cronometer", "status": "planned", "fields": ["nutrition"]},
        {"id": "manual", "name": "Manual", "status": "production", "fields": ["subjective","grappling_session","substances","nutrition","weight"]}
    ]})


@mcp.custom_route("/api/ingest/polar", methods=["POST", "OPTIONS"], include_in_schema=False)
async def api_ingest_polar(request) -> JSONResponse:
    """Ingest Polar health data for a specific user. Requires auth. Enforces user ownership."""
    from starlette.responses import Response
    if request.method == "OPTIONS":
        return Response("", headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        })
    # Auth required
    caller_uid, caller_role, token_info = authenticate_request(request)
    if not caller_uid:
        return _cors_json({"ok": False, "error": "auth_required", "detail": "Bearer token required"}, 401)
    try:
        body = await request.json()
    except Exception:
        return _cors_json({"ok": False, "error": "invalid_json"}, 400)
    user_id = body.get("user_id")
    if not user_id:
        return _cors_json({"ok": False, "error": "user_id required"}, 400)
    if not can_access_user(caller_uid, caller_role, user_id):
        return _cors_json({"ok": False, "error": "forbidden", "detail": "You can only ingest data for your own user_id"}, 403)
    raw_records = body.get("records", body.get("days", []))
    if not raw_records:
        return _cors_json({"ok": False, "error": "no records provided"}, 400)
    # Normalize each Polar record into the standard schema
    normalized = []
    for raw in raw_records:
        rec = _normalize_polar_record(raw, user_id)
        if rec:
            normalized.append(rec)
    if not normalized:
        return _cors_json({"ok": False, "error": "no valid records after normalization"}, 400)
    # Write to per-user health store
    path = _user_health_path(user_id)
    existing = _read_json_file(path) or {"user_id": user_id, "records": [], "providers": []}
    existing_keys = {(r.get("date"), r.get("provider")) for r in existing["records"]}
    added = 0
    updated = 0
    for rec in normalized:
        key = (rec.get("date"), rec.get("provider"))
        if key in existing_keys:
            for i, er in enumerate(existing["records"]):
                if (er.get("date"), er.get("provider")) == key:
                    existing["records"][i] = rec
                    updated += 1
                    break
        else:
            existing["records"].append(rec)
            existing_keys.add(key)
            added += 1
    existing["providers"] = list({r.get("provider") for r in existing["records"] if r.get("provider")})
    existing["user_id"] = user_id
    existing["updated_at"] = _now_iso()
    _write_json_file(path, existing)
    return _cors_json({
        "ok": True,
        "user_id": user_id,
        "added": added,
        "updated": updated,
        "total_records": len(existing["records"]),
        "providers": existing["providers"]
    })


def _normalize_polar_record(raw: dict, user_id: str) -> dict | None:
    """Normalize a Polar record into the standard health schema."""
    date = raw.get("date") or raw.get("local_date")
    if not date:
        return None
    # Polar Nightly Recharge: ANS charge -5 to +5 → normalized 0-100
    ans = raw.get("ans_charge")
    recovery = round(((ans + 5) / 10) * 100) if ans is not None else None
    recharge = raw.get("nightly_recharge_status", "")
    readiness = "unknown"
    if recharge in ("good", "very_good"):
        readiness = "high"
    elif recharge in ("ok", "compromised"):
        readiness = "moderate"
    elif recharge in ("poor", "very_poor"):
        readiness = "low"
    elif recovery is not None:
        readiness = "high" if recovery >= 67 else "moderate" if recovery >= 34 else "low"
    # Sleep: Polar reports in ms
    sleep_ms = raw.get("sleep_duration_ms")
    sleep_h = sleep_ms / 3600000 if sleep_ms else raw.get("sleep_duration_hours") or raw.get("sleep_hours")
    deep_ms = raw.get("deep_sleep_ms")
    rem_ms = raw.get("rem_sleep_ms")
    return {
        "user_id": user_id,
        "date": date,
        "provider": "polar",
        "recovery_score": recovery,
        "readiness_label": readiness,
        "hrv_ms": raw.get("hrv_rmssd") or raw.get("hrv_ms") or raw.get("hrv"),
        "resting_hr": raw.get("resting_heart_rate") or raw.get("sleeping_hr") or raw.get("resting_hr"),
        "sleep_hours": round(sleep_h, 2) if sleep_h else None,
        "sleep_performance_pct": raw.get("sleep_score") or raw.get("sleep_performance_pct"),
        "sws_hours": round(deep_ms / 3600000, 2) if deep_ms else None,
        "rem_hours": round(rem_ms / 3600000, 2) if rem_ms else None,
        "respiratory_rate": raw.get("breathing_rate") or raw.get("respiratory_rate"),
        "daily_strain": raw.get("training_load") or raw.get("cardio_load") or raw.get("daily_strain"),
        "active_calories": raw.get("active_calories"),
        "step_count": raw.get("steps") or raw.get("step_count"),
        "workouts": _normalize_polar_workouts(raw.get("exercises") or raw.get("workouts") or []),
        "data_source": "polar_import",
        "imported_at": _now_iso()
    }


def _normalize_polar_workouts(exercises: list) -> list:
    result = []
    for w in exercises:
        sport = (w.get("sport") or w.get("detailed_sport_info") or "").lower()
        dur_ms = w.get("duration_ms")
        result.append({
            "type": w.get("sport_id") or w.get("sport"),
            "sport_label": w.get("sport") or w.get("detailed_sport_info"),
            "duration_min": round(dur_ms / 60000) if dur_ms else w.get("duration_minutes"),
            "strain": w.get("training_load"),
            "avg_hr": w.get("average_heart_rate") or w.get("avg_hr"),
            "max_hr": w.get("max_heart_rate") or w.get("max_hr"),
            "calories": w.get("calories"),
            "is_grappling": any(k in sport for k in ("martial", "wrestling", "bjj", "jiu", "grappling"))
        })
    return result


@mcp.custom_route("/api/healthz", methods=["GET"], include_in_schema=False)
async def api_healthz(_request) -> JSONResponse:
    """Health check for website to verify MCP is reachable."""
    return _cors_json({"ok": True, "service": "GrapplingMap MCP", "ts": _now_iso()})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
