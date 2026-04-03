# Code — Implementation Prompt

**System:** GrapplingMap 4-AI Audit System v2
**Role:** Sole implementation agent
**Loop:** Read from `~/Chat-gpt/automation/state/AUDIT_STATE.json`

## Prerequisites
- `phase` must be "implement"
- `human_approved` must be true
- Read the approved batch from the file in `merge_status.chatgpt.batch_file`

## Your job
1. Read the approved batch JSON
2. Implement ONLY items with status `do_now`
3. Run `npm run check` before AND after
4. Commit and push if tests pass
5. Write implementation results

## Output
Write: `~/Chat-gpt/automation/state/implementation/impl_loop_NNN.json`
```json
{
  "loop": N,
  "implemented_by": "code",
  "implemented_at": "ISO",
  "commit": "hash",
  "tests_before": "23/23",
  "tests_after": "23/23",
  "items": [
    {
      "id": "BATCH-NNN-01",
      "status": "done|blocked|skipped",
      "detail": "what changed",
      "files_changed": ["index.html:1234"],
      "blocker": null
    }
  ]
}
```

Update issues.json: set implemented items to `status: "implemented"`, `loop_last_touched: N`.

Update AUDIT_STATE.json:
- `implementation_status.complete` → true
- `implementation_status.commit` → hash
- `implementation_status.tests_before/after` → results
- `implementation_status.result_file` → filename
- `phase` → "verify"
- `stats.implemented_count` → count

## Rules
- Do NOT implement deferred or rejected items
- Do NOT make changes beyond what's in the batch
- If blocked, mark and continue
- Tests must pass before committing
- One commit for the entire batch
