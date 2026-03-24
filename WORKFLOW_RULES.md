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

## Automation Bridge (LOCKED — old KM bridge only)

Active system: old Keyboard Maestro bridge. No other automation flow.

**Non-stopping batch (continuation):**
1. Code runs: `bash ~/.handoff/continue_automation.sh "RESULT" --prompt "next prompt"`
2. Script writes prompt to `last_chatgpt_reply.txt` FIRST
3. Script handles stale `run.lock` (waits, force-clears if >60s old)
4. Script calls `mark_done.sh` ONLY after prompt is confirmed written
5. If prompt write fails, done is NOT signaled
6. KM DETECT-CODE-DONE gate: `last_code_result.txt` contains "DONE" AND no `run.lock`
7. KM runs `bridge_cycle.sh` → pastes prompt into Terminal
8. No memory upload. No Finder open. Loop continues.

**True stopping point:**
1. Code calls `mark_done.sh "RESULT LINE"` — no continuation prompt written
2. Only then: commit/push + shared memory sync/upload if appropriate
3. Loop stops.

**Retired (do not use):**
- next_automation_prompt.txt
- .prompt_ready flag
- watch-automation.sh launchd watcher
- NEXT_AUTOMATION_PROMPT_START/END stdout markers as the delivery mechanism

**Rules:**
- Shared memory does not interrupt the automation mid-cycle
- Prompts stay plain text, KM-friendly
- Do not reintroduce watcher-based handoff

## Suggestion Decision Model

Code = technical gatekeeper. Aaron = final owner. ChatGPT/Claude Chat = optional product review.

**Code should decide:**
- Is this technically safe?
- Is this in scope?
- Is this blocked by current code state?
- Is this low-risk / high-value?
- Is this already done or duplicated?
- Does it conflict with locked rules?

**Code should NOT alone decide:**
- Whether a suggestion is actually good product-wise
- Whether it fits Aaron's long-term direction
- Whether it should outrank more important UX/system work

**Code may reject:** unsafe, duplicate, out of scope, clearly low value, conflicting with locked rules.

**Code may NOT auto-approve:** all remaining suggestions as ready to implement.

**Flow:**
1. Suggestions go into AUTOMATION_SUGGESTIONS.md (raw pool)
2. Code screens and ranks into AUTOMATION_ACCEPTED.md (approved items)
3. Current batch moves to AUTOMATION_NOW.md (active work)
4. Next batch stays organized in AUTOMATION_NEXT.md (prepared queue)
5. While implementing NOW, Code also keeps NEXT organized
6. At batch end: report NOW results + confirm NEXT is ready
7. If not obvious → defer for Aaron or ChatGPT/Claude Chat review

## Suggestion Restart on Repo Update
After meaningful repo updates, Code sets `suggestion_pass_needed: yes` in AUTOMATION_SUGGESTIONS_TRIGGER.md.

**Practical flow:**
1. Code writes the trigger after commit/push at true stopping points
2. Claude Chat and/or Cowork check the trigger at their next session start
3. They write suggestions to AUTOMATION_SUGGESTIONS_INBOX.md (source-labeled)
4. Code ingests inbox into AUTOMATION_SUGGESTIONS.md / AUTOMATION_NEXT.md on next review pass
5. Trigger is reset to `suggestion_pass_needed: no`

**Direct Cowork → Claude Chat triggering: NOT possible** in the current setup. No automation bridge exists between Cowork and Claude Chat sessions. Cross-agent triggering requires Aaron to manually start sessions or check the trigger. The practical version is file-based coordination — each agent checks the trigger at session start.

## Multi-Lane Automation (LOCKED)
Do not sit idle if one lane pauses or blocks. Immediately switch to the next approved lane.

**Lanes:** syllabus, product/website, accounts/access, suggestion/review, live-footage

**Rule:**
- If current lane is unblocked and worthwhile → continue it
- If current lane is blocked (needs Aaron, waiting on credentials, external check) → immediately move to next approved lane
- Only stop if ALL approved lanes are blocked or at a true stopping point
- At batch end: state what lane ran, whether it's active/blocked/done, what's next

**Do not:** wait idly, invent approval for blocked items, do tiny filler work

## Manual vs Automated Task Priority
- **Manual/ad hoc tasks from Aaron** (video moves, folder fixes, verifications, memory corrections, direct filesystem actions) → run immediately, even if an automation loop is active.
- **Automated tasks** (website iteration prompts, KM batch continuations) → defer to queue when interrupted by a manual task.

When a manual task interrupts an active automation loop:
1. Preserve the next automation prompt
2. Run the manual task now
3. After completion, write the saved automation prompt via `continue_automation.sh`

Do not discard the queued automation. Do not mix manual results into automation result lines.

## Upload Convenience
- Zip bundles → open ~/Chat-gpt/shared-memory-upload/
- Direct repo-root files → open ~/Chat-gpt/
- Prefer the narrowest useful folder. Do not open extra unrelated folders.
