#!/bin/bash
# Quick check of audit automation outbox state
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Audit Trigger ==="
cat "$DIR/audit_trigger.json" 2>/dev/null || echo "(missing)"

echo ""
echo "=== Prompt Files ==="
for f in chat_audit_prompt.txt cowork_audit_prompt.txt; do
  if [ -f "$DIR/$f" ]; then
    SIZE=$(wc -c < "$DIR/$f" | tr -d ' ')
    echo "  ✓ $f ($SIZE bytes)"
  else
    echo "  ✗ $f (MISSING)"
  fi
done

echo ""
echo "=== Archive ==="
ls -1 "$DIR/archive/" 2>/dev/null | tail -5 || echo "  (empty)"

echo ""
# Consistency check
STATUS=$(python3 -c "import json; print(json.load(open('$DIR/audit_trigger.json')).get('status','unknown'))" 2>/dev/null || echo "unknown")
HAS_CHAT=$([ -f "$DIR/chat_audit_prompt.txt" ] && echo "yes" || echo "no")
HAS_COWORK=$([ -f "$DIR/cowork_audit_prompt.txt" ] && echo "yes" || echo "no")

if [ "$STATUS" = "ready" ] && [ "$HAS_CHAT" = "no" -o "$HAS_COWORK" = "no" ]; then
  echo "⚠ INCONSISTENT: trigger=ready but prompt files missing!"
elif [ "$STATUS" = "ready" ] && [ "$HAS_CHAT" = "yes" ] && [ "$HAS_COWORK" = "yes" ]; then
  echo "✓ READY: trigger=ready, both prompts exist. KM should fire."
elif [ "$STATUS" = "sent" ]; then
  echo "✓ SENT: KM already ran. Check archive for details."
elif [ "$STATUS" = "idle" ]; then
  echo "○ IDLE: nothing pending."
else
  echo "? STATUS: $STATUS (chat=$HAS_CHAT, cowork=$HAS_COWORK)"
fi
