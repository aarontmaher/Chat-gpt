# Zapier Integration — GrapplingMap Prompt Automation

## Overview

Automates prompt routing from Claude Chat to `bridge.md` in the Chat-gpt repo.
Eliminates manual copy-paste between Claude Chat and Code agent.

**Flow:** Claude Chat outputs formatted prompt → Zapier webhook catches it → Zapier writes to `bridge.md` on GitHub → Code agent reads and executes.

---

## Architecture

```
┌──────────────┐    webhook POST     ┌─────────┐    GitHub API     ┌─────────────┐
│ Claude Chat  │ ──────────────────→ │  Zapier │ ──────────────→  │ bridge.md   │
│ (prompt out) │                     │  Zap    │  PUT contents    │ (Chat-gpt)  │
└──────────────┘                     └─────────┘                  └─────────────┘
                                                                        │
                                                                        ▼
                                                                  ┌─────────────┐
                                                                  │ Code agent  │
                                                                  │ reads +     │
                                                                  │ executes    │
                                                                  └─────────────┘
```

**Key constraint:** Zapier writes ONLY to the `NEXT PROMPT TO RUN` block. No automatic pipeline triggering.

---

## 1. Prompt Format Specification

Claude Chat must output prompts in this exact format for Zapier to parse:

```
---ZAPIER-PROMPT-START---
TYPE: CODE|COWORK
SCOPE: <short description>
GOAL: <what this prompt achieves>

<prompt body — the full text Code/Cowork should execute>

— FROM: CLAUDE CHAT
---ZAPIER-PROMPT-END---
```

### Field definitions

| Field | Required | Description |
|-------|----------|-------------|
| TYPE | Yes | Target agent: `CODE` or `COWORK` |
| SCOPE | Yes | One-line summary (used in history log) |
| GOAL | Yes | Success criteria |
| Body | Yes | Full prompt text, any length |
| Sign-off | Yes | Must end with `— FROM: CLAUDE CHAT` |

### Example

```
---ZAPIER-PROMPT-START---
TYPE: CODE
SCOPE: Fix built-out count display
GOAL: Update markBuiltOut() to correctly count 11 positions

Fix the markBuiltOut function in index.html.
The BUILT_OUT_SET should contain exactly 11 entries matching CLAUDE.md.
Verify on localhost before pushing.

— FROM: CLAUDE CHAT
---ZAPIER-PROMPT-END---
```

---

## 2. Zapier Workflow Configuration

### Step 1: Trigger — Webhooks by Zapier (Catch Hook)

1. In Zapier, create a new Zap
2. Trigger: **Webhooks by Zapier** → **Catch Hook**
3. Copy the webhook URL (e.g., `https://hooks.zapier.com/hooks/catch/XXXXX/YYYYY/`)
4. Save this URL — Claude Chat will POST prompts here

**Webhook payload format** (what Claude Chat sends):

```json
{
  "type": "CODE",
  "scope": "Fix built-out count display",
  "goal": "Update markBuiltOut() to correctly count 11 positions",
  "prompt_body": "Fix the markBuiltOut function in index.html.\nThe BUILT_OUT_SET should contain exactly 11 entries matching CLAUDE.md.\nVerify on localhost before pushing.",
  "sign_off": "— FROM: CLAUDE CHAT",
  "timestamp": "2026-03-19T14:30:00Z"
}
```

### Step 2: Action — Code by Zapier (Run JavaScript)

Purpose: Format the prompt body into the bridge.md block structure.

```javascript
// Input fields from trigger:
// inputData.type, inputData.scope, inputData.goal,
// inputData.prompt_body, inputData.sign_off, inputData.timestamp

const marker_start = '<!-- START PROMPT -->';
const marker_end = '<!-- END PROMPT -->';

const prompt_block = [
  `TYPE: ${inputData.type}`,
  `SCOPE: ${inputData.scope}`,
  `GOAL: ${inputData.goal}`,
  '',
  inputData.prompt_body,
  '',
  inputData.sign_off
].join('\n');

const history_entry = [
  `| ${inputData.timestamp} | ${inputData.type} | ${inputData.scope} | received |`
].join('\n');

output = {
  prompt_block: prompt_block,
  history_entry: history_entry,
  timestamp: inputData.timestamp
};
```

