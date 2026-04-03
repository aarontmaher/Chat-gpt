# 4-AI Audit System — Architecture

## Overview

A repeating audit → approve → implement → verify loop where 4 AI agents collaboratively improve the GrapplingMap website.

```
┌──────────────────────────────────────────────────┐
│                  AUDIT PHASE                      │
│  Cowork → UI/UX findings                         │
│  Claude Chat → Product/UX reasoning              │
│  Code → Technical audit                          │
│  All write to: audit-inbox/                      │
└──────────────┬───────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────┐
│                 MERGE PHASE                       │
│  ChatGPT reads all audit-inbox/ files            │
│  Deduplicates, classifies, prioritizes           │
│  Writes: batch.json (approved items)             │
└──────────────┬───────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────┐
│              IMPLEMENT PHASE                      │
│  Code reads batch.json                           │
│  Implements only approved items                  │
│  Writes: batch-result.json                       │
│  Commits + pushes                                │
└──────────────┬───────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────┐
│               VERIFY PHASE                        │
│  All 4 agents verify the batch                   │
│  Each writes to: verify-inbox/                   │
│  ChatGPT reads all, determines convergence       │
│  If not converged → new audit cycle              │
└──────────────┬───────────────────────────────────┘
               ▼
        Converged? ──No──→ Back to AUDIT
               │
              Yes
               ▼
         Batch complete
```

## Folder Structure

```
~/Chat-gpt/audit-system/
├── ARCHITECTURE.md          # This file
├── STATE.json               # Current cycle state
├── audit-inbox/             # Raw findings from each agent
│   ├── cowork.json
│   ├── claude-chat.json
│   └── code.json
├── batch.json               # ChatGPT-approved implementation batch
├── batch-result.json        # Code's implementation results
├── verify-inbox/            # Post-implementation verification
│   ├── cowork.json
│   ├── claude-chat.json
│   ├── code.json
│   └── chatgpt.json
├── history/                 # Archived completed cycles
│   ├── cycle-001/
│   ├── cycle-002/
│   └── ...
└── prompts/                 # Standard prompts for each agent
    ├── audit-cowork.md
    ├── audit-chat.md
    ├── audit-code.md
    ├── merge-chatgpt.md
    ├── implement-code.md
    ├── verify-all.md
    └── converge-chatgpt.md
```

## State Model (STATE.json)

```json
{
  "cycle": 1,
  "phase": "audit|merge|implement|verify|converged",
  "started_at": "2026-04-03T00:00:00Z",
  "updated_at": "2026-04-03T00:00:00Z",
  "audit_complete": {
    "cowork": false,
    "claude_chat": false,
    "code": false
  },
  "batch_approved": false,
  "batch_implemented": false,
  "verify_complete": {
    "cowork": false,
    "claude_chat": false,
    "code": false,
    "chatgpt": false
  },
  "converged": false,
  "batch_item_count": 0,
  "items_fixed": 0,
  "items_remaining": 0
}
```

## Agent Roles

### Cowork (Browser Audit)
- **Input**: Live website URL
- **Method**: Visual inspection, click-through, screenshot
- **Finds**: Broken UI, layout issues, mobile problems, missing content, dead links, confusing UX
- **Output**: `audit-inbox/cowork.json`
- **Cannot**: Read code, edit files, run tests

### Claude Chat (Product/UX Reasoning)
- **Input**: Live website URL (read-only monitoring), prior audit findings
- **Method**: Product thinking, UX analysis, user journey evaluation
- **Finds**: Flow problems, value prop gaps, onboarding issues, conversion friction, information architecture
- **Output**: `audit-inbox/claude-chat.json`
- **Cannot**: Edit code, click UI, make changes

### Code (Technical Audit + Implementation)
- **Input**: Repository files, Playwright tests, live URL
- **Method**: Code inspection, test execution, performance analysis, security review
- **Finds**: Bugs, dead code, performance issues, accessibility gaps, test failures, state inconsistencies
- **Output**: `audit-inbox/code.json` (audit phase), `batch-result.json` (implement phase)
- **Is**: The ONLY agent that implements changes

### ChatGPT (Decision/Merge Layer)
- **Input**: All audit-inbox/ files, batch-result.json, verify-inbox/ files
- **Method**: Cross-reference findings, deduplicate, classify, prioritize, approve
- **Output**: `batch.json` (approved items), convergence decision
- **Cannot**: Edit code, access live site, run tests

## Data Formats

### Audit Finding (audit-inbox/*.json)

```json
{
  "agent": "cowork|claude-chat|code",
  "cycle": 1,
  "timestamp": "2026-04-03T00:00:00Z",
  "findings": [
    {
      "id": "CW-001",
      "title": "Short description",
      "detail": "Full explanation",
      "severity": "critical|high|medium|low",
      "category": "bug|ux|performance|accessibility|content|trust|conversion",
      "page": "/products/mens-rashguard-black",
      "evidence": "screenshot URL or code reference",
      "suggested_fix": "What should change",
      "effort": "easy|medium|large",
      "confidence": "high|medium|low"
    }
  ]
}
```

