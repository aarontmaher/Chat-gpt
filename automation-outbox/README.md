# Audit Automation Outbox

## How It Works

### State Model
The trigger file (`audit_trigger.json`) has three states:

```
"status": "ready"    → prompts are written, KM should send them
"status": "sent"     → KM sent the prompts and archived them
"status": "idle"     → nothing to do
```

### Files
- `audit_trigger.json` — state + metadata
- `chat_audit_prompt.txt` — prompt for Claude Chat (only exists when status=ready)
- `cowork_audit_prompt.txt` — prompt for Cowork (only exists when status=ready)
- `archive/` — timestamped copies of sent prompts

### Code's Job
1. After a meaningful push, write both prompt files
2. Set trigger to `status: "ready"`
3. Never set trigger to "ready" without also writing the prompt files

### KM's Job
1. Check trigger — if `status` is NOT `"ready"`, do nothing
2. If `"ready"`:
   a. Read `chat_audit_prompt.txt` → paste to Claude Chat
   b. Read `cowork_audit_prompt.txt` → paste to Cowork
   c. Archive both files with timestamp
   d. Set trigger to `"status": "sent"`
3. Never archive without setting status to "sent"

### Aaron's Manual Test
1. Run: `cat automation-outbox/audit_trigger.json` — should show status
2. Run: `ls automation-outbox/*.txt` — should show prompt files if status=ready
3. If status=ready but no .txt files → broken state, run Code's refresh prompt
4. If status=sent → KM ran, check archive for what was sent

### Debug
- If KM didn't fire: check trigger status + whether .txt files exist
- If prompts are empty/stale: have Code refresh them
- If state is inconsistent: set trigger to `"status": "idle"` and start fresh