### Step 3: Action — Code by Zapier (Run JavaScript) — Read current bridge.md

Purpose: Fetch current bridge.md content and SHA (required for GitHub API update).

```javascript
// Uses fetch to read current file via GitHub API
const owner = 'aarontmaher';
const repo = 'Chat-gpt';
const path = 'bridge.md';
const token = inputData.github_token; // from Zapier secret storage

const response = await fetch(
  `https://api.github.com/repos/${owner}/${repo}/contents/${path}`,
  {
    headers: {
      'Authorization': `token ${token}`,
      'Accept': 'application/vnd.github.v3+json'
    }
  }
);

const data = await response.json();
const content = Buffer.from(data.content, 'base64').toString('utf-8');
const sha = data.sha;

output = { current_content: content, sha: sha };
```

### Step 4: Action — Code by Zapier (Run JavaScript) — Update bridge.md

Purpose: Replace the NEXT PROMPT TO RUN block and append to history.

```javascript
const content = inputData.current_content;
const sha = inputData.sha;
const prompt_block = inputData.prompt_block;
const history_entry = inputData.history_entry;
const timestamp = inputData.timestamp;
const token = inputData.github_token;

// Replace between START and END markers
const start_marker = '<!-- START PROMPT -->';
const end_marker = '<!-- END PROMPT -->';
const start_idx = content.indexOf(start_marker) + start_marker.length;
const end_idx = content.indexOf(end_marker);

let updated = content.substring(0, start_idx) +
  '\n\n' + prompt_block + '\n\n' +
  content.substring(end_idx);

// Update STATUS table
updated = updated.replace(
  /Last prompt received \| .*/,
  `Last prompt received | ${timestamp}`
);
updated = updated.replace(
  /Zapier connected \| .*/,
  'Zapier connected | true'
);

// Append to PROMPT HISTORY (after "Most recent first" comment)
const history_marker = '<!-- Most recent first -->';
updated = updated.replace(
  history_marker,
  history_marker + '\n' + history_entry
);

// Write back via GitHub API
const owner = 'aarontmaher';
const repo = 'Chat-gpt';
const path = 'bridge.md';

const body = JSON.stringify({
  message: `[zapier] prompt queued: ${inputData.scope}`,
  content: Buffer.from(updated).toString('base64'),
  sha: sha,
  branch: 'main'
});

