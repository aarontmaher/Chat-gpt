# Verification Prompt (All Agents)

Read `~/Chat-gpt/audit-system/STATE.json` to confirm phase is "verify".
Read `~/Chat-gpt/audit-system/batch-result.json` to see what was implemented.

## Your job
Verify each implemented item from the batch:
1. Check that the fix actually works
2. Check that it didn't break anything else
3. Check for regressions
4. Note any NEW issues discovered during verification

## Output
Write to `~/Chat-gpt/audit-system/verify-inbox/<your-agent>.json`:

```json
{
  "agent": "<cowork|claude-chat|code|chatgpt>",
  "cycle": <from STATE.json>,
  "timestamp": "<ISO>",
  "batch_items_verified": [
    {
      "id": "BATCH-001-01",
      "status": "pass|fail|regression",
      "detail": "What you checked and observed",
      "new_issues_found": []
    }
  ],
  "overall": "pass|fail",
  "new_findings": [
    {
      "id": "<AGENT>-NEW-001",
      "title": "New issue found during verification",
      "detail": "...",
      "severity": "critical|high|medium|low",
      "category": "...",
      "page": "..."
    }
  ]
}
```

Update STATE.json: set your `verify_complete.<agent>` flag to true.

## Agent-specific verification
- **Cowork**: Visually verify each fix on the live site (desktop + mobile)
- **Claude Chat**: Evaluate whether fixes improved the user experience
- **Code**: Run tests, check for regressions, verify code changes
- **ChatGPT**: Review all other agents' verifications for consistency
