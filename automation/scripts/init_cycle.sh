#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
STATE="$DIR/state/AUDIT_STATE.json"
ISSUES="$DIR/state/issues.json"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

CURRENT=$(python3 -c "import json; print(json.load(open('$STATE'))['loop'])")
NEXT=$((CURRENT + 1))
PADDED=$(printf '%03d' $NEXT)

echo "============================================"
echo "  Initializing Audit Loop $NEXT"
echo "============================================"

python3 << PYEOF
import json

state = json.load(open('$STATE'))
state['loop'] = $NEXT
state['phase'] = 'audit'
state['started_at'] = '$NOW'
state['updated_at'] = '$NOW'
state['audit_status'] = {
    'claude_chat': {'complete': False, 'file': None},
    'cowork': {'complete': False, 'file': None},
    'code': {'complete': False, 'file': None}
}
state['merge_status'] = {'chatgpt': {'complete': False, 'merged_file': None, 'batch_file': None}}
state['human_approved'] = False
state['implementation_status'] = {'complete': False, 'commit': None, 'tests_before': None, 'tests_after': None, 'result_file': None}
state['verification_status'] = {
    'claude_chat': {'complete': False, 'file': None},
    'cowork': {'complete': False, 'file': None},
    'code': {'complete': False, 'file': None},
    'chatgpt': {'complete': False, 'file': None}
}
state['convergence'] = {'decided': False, 'converged': False, 'reason': None}
json.dump(state, open('$STATE', 'w'), indent=2)
print(f"  State reset for loop $NEXT")
PYEOF

echo ""
echo "Next steps:"
echo "  1. Cowork  → prompts/cowork_ui.md"
echo "  2. Claude Chat → prompts/claude_chat_ux.md"
echo "  3. Code    → prompts/code_technical.md"
echo "  (all 3 can run in parallel)"
echo ""
echo "  4. When all 3 complete → ChatGPT: prompts/chatgpt_merge.md"
echo "  5. Aaron approves batch"
echo "  6. Code: prompts/code_implement.md"
echo "  7. All 4: prompts/verify_all.md"
echo "  8. ChatGPT: prompts/converge_chatgpt.md"
echo ""
echo "Check status: scripts/check_state.sh"
