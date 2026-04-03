#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
STATE="$DIR/state/AUDIT_STATE.json"

python3 << 'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
print("=" * 50)
print(f"  Audit Loop {s['loop']}  |  Phase: {s['phase']}")
print(f"  Updated: {s['updated_at']}")
print("=" * 50)
print()

# Audit
print("AUDIT:")
for a, d in s['audit_status'].items():
    mark = "✓" if d['complete'] else "·"
    print(f"  {mark} {a}: {'done → ' + (d['file'] or '') if d['complete'] else 'pending'}")

# Merge
m = s['merge_status']['chatgpt']
print(f"\nMERGE: {'✓ done' if m['complete'] else '· pending'}")
print(f"HUMAN APPROVED: {'✓ yes' if s['human_approved'] else '· no'}")

# Implement
im = s['implementation_status']
print(f"\nIMPLEMENT: {'✓ ' + (im['commit'] or '') if im['complete'] else '· pending'}")
if im['complete']:
    print(f"  Tests: {im['tests_before']} → {im['tests_after']}")

# Verify
print("\nVERIFY:")
for a, d in s['verification_status'].items():
    mark = "✓" if d['complete'] else "·"
    print(f"  {mark} {a}")

# Convergence
c = s['convergence']
if c['decided']:
    print(f"\nCONVERGED: {'✓ yes' if c['converged'] else '✗ no — ' + (c['reason'] or '')}")
else:
    print(f"\nCONVERGED: · not decided")

# Stats
st = s['stats']
print(f"\nSTATS: {st['approved_count']} approved, {st['implemented_count']} implemented, {st['verified_count']} verified, {st['deferred_count']} deferred, {st['rejected_count']} rejected")

# Next action
print()
phase = s['phase']
if phase == 'idle':
    print("→ Run: scripts/init_cycle.sh")
elif phase == 'audit':
    pending = [a for a, d in s['audit_status'].items() if not d['complete']]
    print(f"→ Waiting for: {', '.join(pending)}")
elif phase == 'merge':
    print("→ ChatGPT: prompts/chatgpt_merge.md")
elif phase == 'awaiting_approval':
    print("→ Aaron: review batch and set human_approved=true")
elif phase == 'implement':
    print("→ Code: prompts/code_implement.md")
elif phase == 'verify':
    pending = [a for a, d in s['verification_status'].items() if not d['complete']]
    print(f"→ Verify pending: {', '.join(pending)}")
elif phase == 'converged':
    print("→ Loop complete! Run init_cycle.sh for next loop.")
PYEOF
-- "$STATE"
