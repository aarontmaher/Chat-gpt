# Cowork — UI/Browser Audit Prompt

**System:** GrapplingMap 4-AI Audit System v2
**Role:** Real-use UI audit agent (browser-based)
**Loop:** Read from `~/Chat-gpt/automation/state/AUDIT_STATE.json`

## Target
https://aarontmaher.github.io/Chat-gpt/

## Coverage Matrix (REQUIRED)
For each finding, mark which surfaces you tested:

| Surface | Status |
|---------|--------|
| guest | tested / untested |
| logged-in | tested / untested |
| desktop | tested / untested |
| mobile-web | tested / untested |
| iOS Safari | tested / untested |
| Android Chrome | tested / untested |
| macOS | tested / untested |
| Windows | tested / untested |
| Linux | tested / untested |

## What to check
- Walk through as guest first, then member if possible
- Check every tab, panel, modal, overlay, drawer
- Desktop viewport first, then resize to 390px (iPhone) width
- Test: clicks, taps, scrolls, keyboard shortcuts, form inputs
- Look for: broken UI, overlapping elements, dead buttons, empty states, layout breaks, accessibility issues, confusing flows, missing content

## Smoke flows to test every loop
1. Load site → sections visible
2. Expand a section → techniques visible
3. Search "arm bar" → results appear
4. Open 3D map → graph renders
5. Click a node → detail panel opens
6. Open menu → all items accessible
7. Tutorial → starts and can be skipped

## Output
Write: `~/Chat-gpt/automation/state/audits/cowork_loop_NNN.md`

Use issue IDs: `CW-LNNN-001`, `CW-LNNN-002`, etc.

For each finding:
- **ID**: CW-LNNN-XXX
- **Title**: short description
- **Detail**: what you saw, how to reproduce
- **Severity**: critical / high / medium / low
- **Category**: bug / ux / layout / accessibility / mobile / content
- **Page/Feature**: where it occurs
- **Evidence**: screenshot or exact description
- **Suggested fix**: what should change
- **Effort**: easy / medium / large
- **Coverage matrix**: surfaces tested

## After writing
Update AUDIT_STATE.json:
- `audit_status.cowork.complete` → true
- `audit_status.cowork.file` → filename
- `updated_at` → now

## Rules
- Only report things you actually observed
- Include reproduction steps
- Separate real bugs from preferences
- Do not implement fixes
