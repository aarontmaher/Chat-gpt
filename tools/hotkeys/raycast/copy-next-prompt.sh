#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Copy Next GrapplingMap Prompt
# @raycast.mode silent
# @raycast.packageName GrapplingMap
# @raycast.shortcut cmd+shift+g

# Fetch latest results.md and copy NEXT PROMPT block to clipboard
RESULTS=$(curl -s "https://raw.githubusercontent.com/aarontmaher/Chat-gpt/main/results.md")
NEXT=$(echo "$RESULTS" | python3 -c "
import sys, re
content = sys.stdin.read()
m = re.search(r'<!-- NEXT-PROMPT-START -->(.*?)<!-- NEXT-PROMPT-END -->', content, re.DOTALL)
if m:
    print(m.group(1).strip())
else:
    print('No next prompt found in results.md')
")
echo "$NEXT" | pbcopy
echo "Next prompt copied to clipboard"
