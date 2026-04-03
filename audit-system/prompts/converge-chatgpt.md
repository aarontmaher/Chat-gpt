# ChatGPT Convergence Prompt

Read `~/Chat-gpt/audit-system/STATE.json` to confirm all 4 verify_complete flags are true.

Read all verification results from `~/Chat-gpt/audit-system/verify-inbox/`:
- cowork.json
- claude-chat.json
- code.json
- chatgpt.json

## Your job
Determine whether this cycle has **converged** (is complete) or needs another iteration.

## Convergence criteria
The cycle is **converged** if:
1. All 4 agents verified the batch as "pass"
2. No agent found regressions
3. No new critical or high-severity findings
4. Any new findings are low priority and can be deferred to the next scheduled cycle

The cycle is **NOT converged** if:
1. Any agent reported a regression
2. Any agent found new critical/high issues
3. The implementation introduced bugs

## If converged
Update STATE.json: set `converged` to true, `phase` to "converged".
Report: "Cycle N converged. X items fixed, 0 regressions."

## If NOT converged
1. Move new findings into `audit-inbox/` for the next cycle
2. Update STATE.json: increment `cycle`, reset flags, set `phase` to "audit"
3. Report: "Cycle N not converged. New issues: [list]. Starting cycle N+1."

## Output
State your convergence decision with reasoning.
