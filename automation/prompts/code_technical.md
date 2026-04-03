# Code — Technical Audit Prompt

**System:** GrapplingMap 4-AI Audit System v2
**Role:** Technical audit agent
**Loop:** Read from `~/Chat-gpt/automation/state/AUDIT_STATE.json`

## Target
`/Users/aaronmaher/Chat-gpt/index.html` and supporting files

## Coverage Matrix (REQUIRED)
| Surface | Status |
|---------|--------|
| guest | tested / untested |
| logged-in | tested / untested |
| desktop | tested / untested |
| mobile-web | tested / untested |
| iOS Safari | inferred / untested |
| Android Chrome | inferred / untested |
| macOS | tested / untested |
| Windows | inferred / untested |
| Linux | inferred / untested |

## What to check
1. Run `npm run check` — report pass/fail
2. Console errors test result
3. Dead code, unused variables, broken references
4. innerHTML with user data (XSS check)
5. State persistence integrity (all fields in save/load/export/import/reset)
6. Keyboard shortcut conflicts
7. DOM ID duplicates
8. Accessibility: ARIA, focus traps, screen reader
9. Performance: DOM count, reflows, intervals/timeouts balance
10. PWA: service worker, manifest, offline handling
11. 3D graph: WebGL fallbacks, touch handling, memory
12. Mobile CSS: overflow, offscreen, touch targets
13. Event listener leaks

## Smoke checks (every loop)
- `npm run check` passes
- No console errors on load
- State save/load round-trips
- Key user flows don't crash

## Output
Write: `~/Chat-gpt/automation/state/audits/code_loop_NNN.md`

Use issue IDs: `CODE-LNNN-001`, `CODE-LNNN-002`, etc.

For each finding:
- **ID**: CODE-LNNN-XXX
- **Title**: short description
- **Detail**: technical analysis with file:line
- **Severity**: critical / high / medium / low
- **Category**: bug / performance / accessibility / security / code-health
- **File/Line**: exact location
- **Suggested fix**: exact code change
- **Effort**: easy / medium / large
- **Coverage matrix**: surfaces tested

## After writing
Update AUDIT_STATE.json:
- `audit_status.code.complete` → true
- `audit_status.code.file` → filename
- `updated_at` → now

## Rules
- Only report real issues, not style preferences
- Include file paths and line numbers
- Distinguish bugs from improvements
- Do NOT implement fixes during audit phase
