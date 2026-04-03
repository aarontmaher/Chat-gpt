# Code Implementation Prompt

Read `~/Chat-gpt/audit-system/STATE.json` to confirm phase is "implement" and batch_approved is true.

Read `~/Chat-gpt/audit-system/batch.json` for the approved implementation batch.

## Your job
1. Implement ONLY the items classified as `do_now` in batch.json
2. For each item, follow the exact action instructions
3. Run `npm run check` after all changes
4. Commit and push if tests pass
5. Write results to batch-result.json

## Output
Write `~/Chat-gpt/audit-system/batch-result.json`:

```json
{
  "cycle": <from STATE.json>,
  "implemented_by": "code",
  "implemented_at": "<ISO>",
  "commit": "<hash>",
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

Update STATE.json: set `batch_implemented` to true, `phase` to "verify", `items_fixed` count.

## Rules
- Do NOT implement deferred or rejected items
- Do NOT make changes beyond what's in batch.json
- If an item is blocked, mark it and continue to the next
- Tests must pass before committing
- One commit for the entire batch
