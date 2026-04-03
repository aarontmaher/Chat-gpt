#!/usr/bin/env bash
# Initialize a new audit cycle
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
STATE="$DIR/STATE.json"

# Read current cycle
CURRENT=$(python3 -c "import json; print(json.load(open('$STATE'))['cycle'])")
NEXT=$((CURRENT + 1))
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Archive previous cycle if it exists and has data
if [ "$CURRENT" -gt 0 ] && [ -d "$DIR/audit-inbox" ]; then
  ARCHIVE="$DIR/history/cycle-$(printf '%03d' $CURRENT)"
  mkdir -p "$ARCHIVE"
  cp -r "$DIR/audit-inbox/" "$ARCHIVE/audit-inbox/" 2>/dev/null || true
  cp -r "$DIR/verify-inbox/" "$ARCHIVE/verify-inbox/" 2>/dev/null || true
  cp "$DIR/batch.json" "$ARCHIVE/" 2>/dev/null || true
  cp "$DIR/batch-result.json" "$ARCHIVE/" 2>/dev/null || true
  cp "$DIR/STATE.json" "$ARCHIVE/STATE.json" 2>/dev/null || true
  echo "Archived cycle $CURRENT to $ARCHIVE"
fi

# Clear working files
rm -f "$DIR/audit-inbox/"*.json
rm -f "$DIR/verify-inbox/"*.json
rm -f "$DIR/batch.json"
rm -f "$DIR/batch-result.json"

# Write new state
python3 -c "
import json
state = {
    'cycle': $NEXT,
    'phase': 'audit',
    'started_at': '$NOW',
    'updated_at': '$NOW',
    'audit_complete': {'cowork': False, 'claude_chat': False, 'code': False},
    'batch_approved': False,
    'batch_implemented': False,
    'verify_complete': {'cowork': False, 'claude_chat': False, 'code': False, 'chatgpt': False},
    'converged': False,
    'batch_item_count': 0,
    'items_fixed': 0,
    'items_remaining': 0
}
json.dump(state, open('$STATE', 'w'), indent=2)
"

echo "============================================"
echo "  Audit Cycle $NEXT initialized"
echo "  Phase: audit"
echo "  Time: $NOW"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Give Cowork the audit prompt:  prompts/audit-cowork.md"
echo "  2. Give Claude Chat the audit prompt: prompts/audit-chat.md"
echo "  3. Give Code the audit prompt:    prompts/audit-code.md"
echo "  4. When all 3 complete, give ChatGPT: prompts/merge-chatgpt.md"
