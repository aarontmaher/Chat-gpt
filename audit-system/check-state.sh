#!/usr/bin/env bash
# Check the current state of the audit system
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
STATE="$DIR/STATE.json"

python3 -c "
import json
s = json.load(open('$STATE'))
print('============================================')
print(f'  Audit Cycle {s[\"cycle\"]}')
print(f'  Phase: {s[\"phase\"]}')
print(f'  Updated: {s[\"updated_at\"]}')
print('============================================')
print()
print('Audit complete:')
for agent, done in s['audit_complete'].items():
    print(f'  {agent}: {\"✓\" if done else \"pending\"}'  )
print()
print(f'Batch approved: {\"✓\" if s[\"batch_approved\"] else \"pending\"}')
print(f'Batch implemented: {\"✓\" if s[\"batch_implemented\"] else \"pending\"}')
print(f'Items: {s[\"items_fixed\"]}/{s[\"batch_item_count\"]} fixed')
print()
print('Verification:')
for agent, done in s['verify_complete'].items():
    print(f'  {agent}: {\"✓\" if done else \"pending\"}'  )
print()
print(f'Converged: {\"✓\" if s[\"converged\"] else \"not yet\"}')
print()

# Next action
if s['phase'] == 'idle':
    print('Next: Run init-cycle.sh to start a new audit cycle')
elif s['phase'] == 'audit':
    pending = [a for a, d in s['audit_complete'].items() if not d]
    plist = ', '.join(pending)
    print(f'Next: Waiting for audit from: {plist}')
    for p in pending:
        prompt_name = {'cowork': 'audit-cowork.md', 'claude_chat': 'audit-chat.md', 'code': 'audit-code.md'}[p]
        print(f'  → Give {p} the prompt: prompts/{prompt_name}')
elif s['phase'] == 'merge':
    print('Next: Give ChatGPT the merge prompt: prompts/merge-chatgpt.md')
elif s['phase'] == 'implement':
    print('Next: Give Code the implement prompt: prompts/implement-code.md')
elif s['phase'] == 'verify':
    pending = [a for a, d in s['verify_complete'].items() if not d]
    plist = ', '.join(pending)
    print(f'Next: Waiting for verification from: {plist}')
    print('  → Give each agent: prompts/verify-all.md')
elif s['phase'] == 'converged':
    print('Cycle complete! Run init-cycle.sh to start the next one.')
"
