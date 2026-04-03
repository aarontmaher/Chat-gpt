#!/usr/bin/env python3
"""
Orchestration skeleton for the 4-AI audit system.
Reads AUDIT_STATE.json, determines next action, and prints instructions.

Future: can be extended to trigger agents programmatically.
"""

import json
import os
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
STATE_FILE = os.path.join(BASE_DIR, "state", "AUDIT_STATE.json")
ISSUES_FILE = os.path.join(BASE_DIR, "state", "issues.json")


def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_issues():
    with open(ISSUES_FILE) as f:
        return json.load(f)


def save_issues(issues):
    with open(ISSUES_FILE, "w") as f:
        json.dump(issues, f, indent=2)


def check_phase_transition(state):
    """Check if current phase can advance and return the next phase."""
    phase = state["phase"]

    if phase == "audit":
        all_done = all(v["complete"] for v in state["audit_status"].values())
        if all_done:
            return "merge"

    elif phase == "merge":
        if state["merge_status"]["chatgpt"]["complete"]:
            return "awaiting_approval"

    elif phase == "awaiting_approval":
        if state["human_approved"]:
            return "implement"

    elif phase == "implement":
        if state["implementation_status"]["complete"]:
            return "verify"

    elif phase == "verify":
        all_done = all(v["complete"] for v in state["verification_status"].values())
        if all_done:
            return "converge"

    return None  # no transition


def advance(state):
    """Try to advance the phase. Returns True if advanced."""
    next_phase = check_phase_transition(state)
    if next_phase:
        old = state["phase"]
        state["phase"] = next_phase
        save_state(state)
        print(f"Phase advanced: {old} → {next_phase}")
        return True
    return False


def status_report(state):
    """Print current status and next action."""
    loop = state["loop"]
    phase = state["phase"]
    print(f"Loop {loop} | Phase: {phase}")
    print()

    if phase == "idle":
        print("Action: Run init_cycle.sh to start a new loop")
    elif phase == "audit":
        pending = [k for k, v in state["audit_status"].items() if not v["complete"]]
        print(f"Waiting for audit from: {', '.join(pending)}")
    elif phase == "merge":
        print("Action: Give ChatGPT → prompts/chatgpt_merge.md")
    elif phase == "awaiting_approval":
        print("Action: Aaron reviews and approves the batch")
        batch_file = state["merge_status"]["chatgpt"].get("batch_file")
        if batch_file:
            print(f"Batch file: state/{batch_file}")
    elif phase == "implement":
        print("Action: Give Code → prompts/code_implement.md")
    elif phase == "verify":
        pending = [k for k, v in state["verification_status"].items() if not v["complete"]]
        print(f"Waiting for verification from: {', '.join(pending)}")
    elif phase == "converge":
        print("Action: Give ChatGPT → prompts/converge_chatgpt.md")
    elif phase == "converged":
        conv = state["convergence"]
        if conv["converged"]:
            print("Loop converged! Run init_cycle.sh for next loop.")
        else:
            print(f"NOT converged: {conv.get('reason', 'unknown')}")
            print("Run init_cycle.sh to start the next loop.")


def main():
    state = load_state()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "advance":
            if not advance(state):
                print("Cannot advance — prerequisites not met")
        elif cmd == "approve":
            state["human_approved"] = True
            save_state(state)
            advance(state)
            print("Batch approved by Aaron")
        elif cmd == "status":
            status_report(state)
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: orchestrate.py [status|advance|approve]")
    else:
        status_report(state)
        print()
        advanced = advance(state)
        if not advanced:
            print("(no phase transition available)")


if __name__ == "__main__":
    main()
