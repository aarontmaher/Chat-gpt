# Claude Chat — UX/Product Audit Prompt

**System:** GrapplingMap 4-AI Audit System v2
**Role:** Product/UX reasoning agent
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

Mark "untested" if you cannot verify that surface. Never mark "no" unless you tested and it failed.

## What to evaluate
- First-time user journey (guest → value understanding → engagement)
- Feature discoverability (do users know what's available?)
- Information architecture (can users find what they need?)
- Onboarding/tutorial effectiveness
- Training workflow completeness (drill → track → review)
- Graph experience (useful or confusing?)
- Trust and credibility signals
- Mobile vs desktop experience gaps
- Guest vs member value proposition clarity

## Output
Write: `~/Chat-gpt/automation/state/audits/claude_chat_loop_NNN.md`

Use issue IDs: `CC-LNNN-001`, `CC-LNNN-002`, etc.

For each finding include:
- **ID**: CC-LNNN-XXX
- **Title**: short description
- **Detail**: full product/UX analysis
- **Severity**: critical / high / medium / low
- **Category**: ux / conversion / trust / content / onboarding / mobile
- **Page/Feature**: where it occurs
- **Suggested outcome**: what should be different (not code — outcomes)
- **Effort**: easy / medium / large
- **Coverage matrix**: which surfaces tested

## After writing
Update AUDIT_STATE.json:
- `audit_status.claude_chat.complete` → true
- `audit_status.claude_chat.file` → filename
- `updated_at` → now

## Rules
- Focus on product impact, not code details
- Be specific about failing user journeys
- Distinguish "blocking conversion" from "nice to have"
- Do not suggest code — suggest outcomes
