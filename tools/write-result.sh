#!/bin/bash
# tools/write-result.sh
# Usage: bash tools/write-result.sh "PROMPT-ID" "plain summary" "commit" [edges] [built_out] [next_action]
# Writes simplified LATEST-RESULT block to results.md.
# Preserves history.

set -euo pipefail

PROMPT_ID="${1:-unknown}"
SUMMARY="${2:-no summary}"
COMMIT="${3:-unknown}"
EDGES="${4:-null}"
BUILT_OUT="${5:-null}"
NEXT_ACTION="${6:-Check live site}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_FILE="${SCRIPT_DIR}/../results.md"

if [[ ! -f "$RESULTS_FILE" ]]; then
    echo "ERROR: results.md not found at $RESULTS_FILE"
    exit 1
fi

# Extract history (everything after LATEST-RESULT-END)
HISTORY=$(sed -n '/<!-- LATEST-RESULT-END -->/,$ p' "$RESULTS_FILE" | tail -n +2)

# Write updated results.md
cat > "$RESULTS_FILE" << ENDFILE
# GrapplingMap — Results Feed
# Code writes here after every completed task.
# Aaron: copy the LATEST-RESULT block and paste to Claude Chat.

<!-- LATEST-RESULT-START -->
PROMPT: ${PROMPT_ID} | STATUS: complete | ${SUMMARY}
SITE: edges=${EDGES} | built-out=${BUILT_OUT} | console=clean | commit=${COMMIT}
NEXT: ${NEXT_ACTION}
<!-- LATEST-RESULT-END -->

${HISTORY}
ENDFILE

echo "Result written: ${PROMPT_ID} (${COMMIT})"
