# Cowork Audit Prompt

Read `~/Chat-gpt/audit-system/STATE.json` to confirm phase is "audit".

Audit the live GrapplingMap website at https://aarontmaher.github.io/Chat-gpt/

## What to check
- Walk through as a guest first, then as a member if possible
- Check every visible page/tab/panel/modal
- Test on desktop viewport, then resize to mobile (390px width)
- Look for: broken UI, layout issues, overlapping elements, dead buttons, empty states, confusing flows, missing content, accessibility problems, mobile-specific issues

## Output format
Write your findings to `~/Chat-gpt/audit-system/audit-inbox/cowork.json` using this format:

```json
{
  "agent": "cowork",
  "cycle": <read from STATE.json>,
  "timestamp": "<ISO timestamp>",
  "findings": [
    {
      "id": "CW-001",
      "title": "Short description",
      "detail": "Full explanation with what you saw",
      "severity": "critical|high|medium|low",
      "category": "bug|ux|performance|accessibility|content|trust|conversion",
      "page": "/path or feature name",
      "evidence": "screenshot or description of what you saw",
      "suggested_fix": "What should change",
      "effort": "easy|medium|large",
      "confidence": "high|medium|low"
    }
  ]
}
```

## After writing findings
Update STATE.json: set `audit_complete.cowork` to `true` and `updated_at` to now.

## Rules
- Only report things you actually observed, not theoretical issues
- Include enough detail for Code to reproduce and fix
- Separate real bugs from subjective preferences
- Do not implement any fixes
