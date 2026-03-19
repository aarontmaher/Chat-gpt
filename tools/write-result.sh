#!/bin/bash
# tools/write-result.sh
# Usage: bash tools/write-result.sh "PROMPT-ID" "plain_summary" "commit" [edges] [no_dest] [in_network] [built_out] [decisions_needed] [technical_summary]
# Called by Code at end of every task.
#
# plain_summary: One sentence, plain English, no jargon, no prompt IDs.
#   GOOD: "Fixed the graph so clicking a technique stays in 3D instead of switching tabs"
#   BAD:  "SITE-BATCH-09 G1 fix1 technique-click done"
#
# decisions_needed: Pipe-separated simple questions for Aaron, or empty string.
#   GOOD: "Should Half guard be separate?|What label for the Mount transition?"
#   BAD:  "" (leave empty if none)
#
# technical_summary: Optional short technical note for Code/Chat reference.

PROMPT_ID="${1:-unknown}"
PLAIN_SUMMARY="${2:-no summary}"
COMMIT="${3:-unknown}"
EDGES="${4:-null}"
NO_DEST="${5:-null}"
IN_NETWORK="${6:-null}"
BUILT_OUT="${7:-null}"
DECISIONS_RAW="${8:-}"
TECHNICAL_SUMMARY="${9:-}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_FILE="${SCRIPT_DIR}/../results.md"

# Build decisions_needed JSON array from pipe-separated string
if [[ -z "$DECISIONS_RAW" ]]; then
    DECISIONS_JSON="[]"
else
    DECISIONS_JSON=$(echo "$DECISIONS_RAW" | python3 -c "
import sys, json
raw = sys.stdin.read().strip()
items = [q.strip() for q in raw.split('|') if q.strip()]
print(json.dumps(items))
")
fi

# Build JSON result
RESULT=$(python3 -c "
import json
data = {
    'prompt_id': '$PROMPT_ID',
    'timestamp': '$TIMESTAMP',
    'status': 'complete',
    'plain_summary': '''$PLAIN_SUMMARY'''.strip(),
    'technical_summary': '''$TECHNICAL_SUMMARY'''.strip() or None,
    'decisions_needed': $DECISIONS_JSON,
    'edges': $EDGES if '$EDGES' != 'null' else None,
    'no_dest': $NO_DEST if '$NO_DEST' != 'null' else None,
    'in_network': $IN_NETWORK if '$IN_NETWORK' != 'null' else None,
    'built_out': $BUILT_OUT if '$BUILT_OUT' != 'null' else None,
    'commit': '$COMMIT',
    'console_errors': 'none',
    'flags': []
}
print(json.dumps(data, indent=2))
")

# Read current results.md
if [[ ! -f "$RESULTS_FILE" ]]; then
    echo "ERROR: results.md not found at $RESULTS_FILE"
    exit 1
fi

CURRENT=$(cat "$RESULTS_FILE")

# Extract old latest result (between markers, excluding marker lines)
OLD_LATEST=$(echo "$CURRENT" | sed -n '/<!-- LATEST-RESULT-START -->/,/<!-- LATEST-RESULT-END -->/p' | grep -v '<!-- LATEST-RESULT-START -->' | grep -v '<!-- LATEST-RESULT-END -->')

# Extract existing history (between markers, excluding marker lines)
HISTORY=$(echo "$CURRENT" | sed -n '/<!-- RESULT-HISTORY -->/,/<!-- RESULT-HISTORY-END -->/p' | grep -v '<!-- RESULT-HISTORY -->' | grep -v '<!-- RESULT-HISTORY-END -->')

# Write updated results.md
cat > "$RESULTS_FILE" << ENDFILE
# GrapplingMap — Results Feed
# Code writes here after every completed task.
# Claude Chat + Voice Claude read this to debrief Aaron.
# Format: most recent first. plain_summary is spoken aloud by Siri.

<!-- LATEST-RESULT-START -->
$RESULT
<!-- LATEST-RESULT-END -->

<!-- RESULT-HISTORY -->
$OLD_LATEST
$HISTORY
<!-- RESULT-HISTORY-END -->
ENDFILE

echo "Result written: $PROMPT_ID ($TIMESTAMP)"
