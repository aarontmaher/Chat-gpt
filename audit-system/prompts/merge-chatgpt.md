# ChatGPT Merge Prompt

Read `~/Chat-gpt/audit-system/STATE.json` to confirm all 3 audit_complete flags are true.

Read all audit findings from:
- `~/Chat-gpt/audit-system/audit-inbox/cowork.json`
- `~/Chat-gpt/audit-system/audit-inbox/claude-chat.json`
- `~/Chat-gpt/audit-system/audit-inbox/code.json`

## Your job
1. Deduplicate — if multiple agents found the same issue, merge into one item
2. Classify each unique finding:
   - `do_now` — clear improvement, safe, high value
   - `do_later` — valid but lower priority
   - `do_not_do` — generic fluff, risky, or low value
   - `needs_safer_version` — good idea but needs a different approach
3. Prioritize the `do_now` items into an implementation batch
4. Write the approved batch

## Decision standard
Approve if it:
- Clearly improves conversion, UX, trust, speed, or maintainability
- Is low enough risk for the current app
- Is genuinely better, not just different

Reject if it:
- Is generic best-practice with no specific user value
- Would add visual clutter
- Risks theme/app stability
- Is redundant with existing functionality

## Output
Write `~/Chat-gpt/audit-system/batch.json` with the approved batch format.
Update STATE.json: set `batch_approved` to true, `phase` to "implement", `batch_item_count` to the number of approved items.

## Rules
- Be the quality gate — not everything suggested should be implemented
- Group related fixes into coherent items
- Provide exact implementation instructions for Code
- Include risk level for each item
