# GrapplingMap — Siri Shortcuts Integration

## Overview
Four Siri Shortcuts connect Aaron's voice to the GrapplingMap pipeline.
Siri = trigger/executor. Claude voice chat = brain/decision maker.

---

## Shortcuts to create (step-by-step for each)

### Shortcut 1: "GrapplingMap Status"
**Trigger:** "Hey Siri, GrapplingMap Status"

**What it does:**
1. Fetches `https://raw.githubusercontent.com/aarontmaher/Chat-gpt/main/results.md`
2. Extracts content between `<!-- LATEST-RESULT-START -->` and `<!-- LATEST-RESULT-END -->`
3. Speaks the result aloud via text-to-speech:
   "Last task: [prompt_id]. [summary]. Edges: [edges]. Commit: [commit]."

**Setup:**
1. Open **Shortcuts** app → tap **+** → name it "GrapplingMap Status"
2. Add action: **Get Contents of URL**
   - URL: `https://raw.githubusercontent.com/aarontmaher/Chat-gpt/main/results.md`
3. Add action: **Get Text from Input**
4. Add action: **Match Text**
   - Pattern: `LATEST-RESULT-START -->([\s\S]*?)<!-- LATEST-RESULT-END`
5. Add action: **Get Group from Matched Text** → Group 1
6. Add action: **Speak Text** → speak the matched content

> **Alternative (simpler):** Use the **Run Script over SSH** action to call `bash ~/Chat-gpt/tools/siri/get-status.sh` on your Mac, then **Speak Text** with the output.

---

### Shortcut 2: "GrapplingMap Send Prompt"
**Trigger:** "Hey Siri, Send GrapplingMap Prompt"

**What it does:**
1. Reads text from clipboard (Claude voice chat outputs the prompt, you copy it)
2. POSTs clipboard content to Zapier webhook URL
3. Speaks "Prompt sent to Code"

**Setup:**
1. Open **Shortcuts** app → tap **+** → name it "Send GrapplingMap Prompt"
2. Add action: **Text** → paste your Zapier webhook URL (update after Zapier setup)
3. Add action: **Set Variable** → name it `WebhookURL`
4. Add action: **Get Clipboard**
5. Add action: **Get Contents of URL**
   - URL: `WebhookURL` variable
   - Method: **POST**
   - Headers: `Content-Type: application/json`
   - Request Body: JSON → key `prompt`, value: **Clipboard** variable
6. Add action: **Speak Text** → "Prompt sent"

---

### Shortcut 3: "GrapplingMap Run Pipeline"
**Trigger:** "Hey Siri, Run GrapplingMap Pipeline"

**What it does:**
1. POSTs to a second Zapier webhook that triggers `watch-and-push.sh` remotely
2. Speaks "Pipeline triggered"

**Note:** Requires one of:
- **SSH from iPhone to Mac** (Mac must be on same network or have static IP/ngrok)
- **Second Zap:** Webhook → SSH to Mac → `bash ~/Chat-gpt/tools/watch-and-push.sh`

**Setup (SSH approach — simplest):**
1. Open **Shortcuts** app → tap **+** → name it "Run GrapplingMap Pipeline"
2. Add action: **Run Script over SSH**
   - Host: your Mac's IP (or ngrok URL)
   - User: your Mac username
   - Authentication: SSH Key (set up in advance)
   - Script: `bash ~/Chat-gpt/tools/watch-and-push.sh`
3. Add action: **Speak Text** → "Pipeline triggered"

**Setup (Zapier approach — future):**
- Documented in `zapier-integration.md` Part 2.

---

### Shortcut 4: "GrapplingMap What's Next"
**Trigger:** "Hey Siri, What's Next GrapplingMap"

**What it does:**
1. Fetches CLAUDE.md from GitHub
2. Extracts PENDING TASKS section
3. Speaks the first 3 pending items aloud

**Setup:**
1. Open **Shortcuts** app → tap **+** → name it "What's Next GrapplingMap"
2. Add action: **Get Contents of URL**
   - URL: `https://raw.githubusercontent.com/aarontmaher/Chat-gpt/main/CLAUDE.md`
3. Add action: **Get Text from Input**
4. Add action: **Match Text**
   - Pattern: `## PENDING TASKS([\s\S]*?)---`
5. Add action: **Get Group from Matched Text** → Group 1
6. Add action: **Speak Text** → speak matched content (first 500 chars)

> **Alternative:** Use **Run Script over SSH** → `bash ~/Chat-gpt/tools/siri/get-next.sh`

---

## Voice Claude Integration

### How to use Claude voice chat with these shortcuts:
1. **"Hey Siri, GrapplingMap Status"** → hear what happened
2. Open Claude voice chat → paste `docs/voice-claude-template.md` → speak instructions
3. Claude voice generates the prompt text
4. Copy the prompt text
5. **"Hey Siri, Send GrapplingMap Prompt"** → fires to Zapier → Code picks up from bridge.md

### Hands-free flow while rolling/editing:
```
"Hey Siri GrapplingMap Status"       → hear results
"Hey Siri What's Next GrapplingMap"  → hear pending tasks
Open Claude voice → discuss → get prompt
"Hey Siri Send GrapplingMap Prompt"  → fired
Back to rolling/editing
```

---

## iOS Shortcuts Setup Notes
- All shortcuts use **Get Contents of URL** action for HTTP requests
- Zapier webhook URL stored as a **Text** action at top of each shortcut (easy to update)
- GitHub raw URLs are public — no PAT needed for reads
- For SSH shortcuts: set up SSH key pair between iPhone and Mac first
- Test each shortcut from the Shortcuts app before voice testing
- Siri may require you to run a shortcut manually once before it recognises the voice trigger
