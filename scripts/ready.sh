#!/bin/bash
set -e
echo "=== GrapplingMap Ready Check ==="
cd /Users/aaronmaher/Chat-gpt

echo ""
echo "--- Build check ---"
python3 -c "
import re, json
html = open('index.html').read()
# Count edges
idx = html.find('const NET_EDGES = [')
if idx == -1:
    print('FAIL: NET_EDGES not found')
    exit(1)
start = idx + len('const NET_EDGES = ')
depth = 0
end = start
for i, c in enumerate(html[start:]):
    if c == '[': depth += 1
    elif c == ']': depth -= 1
    if depth == 0:
        end = start + i + 1
        break
edges = json.loads(html[start:end])
print(f'edges: {len(edges)} (expected 36)')
assert len(edges) == 36, f'FAIL: expected 36 edges, got {len(edges)}'
# Count guard positions
idx2 = html.find('const SECTIONS = [')
start2 = idx2 + len('const SECTIONS = ')
depth2 = 0
for i, c in enumerate(html[start2:]):
    if c == '[': depth2 += 1
    elif c == ']': depth2 -= 1
    if depth2 == 0:
        end2 = start2 + i + 1
        break
sections = json.loads(html[start2:end2])
guard = next((s for s in sections if s['title']=='Guard'), None)
guard_count = len(guard['nodes']) if guard else 0
print(f'guard: {guard_count} (expected 19)')
assert guard_count == 19, f'FAIL: expected 19 guard positions, got {guard_count}'
print('build: PASS')
"

echo ""
echo "--- Smoke tests ---"
npx playwright test tests/e2e/smoke.spec.js --reporter=line

echo ""
echo "--- Open PRs ---"
curl -s "https://api.github.com/repos/aarontmaher/Chat-gpt/pulls?state=open" | python3 -c "
import json,sys
prs = json.load(sys.stdin)
print(f'open PRs: {len(prs)}')
"

echo ""
echo "--- OPML fingerprint ---"
python3 -c "
import hashlib, os
p = os.path.expanduser('~/GrapplingMap/exports/grappling.opml')
if os.path.exists(p):
    with open(p, 'rb') as f:
        fp = hashlib.md5(f.read()).hexdigest()
    print(f'fingerprint: {fp[:8]}...')
else:
    print('OPML file not found (skipped)')
"

echo ""
echo "=== Ready check complete ==="
