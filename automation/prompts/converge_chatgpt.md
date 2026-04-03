# ChatGPT — Convergence Decision Prompt

**System:** GrapplingMap 4-AI Audit System v2
**Role:** Convergence decision maker
**Loop:** Read from `~/Chat-gpt/automation/state/AUDIT_STATE.json`

## Prerequisites
All 4 `verification_status` agents must be `complete: true`.

## Input
Read all verification files from `~/Chat-gpt/automation/state/verification/`

## Convergence criteria

**Converged** when:
1. All approved batch items have Code verification = pass
2. Cowork confirms user-facing behavior is materially correct
3. Claude Chat confirms the changes materially resolved the UX issues
4. No agent found critical/high regressions
5. Minor disagreements do NOT block closure

**NOT converged** when:
1. Any agent found a regression
2. Code tests fail
3. New critical/high issues were introduced
4. Implementation clearly missed the intent of approved items

## If converged
- Update issues.json: verified items → `status: "verified"`
- Update AUDIT_STATE.json: `convergence.decided` → true, `convergence.converged` → true, `phase` → "converged"
- Report: "Loop N converged. X items verified, 0 regressions."

## If NOT converged
- New findings → add to issues.json with `status: "new"`, `loop_found: N+1`
- Failed items → `status: "failed"` in issues.json
- Update AUDIT_STATE.json: `convergence.decided` → true, `convergence.converged` → false
- Report: "Loop N not converged. Reason: [X]. Failed items and new findings carried to loop N+1."
- Do NOT auto-start the next loop — Aaron will run `init_cycle.sh`

## Partial loop rule
Failed items get deep re-audit next loop. But every loop also includes lightweight smoke:
- npm run check
- key user flows
