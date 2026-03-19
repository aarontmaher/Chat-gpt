#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title GrapplingMap Status
# @raycast.mode fullOutput
# @raycast.packageName GrapplingMap
# @raycast.shortcut cmd+shift+s

# Fetch and display latest results
curl -s "https://raw.githubusercontent.com/aarontmaher/Chat-gpt/main/results.md" | python3 -c "
import sys, re
content = sys.stdin.read()
m = re.search(r'<!-- LATEST-RESULT-START -->(.*?)<!-- LATEST-RESULT-END -->', content, re.DOTALL)
if m:
    print(m.group(1).strip())
else:
    print('No results found')
"
