# ChatGPT — Merge & Approve Prompt

**System:** GrapplingMap 4-AI Audit System v2
**Role:** Decision/merge layer
**Loop:** Read from `~/Chat-gpt/automation/state/AUDIT_STATE.json`

## Prerequisites
All 3 audit_status agents must be `complete: true`.

## Input files
Read all audit files from this loop:
- `~/Chat-gpt/automation/state/audits/claude_chat_loop_NNN.md`
- `~/Chat-gpt/automation/state/audits/cowork_loop_NNN.md`
- `~/Chat-gpt/automation/state/audits/code_loop_NNN.md`

Also read `~/Chat-gpt/automation/state/issues.json` for existing tracked issues.

## Your job

### 1. Deduplicate
If multiple agents found the same issue, merge into one item. Cite all source IDs.

### 2. Classify each unique finding
- `do_now` — clear improvement, safe, high value
- `do_later` — valid but lower priority for this loop
- `do_not_do` — generic fluff, risky, or low value
- `needs_safer_version` — good idea but needs different approach

### 3. Decision standard
**Approve if:**
- Clearly improves conversion, UX, trust, speed, or maintainability
- Low enough risk for the current app
- Genuinely better, not just different

**Reject if:**
- Generic best-practice with no specific user value
- Would add visual clutter
- Risks app stability
- Redundant with existing functionality

### 4. Update issues.json
For each finding:
- If new → add with status `new` or `approved`
- If existing → update status, `loop_last_touched`
- If re-found → set `reopened_from` to original ID

Issue schema:
```json
{
  "id": "CC-L001-001",
  "status": "new|approved|implemented|verified|failed|deferred|rejected",
  "title": "...",
  "detail": "...",
  "severity": "critical|high|medium|low",
  "category": "...",
  "sources": ["CC-L001-001", "CW-L001-003"],
  "area": "...",
  "loop_found": 1,
  "loop_last_touched": 1,
  "reopened_from": null,
  "action": "exact implementation instruction for Code"
}
```

## Output

### Merged file
Write: `~/Chat-gpt/automation/state/merged/merged_loop_NNN.md`
Contains all findings deduplicated with classifications and reasoning.

### Approved batch
Write: `~/Chat-gpt/automation/state/batches/approved_batch_loop_NNN.json`
```json
{
  "loop": N,
  "approved_by": "chatgpt",
  "approved_at": "ISO",
  "awaiting_human_approval": true,
  "items": [
    {
      "id": "BATCH-NNN-01",
      "source_ids": ["CC-L001-001", "CW-L001-003"],
      "title": "...",
      "action": "exact implementation instruction",
      "priority": 1,
      "risk": "low|medium|high",
      "files_likely": ["index.html"]
    }
  ],
  "deferred": [...],
  "rejected": [...]
}
```

## After writing
Update AUDIT_STATE.json:
- `merge_status.chatgpt.complete` → true
- `merge_status.chatgpt.merged_file` → filename
- `merge_status.chatgpt.batch_file` → filename
- `phase` → "awaiting_approval"
- `stats.total_issues_found` / `approved_count` / `deferred_count` / `rejected_count`

## STOP HERE
Do NOT proceed to implementation. The batch must be reviewed and approved by Aaron first.
Aaron will set `human_approved` → true in AUDIT_STATE.json when ready.
