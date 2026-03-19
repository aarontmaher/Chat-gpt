#!/bin/bash
# tools/siri/get-next.sh
# Fetches PENDING TASKS from CLAUDE.md and outputs for Siri to speak

set -euo pipefail

RAW_URL="https://raw.githubusercontent.com/aarontmaher/Chat-gpt/main/CLAUDE.md"

curl -s "$RAW_URL" | \
    sed -n '/## PENDING TASKS/,/^---$/p' | \
    grep -v "^##" | grep -v "^---" | grep -v "^#" | grep -v "^$" | \
    head -5
