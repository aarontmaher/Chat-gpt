# Code Audit Prompt

Read `~/Chat-gpt/audit-system/STATE.json` to confirm phase is "audit".

Run a technical audit of `/Users/aaronmaher/Chat-gpt/index.html` and supporting files.

## What to check
1. Run `npm run check` — report any test failures
2. Check for console errors (the "No console errors" test)
3. Scan for: dead code, unused variables, broken event listeners, state inconsistencies
4. Check innerHTML usage for XSS risks
5. Check localStorage integrity (all STATE fields in save/load/export/import/reset)
6. Check accessibility: ARIA, focus traps, keyboard nav, screen reader
7. Check performance: DOM count, unnecessary reflows, heavy operations
8. Check mobile CSS: any overflow, offscreen, or layout issues in media queries
9. Check PWA: service worker, manifest, offline behavior
10. Check 3D graph: WebGL fallbacks, touch handling, memory leaks

## Output format
Write findings to `~/Chat-gpt/audit-system/audit-inbox/code.json`:

```json
{
  "agent": "code",
  "cycle": <from STATE.json>,
  "timestamp": "<ISO>",
  "findings": [
    {
      "id": "CD-001",
      "title": "Short description",
      "detail": "Technical analysis with file:line references",
      "severity": "critical|high|medium|low",
      "category": "bug|performance|accessibility|security|code-health",
      "page": "file:line or feature",
      "evidence": "Code reference or test output",
      "suggested_fix": "Exact code change needed",
      "effort": "easy|medium|large",
      "confidence": "high|medium|low"
    }
  ]
}
```

## After writing findings
Update STATE.json: set `audit_complete.code` to `true`.

## Rules
- Only report real issues, not style preferences
- Include file paths and line numbers
- Distinguish bugs from improvements
- Do not implement fixes during audit phase
