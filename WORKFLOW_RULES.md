# WORKFLOW RULES
Last updated: 2026-03-23

## Role Split (Non-negotiable)
| Role | Responsibility |
|------|---------------|
| Claude Chat | Content planning, prompt review, naming/schema decisions, second-opinion reasoning, shared memory update drafting. NOT for site checking, terminal reading, implementation verification, visual UX verification, or repeated repo-state auditing. Read-only monitoring. No state-changing clicks. No JS. |
| Cowork | RETIRED. Patch system replaces structural work. |
| Code | Repo/website implementer. Edits, commits, pushes. Plain English paste-backs. |
| Aaron | All decisions + all technique names + all OT context labels. |
| ChatGPT | OPML analysis, prompt QA, technical advice. No direct edits. |

## Default Priority Order
1. Website/app improvements (mobile UX, search, video, polish)
2. Mobile UX improvements
3. Automation/workflow improvements
4. Live-footage understanding improvements
5. Content filling (only when Aaron is actively supplying content)

Content filling is input-limited — do not default to it as the top priority.

## Code Paste-back Format
Every paste-back must include:
- What changed (one sentence, no jargon)
- What decisions Aaron needs to make (simple questions only)
- What to check on the live site (one action)

## OPML Workflow
- Source of truth: ~/Chat-gpt/grappling.opml
- Changes: Aaron tells Chat → Chat writes OPML-PATCH → Code edits grappling.opml → pipeline → site updates
- No manual edits except via Code patch prompts
- Mindomo is viewer only, NOT editor

## Live Footage Workflow
1. Drop videos into ~/GrapplingMap/live-footage/INBOX/
2. Tell Code the sequence (or say "review inbox" for assisted placement)
3. Code proposes folder path based on sequence + classification memory
4. Aaron approves/corrects
5. Code moves video, logs result to video-classification-memory.json

## Video Placement
- If chain is short and clear → one best folder
- If chain is long with multiple retrieval points → copy to 2-3 key folders
- Never spray everywhere
- If ambiguous → ask

## Folder Naming
- Key branch points only (sub-position, approach, finish)
- Collapse narrative/transitional descriptions
- When simplifying paths, always move files in same operation
- Remove old empty paths after successful moves

## Automation
- Keyboard Maestro is the active automation system
- Do not introduce a separate replacement automation loop unless Aaron explicitly chooses one

## Website / App Improvement Guardrails
- Do not touch grappling.opml
- Do not alter taxonomy or content structure
- Do not modify live-footage folder organization
- Only safe frontend/product improvements (mobile UX, search, video, polish, accessibility)
- No broad refactors
- Validate with Playwright (npm run check) after changes
- One batch per iteration, stop and report

## Shared Memory
- Read shared memory files at start of every task
- Re-check before significant edits, destructive actions, or final reports
- File roles:
  - HANDOFF_LATEST.md: primary live state for next actions
  - PROJECT_STATE.md: concise current state
  - DECISIONS.md: stable locked rules only
  - WORKFLOW_RULES.md: stable process rules only
  - MEMORY_UPDATES.md: append-only history
  - SYSTEM_OPTIMIZATION.md: background reference

## Shared Memory Sync Timing
Only prompt upload when the automation cycle has reached a TRUE STOPPING POINT:
- No more worthwhile improvement left in scope
- OR the next step requires Aaron's input/decision
- OR the loop has genuinely run out of clear next-best actions

At a true stopping point: validate → update memory files → refresh zips → commit → push → THEN say "UPLOAD TO CHATGPT" → auto-open Finder. Never prompt upload before commit/push.

Do NOT prompt upload:
- At the end of ordinary intermediate batches
- Just because one iteration finished
- While there is a clear next-best worthwhile batch to continue with

Decision rule: if there is a clear next-best improvement in scope, the cycle is NOT finished.

At end of a normal batch (stopping-point: no):
1. Print result line
2. Do NOT prompt upload or open Finder
3. Append exactly one machine-friendly block:

NEXT_AUTOMATION_PROMPT_START
<prompt text only, no explanation, no duplicate signatures>
NEXT_AUTOMATION_PROMPT_END

No extra commentary after the END marker. No second copy of the prompt.

At a true stopping point (stopping-point: yes):
1. Validate → update memory → refresh zips → commit → push → prompt upload → open Finder
2. Do NOT output NEXT_AUTOMATION_PROMPT markers unless explicitly useful.

Keyboard Maestro captures prompts by matching NEXT_AUTOMATION_PROMPT_START through NEXT_AUTOMATION_PROMPT_END.

## Manual vs Automated Task Priority
- **Manual/ad hoc tasks from Aaron** (video moves, folder fixes, verifications, memory corrections, direct filesystem actions) → run immediately, even if an automation loop is active.
- **Automated tasks** (website iteration prompts, KM batch continuations) → defer to queue when interrupted by a manual task.

When a manual task interrupts an active automation loop:
1. Preserve the next automation prompt
2. Run the manual task now
3. After completion, re-output the saved automation prompt in KM-friendly format (NEXT_AUTOMATION_PROMPT_START/END)

Do not discard the queued automation. Do not mix manual results into automation result lines.

## Upload Convenience
- Zip bundles → open ~/Chat-gpt/shared-memory-upload/
- Direct repo-root files → open ~/Chat-gpt/
- Prefer the narrowest useful folder. Do not open extra unrelated folders.
