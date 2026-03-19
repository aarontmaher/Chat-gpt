#!/bin/bash
# tools/siri/get-status.sh
# Fetches latest result from results.md and outputs for Siri to speak

set -euo pipefail

RAW_URL="https://raw.githubusercontent.com/aarontmaher/Chat-gpt/main/results.md"

RESULT=$(curl -s "$RAW_URL" | \
    sed -n '/<!-- LATEST-RESULT-START -->/,/<!-- LATEST-RESULT-END -->/p' | \
    grep -v '<!--')

if [[ -z "$RESULT" ]]; then
    echo "No results found."
    exit 0
fi

python3 -c "
import sys, json
try:
    d = json.loads('''$RESULT'''.strip())
    pid = d.get('prompt_id', 'unknown')
    summary = d.get('summary', 'no summary')
    edges = d.get('edges', 'unknown')
    commit = d.get('commit', 'unknown')
    print(f'Last task: {pid}. {summary}. Edges: {edges}. Commit: {commit}.')
except Exception as e:
    print(f'Could not parse results: {e}')
"
