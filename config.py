from __future__ import annotations

import os


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_LOG_FILE = os.path.join(PROJECT_ROOT, "audit_log.jsonl")

AUTOMATION_SUGGESTIONS_FILE = os.path.join(PROJECT_ROOT, "AUTOMATION_SUGGESTIONS.md")
AUTOMATION_SUGGESTIONS_INBOX_FILE = os.path.join(PROJECT_ROOT, "AUTOMATION_SUGGESTIONS_INBOX.md")
AUTOMATION_ACCEPTED_FILE = os.path.join(PROJECT_ROOT, "AUTOMATION_ACCEPTED.md")
AUTOMATION_NOW_FILE = os.path.join(PROJECT_ROOT, "AUTOMATION_NOW.md")
AUTOMATION_NEXT_FILE = os.path.join(PROJECT_ROOT, "AUTOMATION_NEXT.md")
HANDOFF_LATEST_FILE = os.path.join(PROJECT_ROOT, "HANDOFF_LATEST.md")
TOKENS_FILE = os.path.join(PROJECT_ROOT, "tokens.json")
WHOOP_TOKENS_FILE = os.path.expanduser("~/whoop-integration/whoop_tokens.json")
WHOOP_SQLITE_FILE = os.path.expanduser("~/whoop-integration/data/whoop.sqlite3")

PROJECT_AUTOMATION_DIR = os.path.join(PROJECT_ROOT, "automation")
PROJECT_STATE_DIR = os.path.join(PROJECT_AUTOMATION_DIR, "state")
AUDIT_STATE_FILE = os.path.join(PROJECT_STATE_DIR, "AUDIT_STATE.json")
ISSUES_FILE = os.path.join(PROJECT_STATE_DIR, "issues.json")
PROJECT_BATCHES_DIR = os.path.join(PROJECT_STATE_DIR, "batches")
PROJECT_IMPLEMENTATION_DIR = os.path.join(PROJECT_STATE_DIR, "implementation")
PROJECT_HANDOFF_DIR = os.path.join(PROJECT_STATE_DIR, "suggestion-handoffs")
PROJECT_HANDOFF_ARTIFACTS_DIR = os.path.join(PROJECT_STATE_DIR, "handoffs")
PROMPT_JOBS_FILE = os.path.join(PROJECT_STATE_DIR, "PROMPT_JOBS.json")
SHARED_MEMORY_FILE = os.path.join(PROJECT_STATE_DIR, "SHARED_MEMORY.json")

CHATGPT_ROOT = os.path.expanduser("~/Chat-gpt")
CHATGPT_AUTOMATION_DIR = os.path.join(CHATGPT_ROOT, "automation")
PROMPTS_DIR = os.path.join(CHATGPT_AUTOMATION_DIR, "prompts")
STATE_DIR = os.path.join(CHATGPT_AUTOMATION_DIR, "state")
AUDITS_DIR = os.path.join(STATE_DIR, "audits")
MERGED_DIR = os.path.join(STATE_DIR, "merged")
SPEC_BATCHES_DIR = os.path.join(STATE_DIR, "batches")
SPEC_IMPLEMENTATION_DIR = os.path.join(STATE_DIR, "implementation")
VERIFICATION_DIR = os.path.join(STATE_DIR, "verification")
SPEC_AUDIT_STATE_FILE = os.path.join(STATE_DIR, "AUDIT_STATE.json")
SPEC_ISSUES_FILE = os.path.join(STATE_DIR, "issues.json")
WORK_STATUS_FILE = os.path.join(STATE_DIR, "WORK_STATUS.json")
ORCHESTRATE_SCRIPT = os.path.join(CHATGPT_AUTOMATION_DIR, "scripts", "orchestrate.py")

SCHEMA_VERSION = 1

ROUTE_AUTH_RULES = {
    "/api/me/": {"auth_required": True, "auth_type": "bearer", "scope": "private"},
    "/api/aggregate/": {"auth_required": False, "auth_type": "none", "scope": "public"},
    "/api/graph/": {"auth_required": False, "auth_type": "none", "scope": "public"},
    "/api/syllabus/": {"auth_required": False, "auth_type": "none", "scope": "public"},
}

TOOL_TIER_REQUIREMENTS = {
    "list_pending_suggestions": 1,
    "get_suggestion": 1,
    "list_automation_batches": 1,
    "get_automation_state": 1,
    "get_preview_status": 1,
    "get_handoff": 1,
    "get_daily_performance_object": 1,
    "get_work_status": 1,
    "submit_suggestion": 2,
    "approve_suggestion_for_preview": 3,
    "create_handoff_artifact": 3,
    "start_preview_run": 3,
    "advance_phase": 3,
    "update_work_status": 3,
    "create_prompt_job": 3,
    "list_prompt_jobs": 3,
    "get_prompt_job": 3,
    "claim_prompt_job": 3,
    "complete_prompt_job": 3,
    "fail_prompt_job": 3,
    "cancel_prompt_job": 3,
    "approve_batch": 4,
}

AUTOMATION_SUGGESTIONS_PATH = AUTOMATION_SUGGESTIONS_FILE
AUTOMATION_SUGGESTIONS_INBOX_PATH = AUTOMATION_SUGGESTIONS_INBOX_FILE
AUTOMATION_ACCEPTED_PATH = AUTOMATION_ACCEPTED_FILE
AUTOMATION_NOW_PATH = AUTOMATION_NOW_FILE
AUTOMATION_NEXT_PATH = AUTOMATION_NEXT_FILE
HANDOFF_LATEST_PATH = HANDOFF_LATEST_FILE
AUDIT_STATE_PATH = AUDIT_STATE_FILE
BATCHES_DIR = PROJECT_BATCHES_DIR
IMPLEMENTATION_RESULTS_DIR = PROJECT_IMPLEMENTATION_DIR


def get_route_auth(path: str) -> dict[str, object]:
    normalized = path if path.startswith("/") else f"/{path}"
    for prefix, rule in ROUTE_AUTH_RULES.items():
        if normalized.startswith(prefix):
            return {"path": normalized, **rule}
    return {
        "path": normalized,
        "auth_required": False,
        "auth_type": "unknown",
        "scope": "unknown",
    }


def get_tool_tier(tool_name: str) -> int | None:
    return TOOL_TIER_REQUIREMENTS.get(tool_name)