### Approved Batch (batch.json)

```json
{
  "cycle": 1,
  "approved_by": "chatgpt",
  "approved_at": "2026-04-03T00:00:00Z",
  "items": [
    {
      "id": "BATCH-001-01",
      "source_ids": ["CW-001", "CC-003"],
      "title": "Fix X",
      "action": "Exact implementation instruction",
      "classification": "do_now|do_later|do_not_do|needs_safer_version",
      "priority": 1,
      "files_likely": ["index.html"],
      "risk": "low|medium|high"
    }
  ],
  "deferred": [
    {
      "id": "DEF-001",
      "source_ids": ["CW-002"],
      "reason": "Needs Aaron input"
    }
  ],
  "rejected": [
    {
      "id": "REJ-001",
      "source_ids": ["CC-001"],
      "reason": "Generic fluff, low business value"
    }
  ]
}
```

### Batch Result (batch-result.json)

```json
{
  "cycle": 1,
  "implemented_by": "code",
  "implemented_at": "2026-04-03T00:00:00Z",
  "commit": "abc1234",
  "tests_before": "23/23",
  "tests_after": "23/23",
  "items": [
    {
      "id": "BATCH-001-01",
      "status": "done|blocked|skipped",
      "detail": "What was changed",
      "files_changed": ["index.html:1234"],
      "blocker": null
    }
  ]
}
```

### Verification (verify-inbox/*.json)

```json
{
  "agent": "cowork|claude-chat|code|chatgpt",
  "cycle": 1,
  "timestamp": "2026-04-03T00:00:00Z",
  "batch_items_verified": [
    {
      "id": "BATCH-001-01",
      "status": "pass|fail|regression",
      "detail": "Verification notes",
      "new_issues_found": []
    }
  ],
  "overall": "pass|fail",
  "new_findings": []
}
```

## Orchestration

### Phase Transitions

```
STATE.phase transitions:
  "idle" → "audit"      (triggered by: manual start or scheduled)
  "audit" → "merge"     (triggered by: all 3 audit agents complete)
  "merge" → "implement" (triggered by: ChatGPT approves batch)
  "implement" → "verify" (triggered by: Code completes batch)
  "verify" → "converged" (triggered by: all 4 verify + ChatGPT says converged)
  "verify" → "audit"    (triggered by: ChatGPT says NOT converged, new issues found)
  "converged" → "idle"  (triggered by: cycle archived)
```

### Trigger Model

Each agent checks STATE.json to know what phase we're in and whether it's their turn:

1. **Start cycle**: Update STATE.json phase to "audit"
2. **Audit agents**: Each checks if phase="audit" and their audit_complete flag is false
3. **Merge**: ChatGPT checks if all 3 audit_complete flags are true
4. **Implement**: Code checks if batch_approved is true
5. **Verify**: Each agent checks if batch_implemented is true and their verify flag is false
6. **Converge**: ChatGPT checks if all 4 verify flags are true

### Orchestration Options

**Option A: Manual (current)**
Aaron copies prompts between agents manually. Each prompt reads STATE.json.

**Option B: Keyboard Maestro (existing bridge)**
The existing bridge_cycle.sh + mark_done.sh system can be adapted.

**Option C: Script Editor (recommended for next step)**
AppleScript that:
1. Reads STATE.json
2. Determines next action
3. Opens the right app (Claude Code terminal, Claude Chat, Cowork browser)
4. Pastes the right prompt
5. Waits for completion signal (file write)
6. Advances state

### Convergence Logic

ChatGPT determines convergence when:
1. All 4 agents verified the batch
2. No agent found regressions (all "pass")
3. No new critical/high findings
4. New findings (if any) are low priority and can be deferred

If NOT converged:
- New findings become the next cycle's audit-inbox
- STATE.cycle increments
- Loop restarts

## Reuse in Website

The same architecture maps to user-submitted improvements:

```
User submits suggestion → audit-inbox/user.json
AI agents evaluate feasibility → batch.json
Code implements → batch-result.json
Automated tests verify → verify-inbox/
User confirms on live site → converged
```

This requires:
1. A submission form on the website
2. An API endpoint that writes to audit-inbox/
3. A dashboard showing cycle state
4. Notification when implementation is ready to verify

## Getting Started

1. Run `init-cycle.sh` to create a new cycle
2. Give each agent their audit prompt from `prompts/`
3. Each agent writes to `audit-inbox/`
4. Give ChatGPT the merge prompt
5. Give Code the implement prompt
6. Give each agent the verify prompt
7. Give ChatGPT the converge prompt
8. If converged, archive and done. If not, repeat.
