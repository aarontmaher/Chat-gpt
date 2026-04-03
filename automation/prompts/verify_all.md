# All Agents — Verification Prompt

**System:** GrapplingMap 4-AI Audit System v2
**Role:** Verification (all 4 agents)
**Loop:** Read from `~/Chat-gpt/automation/state/AUDIT_STATE.json`

## Prerequisites
- `phase` must be "verify"
- Read implementation results from file in `implementation_status.result_file`

## Your job
Verify each implemented item:
1. Does the fix work as intended?
2. Did it introduce regressions?
3. Are there new issues?

## Smoke checks (Code only, every loop)
- `npm run check` passes
- No console errors
- Key user flows work

## Output
Write: `~/Chat-gpt/automation/state/verification/<agent>_loop_NNN.md`

For each batch item:
- **ID**: BATCH-NNN-XX
- **Status**: pass / fail / regression
- **Detail**: what you verified
- **New issues**: any new problems found

Overall: pass / fail

## After writing
Update AUDIT_STATE.json:
- `verification_status.<agent>.complete` → true
- `verification_status.<agent>.file` → filename

Update issues.json: set verified items to `status: "verified"`, failed items to `status: "failed"`.

## Agent-specific focus
- **Cowork**: visually verify on live site (desktop + mobile resize)
- **Claude Chat**: evaluate UX improvement quality
- **Code**: run tests, check for regressions, verify code
- **ChatGPT**: review all verifications, check consistency
