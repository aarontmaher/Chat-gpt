#!/bin/bash
# tools/siri/send-prompt.sh
# Called by Siri Shortcut via SSH or Run Script action
# Usage: bash tools/siri/send-prompt.sh "prompt text"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../../.env.zapier"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: .env.zapier not found at $ENV_FILE"
    exit 1
fi

WEBHOOK_URL=$(grep ZAPIER_WEBHOOK "$ENV_FILE" | head -1 | cut -d= -f2)

if [[ -z "$WEBHOOK_URL" ]]; then
    echo "ERROR: ZAPIER_WEBHOOK not set in .env.zapier"
    exit 1
fi

PROMPT_TEXT="${1:?Usage: send-prompt.sh \"prompt text\"}"

curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": $(echo "$PROMPT_TEXT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'), \"source\": \"siri\"}"

echo "Sent to Zapier"