const response = await fetch(
  `https://api.github.com/repos/${owner}/${repo}/contents/${path}`,
  {
    method: 'PUT',
    headers: {
      'Authorization': `token ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/vnd.github.v3+json'
    },
    body: body
  }
);

const result = await response.json();
output = { success: response.ok, commit_sha: result.commit?.sha || 'failed' };
```

### Step 5 (Optional): Action — Filter

Only proceed if Step 4 succeeded (`success` is `true`). Otherwise stop.

---

## 3. Authentication & Setup Guide (for Aaron)

### Prerequisites

- GitHub account with write access to `aarontmaher/Chat-gpt`
- Zapier account (free tier supports 5 Zaps, 100 tasks/month — sufficient)

### Step-by-step setup

#### A. Create a GitHub Personal Access Token (PAT)

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Name: `zapier-grapplingmap`
4. Expiration: 90 days (set a calendar reminder to rotate)
5. Scopes: check **`repo`** (full control of private repositories)
6. Click **Generate token**
7. **Copy the token immediately** — you won't see it again

#### B. Create the Zapier Zap

1. Go to https://zapier.com and sign in
2. Click **Create Zap**
3. **Trigger:**
   - Search for **"Webhooks by Zapier"**
   - Choose **"Catch Hook"**
   - Click Continue (no setup needed)
   - Copy the webhook URL shown — save it somewhere safe
   - Click **Test trigger** (skip for now, we'll test later)

4. **Action 1 — Format prompt:**
   - Search for **"Code by Zapier"**
   - Choose **"Run JavaScript"**
   - Input Data: map `type`, `scope`, `goal`, `prompt_body`, `sign_off`, `timestamp` from the trigger
   - Code: paste the JavaScript from Step 2 above
   - Test this step

5. **Action 2 — Read bridge.md:**
   - Another **"Code by Zapier"** → **"Run JavaScript"**
   - Add `github_token` as an input field, paste your PAT as the value
   - Code: paste the JavaScript from Step 3 above
   - Test this step

6. **Action 3 — Write bridge.md:**
   - Another **"Code by Zapier"** → **"Run JavaScript"**
   - Map inputs from previous steps + `github_token`
   - Code: paste the JavaScript from Step 4 above
   - Test this step

7. **Turn on the Zap**

#### C. Test the webhook

Send a test POST from Terminal:

```bash
curl -X POST "YOUR_ZAPIER_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CODE",
    "scope": "Test prompt",
    "goal": "Verify Zapier integration works",
    "prompt_body": "This is a test prompt. No action needed.",
    "sign_off": "— FROM: CLAUDE CHAT",
    "timestamp": "2026-03-19T15:00:00Z"
  }'
```

Then check:
1. Zapier task history shows success
2. `bridge.md` on GitHub has the prompt in the NEXT PROMPT TO RUN block
3. STATUS table shows updated timestamp

#### D. Connect Claude Chat

Once tested, provide Claude Chat with:
- The Zapier webhook URL
- The prompt format specification (Section 1 above)
- Instruction: "When I say 'send to bridge', format the prompt and POST to this webhook"

---

## 4. Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| 409 Conflict | bridge.md was updated between read and write | Zap retries automatically (Zapier built-in) |
| 401 Unauthorized | PAT expired or revoked | Regenerate PAT, update in Zapier |
| 422 Unprocessable | SHA mismatch (file changed) | Zapier auto-retry handles this |
| Malformed prompt | Missing TYPE/SCOPE/GOAL fields | Code by Zapier step validates; Zap stops on error |
| Rate limit (403) | Too many API calls | Free tier: 5,000 req/hr — not a concern at this volume |

### Logging

- Zapier Task History shows every run with input/output
- bridge.md PROMPT HISTORY table provides an audit trail
- GitHub commit history shows every bridge.md update with `[zapier]` prefix

---

## 5. Operational Notes

### What Zapier does NOT do
- Trigger the pipeline (watch-and-push.sh)
- Execute prompts — Code agent does this manually
- Modify any file other than bridge.md
- Create branches or PRs

### Prompt lifecycle
1. Claude Chat formats prompt → POSTs to webhook
2. Zapier writes prompt to bridge.md `NEXT PROMPT TO RUN` block
3. Code agent opens bridge.md, reads prompt, executes it
4. Code agent clears `NEXT PROMPT TO RUN` block and updates STATUS when done

### Cost
- Zapier free tier: 100 tasks/month, 5 Zaps — more than enough
- GitHub API: free for public repos, 5,000 requests/hour
- No other costs

### Security
- GitHub PAT stored in Zapier's encrypted secret storage
- Webhook URL is unguessable (random string) but should not be shared publicly
- PAT has `repo` scope — rotate every 90 days
- Consider switching to fine-grained PAT (Contents: Read and write) for least privilege

---

## 6. Future Enhancements (not in scope now)

- Slack/Discord notification when prompt lands in bridge.md
- Two-way sync: Code agent POSTs completion status back via second webhook
- Zapier → GitHub Actions trigger for automated pipeline runs
- Fine-grained PAT with minimal permissions
