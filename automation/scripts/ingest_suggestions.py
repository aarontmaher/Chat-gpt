#!/usr/bin/env python3
"""
Ingest approved website suggestions into the 4-AI automation system.
Reads suggestion_handoffs from the website's localStorage export
and creates structured issues in the automation issues.json.
"""

import json
import os
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
ISSUES_FILE = os.path.join(BASE_DIR, "state", "issues.json")
STATE_FILE = os.path.join(BASE_DIR, "state", "AUDIT_STATE.json")
HANDOFF_DIR = os.path.join(BASE_DIR, "state", "suggestion-handoffs")


def load_issues():
    with open(ISSUES_FILE) as f:
        return json.load(f)


def save_issues(data):
    with open(ISSUES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)


def ingest_from_file(filepath):
    """Ingest suggestion handoffs from a JSON file (exported from website)."""
    with open(filepath) as f:
        handoffs = json.load(f)

    if isinstance(handoffs, dict) and "suggestion_handoffs" in handoffs:
        handoffs = handoffs["suggestion_handoffs"]

    if not handoffs:
        print("No handoffs to ingest.")
        return

    issues_data = load_issues()
    state = load_state()
    current_loop = state.get("loop", 0)
    existing_ids = {i["id"] for i in issues_data.get("issues", [])}
    ingested = 0

    for h in handoffs:
        if h.get("automation_status") != "pending_audit":
            continue

        # Generate automation issue ID from suggestion ID
        sug_id = h.get("suggestion_id", "SUG-unknown")
        issue_id = f"WEB-{sug_id}"

        if issue_id in existing_ids:
            print(f"  Skip (already exists): {issue_id}")
            continue

        severity_map = {"high": "high", "medium": "medium", "low": "low"}
        severity = severity_map.get(h.get("severity_guess", ""), "medium")

        issue = {
            "id": issue_id,
            "status": "new",
            "title": h.get("normalized_summary", "Website suggestion"),
            "detail": h.get("original_message", ""),
            "severity": severity,
            "category": h.get("classification", "unclear"),
            "sources": [sug_id],
            "area": h.get("source_page", "unknown"),
            "loop_found": current_loop or 1,
            "loop_last_touched": current_loop or 1,
            "reopened_from": None,
            "action": f"Review and implement: {h.get('normalized_summary', '')}",
            "website_suggestion_id": sug_id,
            "approved_at": h.get("approved_at"),
            "approved_by": h.get("approved_by", "owner"),
        }

        issues_data.setdefault("issues", []).append(issue)
        existing_ids.add(issue_id)
        ingested += 1
        print(f"  Ingested: {issue_id} — {issue['title'][:60]}")

    save_issues(issues_data)
    print(f"\nTotal ingested: {ingested}")
    print(f"Total issues now: {len(issues_data.get('issues', []))}")


def ingest_from_stdin():
    """Read handoffs from stdin (piped from website export)."""
    data = json.load(sys.stdin)
    # Write to temp file and ingest
    os.makedirs(HANDOFF_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(HANDOFF_DIR, f"handoff_{ts}.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved handoff to: {filepath}")
    ingest_from_file(filepath)


def main():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            sys.exit(1)
        ingest_from_file(filepath)
    elif not sys.stdin.isatty():
        ingest_from_stdin()
    else:
        # Check for any unprocessed handoff files
        os.makedirs(HANDOFF_DIR, exist_ok=True)
        files = sorted(f for f in os.listdir(HANDOFF_DIR) if f.endswith(".json"))
        if files:
            print(f"Found {len(files)} handoff file(s):")
            for f in files:
                print(f"  Processing: {f}")
                ingest_from_file(os.path.join(HANDOFF_DIR, f))
        else:
            print("No handoff files found.")
            print("Usage:")
            print("  python3 ingest_suggestions.py <handoff.json>")
            print("  cat handoff.json | python3 ingest_suggestions.py")
            print(f"  Drop files in: {HANDOFF_DIR}/")


if __name__ == "__main__":
    main()
