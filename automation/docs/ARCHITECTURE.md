# 4-AI Audit System v2 — Architecture

## Overview

A repeating audit → merge → approve → implement → verify → converge loop with 4 AI agents and a human approval gate.

```
AUDIT (3 agents parallel)
  Claude Chat → UX/product findings
  Cowork → UI/browser findings
  Code → Technical findings
  Each writes: state/audits/<agent>_loop_NNN.md
         ↓
MERGE (ChatGPT)
  Deduplicates, classifies, builds approved batch
  Writes: state/merged/merged_loop_NNN.md
          state/batches/approved_batch_loop_NNN.json
  Updates: state/issues.json
         ↓
HUMAN APPROVAL (Aaron)
  Reviews batch, edits if needed
  Sets human_approved=true in AUDIT_STATE.json
         ↓
IMPLEMENT (Code only)
  Implements approved items
  Writes: state/implementation/impl_loop_NNN.json
  Commits + pushes
         ↓
VERIFY (all 4 agents)
  Each verifies the batch
  Writes: state/verification/<agent>_loop_NNN.md
         ↓
CONVERGE (ChatGPT)
  Decides if loop is complete or needs another iteration
  If converged → done
  If not → new loop with failed/new items
```

## Folder Structure

```
~/Chat-gpt/automation/
├── prompts/                    # Standard prompts for each agent/phase
│   ├── claude_chat_ux.md
│   ├── cowork_ui.md
│   ├── code_technical.md
│   ├── chatgpt_merge.md
│   ├── code_implement.md
│   ├── verify_all.md
│   └── converge_chatgpt.md
├── state/                      # All state and data files
│   ├── AUDIT_STATE.json        # Current loop state machine
│   ├── issues.json             # Persistent issue tracker
│   ├── audits/                 # Per-agent per-loop audit files
│   ├── merged/                 # ChatGPT merged findings
│   ├── batches/                # Approved implementation batches
│   ├── implementation/         # Code implementation results
│   └── verification/           # Per-agent verification results
├── scripts/                    # Orchestration scripts
│   ├── init_cycle.sh           # Start a new loop
│   ├── check_state.sh          # Show current state
│   └── orchestrate.py          # State machine + commands
└── docs/
    └── ARCHITECTURE.md         # This file
```

## Issue ID Format

`<AGENT>-L<LOOP>-<SEQ>`

- `CC-L001-001` — Claude Chat, loop 1, finding 1
- `CW-L001-001` — Cowork
- `CODE-L001-001` — Code
- `GPT-L001-001` — ChatGPT (during merge/verify)

## Issue Lifecycle

```
new → approved → implemented → verified → DONE
  ↓        ↓           ↓
rejected  deferred    failed → reopened (new loop)
```

Fields:
- id, status, title, detail, severity, category
- sources (array of contributing agent IDs)
- area (feature/page affected)
- loop_found, loop_last_touched
- reopened_from (original ID if reopened)
- action (implementation instruction)

## Surface Coverage Matrix

Every audit must report which surfaces were tested:

| Surface | Values |
|---------|--------|
| guest | tested / untested |
| logged-in | tested / untested |
| desktop | tested / untested |
| mobile-web | tested / untested |
| iOS Safari | tested / untested |
| Android Chrome | tested / untested |
| macOS | tested / untested |
| Windows | tested / untested |
| Linux | tested / untested |

## Convergence Rules

**Converged** when:
- All approved batch items: Code = pass
- Cowork: user-facing behavior materially correct
- Claude Chat: materially resolved
- ChatGPT: no reopening required
- Minor disagreements do NOT block closure

**Not converged** when:
- Regressions found
- Tests fail
- New critical/high issues introduced

## Human Approval Gate

The system STOPS after ChatGPT produces the merged/approved batch.
Aaron must review and approve before implementation begins.
`orchestrate.py approve` sets the flag and advances to implement phase.

## Commands

```bash
# Start a new loop
bash scripts/init_cycle.sh

# Check current state
bash scripts/check_state.sh

# Orchestrator
python3 scripts/orchestrate.py status   # show status
python3 scripts/orchestrate.py advance  # try to advance phase
python3 scripts/orchestrate.py approve  # Aaron approves batch
```
