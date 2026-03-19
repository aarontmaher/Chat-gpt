# GrapplingMap — CLAUDE.md
# Single source of truth for all agents (Chat/Cowork/Code/Aaron/ChatGPT).
# Update after every major decision or state change. Read at start of every session.
# Last updated: 2026-03-19
---
## PROJECT
| Item | Value |
|------|-------|
| Live site | https://aarontmaher.github.io/Chat-gpt/ |
| Repo | git@github.com:aarontmaher/Chat-gpt.git |
| Local path | /Users/aaronmaher/Chat-gpt/ |
| Dev server | python3 -m http.server (check current port in watch-and-push.sh) |
| Mindomo map | https://www.mindomo.com/outline/8acaf2c87cd24bd8a647054f1e427e4c |
| Bridge file | ~/GrapplingMap/bridge.md |
| Pipeline runner | ~/Chat-gpt/tools/watch-and-push.sh (launchd auto-start on login) |
| Pipeline converter | ~/Chat-gpt/tools/opml_to_sections.py |
| Exports path | ~/GrapplingMap/exports/grappling.opml (single source of truth) |
| Live footage root | ~/GrapplingMap/live-footage/ |
| Results feed | ~/Chat-gpt/results.md (Code writes after every task via tools/write-result.sh) |
---
## MISSION
Build a demo-ready proof of product:
- Website renders a Reference tree + 3D weighted network graph from Mindomo OPML pipeline.
- Site must be stable: Reference/3D sync works, filters work, console errors zero, pipeline reliable.
- After proof-of-product, remaining work = filling technique text + attaching instructional/live media.
---
## ROLE SPLIT (NON-NEGOTIABLE)
| Role | Responsibility |
|------|---------------|
| Claude Chat | Prompt writer + coordinator ONLY. Read-only monitoring allowed (refresh/scroll/read). No state-changing clicks. No JS. |
| Cowork | Mindomo UI edits + verification checklists. UI-only. No JS ever. Does not invent technique names. |
| Code | Repo/website implementer. Edits, commits, pushes only. Verifies localhost before pushing. Plain English paste-backs. |
| Aaron | All decisions + all technique names + all OT context labels. |
| ChatGPT | OPML analysis, prompt QA, technical advice. No direct edits. |
### Claude Chat:
- Read-only monitoring: may reload/scroll/read live site passively.
- No state-changing clicks, no JS, no DevTools commands.
- Never invents BJJ technique names or OT context labels.
- If a prompt needs technique names or labels: ask Aaron first, wait, then issue prompt.
### Code paste-back format:
Every paste-back must include a PLAIN ENGLISH SUMMARY section:
- What changed (one sentence, no jargon)
- What decisions Aaron needs to make (simple questions only)
- What to check on the live site (one action)
### Cowork:
- Mindomo UI-only. No JavaScript tools anywhere ever.
- Does not invent technique names or content.
- May reorganize existing nodes (rename, move, delete duplicates, add empty schema headings).
- For verification: may access live site for binary pass/fail checklists only. No exploration, no JS.
- Dismiss popups: prefer Cancel/close. If a popup blocks work, report it and stop.
- Export goes to ~/Downloads/ — always report "needs pipeline copy".
### Cowork paste-back format:
Every paste-back must include a PLAIN ENGLISH SUMMARY section:
- What was fixed (e.g. "Renamed 3 misplaced nodes")
- What was flagged (e.g. "Found a node with wrong spelling — needs Aaron to confirm")
- Nothing technical — write as if explaining to someone who doesn't code
### Aaron provides:
- ALL BJJ technique names and content.
- ALL OT context labels (left side of arrow).
- ALL canonical name and destination decisions.
---
## HARD RULES (no exceptions)
1. Claude never invents technique names. Aaron adds all content directly in Mindomo.
2. No-Gi only. Never add Gi techniques (bow and arrow choke, collar choke = Gi examples).
3. Cowork UI-only always. No JavaScript anywhere.
4. Knee on belly = PERMANENT HOLD. Never redirect, never delete, always flag.
5. OT format = "Context label -> ExactCanonicalNodeName". Single arrow, leaf only.
6. Bare arrows (no left label) = FLAG. Never parse as graph edges.
7. Never delete unless confirmed true duplicate or empty shell already replaced.
8. Technique content = Aaron's domain. Ask Aaron before any content prompt.
9. Exits / Transitions = instructional text only. NOT graph edges. Never parsed.
---
## SCHEMA (LOCKED)
### A) Dominant Positions
- Perspectives: Attacker / Defender
- Headings (6): Setups/Entries, Control, Offence, Defence/Escapes, Submissions, Offensive transitions
- Canonical: Turtle, Front Headlock, Mount, Side Control, North South, Back Control
### B) Guard
- Perspectives: Passer / Guard player
- Headings (6): Setups/Entries, Control, Offence, Defence/Escapes, Submissions, Offensive transitions
- Half guard is canonical and must remain canonical.
- Canonical (19): Shin pin, Supine Guard, J point, Closed Guard, Headquarters,
  Quarter guard, Half Guard Passing, Butterfly guard, Half butterfly,
  Knee shield half guard, K guard, De la riva, Reverse de la riva,
  Butterfly ashi, Outside ashi, X guard, Single leg X, Seated Guard, Half guard
### C) Scrambles
- Perspectives: Initiative / Defensive
- Headings (6): Setups/Entries, Control, Offence, Defence/Escapes, Submissions, Offensive transitions
- Exits / Transitions = instructional only. NOT graph edges.
- Canonical: Berimbolo, Crab ride, Grounded 50/50
### D) Wrestling
- Perspectives: Attacker / Defender
- Headings (6): Setups/Entries, Control, Offence, Defence (NOT Defence/Escapes), Submissions, Offensive transitions
- Canonical shots: Head inside single leg, Head outside single leg, Double leg, Low ankle
- Shots container: "Shots" (renamed from "Shots (NEW)")
### E) Hand Fighting (NEW)
- Perspectives: You / Opponent
- Headings (5 - NO Submissions): Setups/Entries, Control, Offence, Defence, Offensive transitions
- Sub-nodes: Outside tie, Inside tie, Collar tie, Underhook, Overhook, 2-on-1, Over/Under
### F) Wrestling Bodylock
- Perspectives: Attacker / Defender + 6 headings (Defence not Defence/Escapes)
- Sub-positions (canonical when they have perspective layers, detected at any depth):
  Side bodylock (renamed from Wrestling side bodylock), Wrestling rear bodylock
---
## TRANSITION RULES (LOCKED)
Format: "Context-specific label -> ExactCanonicalNodeName"
- Single arrow. Leaf nodes only. Left side = context. Right side = exact canonical name.
- Bare arrows (no left label) = FLAG, never parse as edges.
- Mojibake: a†' = -> (pipeline handles automatically)
Canonical destinations:
- Dominant Positions: Turtle, Front Headlock, Mount, Side Control, North South, Back Control
- Scrambles: Berimbolo, Crab ride, Grounded 50/50
- Wrestling: Head inside single leg, Head outside single leg, Double leg, Low ankle,
  Wrestling bodylock, Side bodylock, Wrestling rear bodylock
- Guard: all 19 listed above
NOT canonical (hold): Knee on belly (permanent), Saddle (TBD), any node without perspective layer.
---
## DATA RULES
- No-Gi only. Permanent.
- Notes: explanations -> child node named "Notes" under relevant item.
- Media: "Instructional video" / "Live video" as children of technique. Inline buttons on row.
- Delete: ONLY true duplicates (same name + same parent) + empty replaced shells.
- OT structure: Offensive transitions = arrow-format leaf edges ONLY.
  If technique/positional content found under OT: move to Offence (attacks) or Control (positions).
  Move entire subtree as one unit. Aaron reorganises later.
---
## WEBSITE SPEC (LOCKED)
Key generation (KEY_VERSION=2): section|position|perspective|heading|itemLabel
Canonical detection: isCanonical = has perspective layer child (at any nesting depth)
Boot sequence: loadState -> initDataFromSections -> buildSections -> markBuiltOut -> updateStats -> initGraph3D
Built-out: >=3 canonical headings with >=1 real technique. Excludes Hand Fighting.
Expected built-out (8): J point, K guard, Quarter guard, Supine Guard, Mount, Turtle, Berimbolo, Grounded 50/50
3D Graph:
- Canonical positions only. in_network = participates in >=1 transition edge.
- Edge weight: count occurrences of same (contextLabel -> destination) pair.
- Node size: indegree + 1.
- Orphans: shown at reduced opacity (never hidden).
- Auto-rotation on load, stops permanently on user interaction.
- Hub centering: high-indegree nodes pulled toward centre.
Reference panel:
- Heading click: scroll + yellow highlight ~2s + expand only. No SELECTED_NODE change.
- Technique selection persists across tabs, clears on filter/collapse/Esc.
Filters: DRILLING/LEARNED/MY GAME (position-level). MY GAME = union of both.
Empty state: graph visible at low opacity + overlay message.
Progress: localStorage, KEY_VERSION=2, clean reset on mismatch.
---
## LIVE FOOTAGE SYSTEM (Phase 1)
Folder: ~/GrapplingMap/live-footage/<section>/<position>/<perspective>/<heading>/<technique>/
COMMIT_MIN = 5 clips per folder. Playlists per technique (not per position).
Non-destructive: additive only. Orphan folders with videos: keep. Empty: trash via --hard-delete only.
Workflow:
1. Aaron exports clips from CapCut -> drops in correct technique folder (search Finder)
2. bash ~/GrapplingMap/tools/sync-live-footage.sh --dry-run -> preview
3. >=5 clips: creates playlist + updates live-playlists.json + outputs mindomo_live_patch.md
4. Cowork applies patch (adds "Live video" child under technique node)
5. Site shows Live footage button if playlist ID exists
Scripts:
- ~/GrapplingMap/tools/live_folders_from_opml.py (auto-runs after each pipeline push)
- ~/GrapplingMap/tools/sync-live-footage.sh (--dry-run / --apply)
- ~/GrapplingMap/live-footage/live-index.json (manifest: 574 entries)
- ~/Chat-gpt/live-playlists.json (keyed by technique path key)
---
## RESULTS FEED
- ~/Chat-gpt/results.md — auto-updated by pipeline after each push.
- Contains LATEST-RESULT markers for programmatic reading.
- Siri integration: archived (docs/archive/), not active. Scripts remain in tools/siri/ for future use.
DAILY PASTE-BACK WORKFLOW:
1. Open results.md (raw.githubusercontent.com/aarontmaher/Chat-gpt/main/results.md)
2. Copy LATEST-RESULT block
3. Paste to Claude Chat in one message
That's it — Chat reads Code + Cowork results from one paste.
---
## HOTKEY WORKFLOW (Raycast — install with: brew install --cask raycast)
Scripts: ~/Chat-gpt/tools/hotkeys/raycast/
- Cmd+Shift+G: copy next Code prompt to clipboard (from results.md NEXT-PROMPT block)
- Cmd+Shift+S: show pipeline status (LATEST-RESULT from results.md)
- Cmd+Shift+B: open bridge.md in default editor
Setup: Raycast prefs → Extensions → Script Commands → Add Directory → ~/Chat-gpt/tools/hotkeys/raycast/
No Zapier, no API, no Siri needed. Works offline (except GitHub fetch for status).
---
## WORKFLOW (LOCKED — OPML-ONLY)
Source of truth: grappling.opml in git (repo file)
- Repo path: ~/Chat-gpt/grappling.opml
- Pipeline input (canonical): ~/GrapplingMap/exports/grappling.opml
Mindomo: reference viewer only — NOT an editor
HOW CHANGES ARE MADE:
  Aaron tells Chat → Chat writes OPML-PATCH prompt → Code edits grappling.opml
  → pipeline runs → site updates shortly after push → Chat verifies
  No manual edits to OPML except via Code patch prompts.
PATCH REQUEST FORMAT:
  Aaron: "Add [text] to [Section > Position > Perspective > Heading]"
  Chat: writes OPML-PATCH-NN prompt with exact path + text
  Code: edits grappling.opml, runs pipeline, commits, pushes
WHAT IS NOT ALLOWED:
  - "Add content in Mindomo" (Mindomo is not the editor)
  - "Export OPML from Mindomo" as primary workflow
  - Cowork for structural edits (retired)
COWORK STATUS: RETIRED
  Re-enable only if explicitly requested for rare Mindomo UI task
---
## OPML PIPELINE
Single source of truth: ~/GrapplingMap/exports/grappling.opml
Watcher copies newest Downloads OPML -> exports/ on each run.
All tools must read from exports/, never raw Downloads files.
tail -3 ~/Chat-gpt/tools/watch-and-push.log
git -C ~/Chat-gpt log -1 --format="%h %s %ci"
---
## CURRENT SNAPSHOT
# Regenerate after major pipeline runs. Run DIAG on localhost after hard refresh.
# Do NOT hardcode counts here - they drift.
Last updated: 2026-03-19
Pipeline: stable, NO_DEST=0, HELD=1 (Knee on belly bare arrow)
Transition edges: 36 (Python). in_network: 36.
Schema verified: all Guard (12/12), Wrestling sub-positions, Scrambles
OT restructure: Half Guard Passing, Reverse de la riva, K guard, Grounded 50/50 all cleaned
Built-out set (11): J point, K guard, Quarter guard, Supine Guard, Mount, Turtle,
  Berimbolo, Grounded 50/50, Wrestling bodylock, Back Control, Crab ride
Live footage: 574 folders created, sync script ready, Phase 2 (YouTube) pending
CLAUDE.md: live, commit 50d9d9e
---
## PENDING TASKS
# Update this section every session.
Code: PIPE-LIVE-01B (verify live button wiring), SITE-BATCH-07 (done)
Cowork: RETIRED — patch system + Chat verification replaces Cowork for structural work.
Aaron decisions: Saddle canonical name TBD
Half guard: RESOLVED — created 2026-03-19 by Cowork. Now 19 Guard canonical positions.
Guard OT status: 16/19 positions have zero OT lines. Only HGP + RDLR have edges. Content needed from Aaron.
OPML audit (2026-03-19): 3592 paths, 808 technique leaves, 48 canonical, 27 OT leaves,
  0 non-standard attrs, fingerprint cb7b55fb. Safe to drop Mindomo as editor: YES.
NEXT SESSION PRIORITIES:
1. Add OT lines to Guard positions (Aaron tells Chat which + labels)
2. Add technique content via OPML patches (no Mindomo)
3. Test live footage: drop first real clip → run dry-run
4. Record proper demo video
---
## LOCKED DECISIONS
| Decision | Resolution |
|----------|-----------|
| Technique content | Aaron only. Claude NEVER invents. |
| No-Gi | Confirmed permanent. |
| Half guard | Created 2026-03-19 by Cowork. Now canonical (19 Guard positions). |
| Guard canonical count | 19 (Half guard added 2026-03-19) |
| Knee on belly | PERMANENT HOLD. Never redirect/delete. |
| Saddle canonical | Not defined. Hold. |
| Wrestling heading | "Defence" (not "Defence / Escapes") |
| Guard heading | "Defence / Escapes" |
| Side bodylock name | "Side bodylock" |
| Shots container | "Shots" |
| 2-on-1 canonical | "2-on-1 (You)" |
| KEY_VERSION | 2 |
| Built-out filter | Excludes Hand Fighting |
| Built-out count | 11 positions (verified 2026-03-19) |
| COMMIT_MIN | 5 videos per technique folder |
| Playlists | Per technique |
| OT nested content | Move to Control as-is |
| Chest to chest (HGP) | Moved to Control |
| Diving to crab x (RDLR) | Moved to Control |
| Opponent backsteps (K guard) | Moved to Control |
| Grounded 50/50 OT | "Exit grounded 50/50 to side control -> Side Control" |
| Exits / Transitions | NOT graph edges |
| HGP Passer OT | "Half guard passing to mount (knee slide) → Mount" |
| RDLR GP OT | "Reverse de la riva inversion to crab ride → Crab ride" |
| Boot sequence | loadState->initDataFromSections->buildSections->markBuiltOut->updateStats->initGraph3D |
| Live footage shuffle | youtubePlaylistUrl() adds shuffle=1&playnext=1 (commit 6630276) |
| Results feed | results.md written after every Code task. Schema: prompt_id, timestamp, summary, edges, commit, flags. |
| Siri integration | Archived — not needed yet. results.md feed active. Scripts in tools/siri/ for future. |
| OPML-only workflow | Active. grappling.opml = source of truth. Mindomo = viewer only. |
| Cowork retired | 2026-03-19. Patch system replaces all structural Cowork work. |
| OPML audit | Passed 2026-03-19. Fingerprint: cb7b55fbfcf6e601f49ec920f652dcf5 |
---
## AUTO-MERGE (claude/** branches)
Auto-merge is enabled for PRs opened from branches matching `claude/**`.
- Merge method: squash (falls back to merge if squash is disallowed).
- Fork PRs are ignored for security.
- Pre-req: Aaron must enable Settings -> General -> Pull Requests -> "Allow auto-merge" = ON.
- Verify: open a PR from a `claude/test-automerge` branch — the PR should show "Auto-merge enabled" badge.
- Workflow file: `.github/workflows/auto-enable-automerge.yml`
---
## PROMPT-ID LOG
| ID | Task | Status |
|----|------|--------|
| SITE-BATCH-01 to 06 | Website fixes + demo hardening | done |
| SITE-OVERNIGHT-02 to 03 | Overnight export processing | done |
| PIPE-01 to 08 | Pipeline copies + re-runs | done |
| PIPE-09 | Pipeline + CLAUDE.md | done b954aa6 |
| PIPE-10 | CLAUDE.md update + GUARD-03 monitor | running |
| PIPE-LIVE-01A | 574 live footage folders | done 93c5b88 |
| PIPE-LIVE-01B | live-playlists.json + button | pending verify |
| COWORK-BATCH-01 to 07 | Schema + OT fixes | done |
| COWORK-OVERNIGHT-02 to 03 | Schema + OT verify | done |
| WREST-01 to 07 | Wrestling fixes | done |
| DP-01 to 06 | Dominant Positions fixes | done |
| SCR-01 to 04 | Scrambles fixes | done |
| GUARD-01 | Guard OT check | done |
| GUARD-02 | HGP + RDLR bare OT flags | done (fixed by GUARD-03) |
| GUARD-03 | Add 2 new OT lines (HGP→Mount, RDLR→Crab ride) | done |
| SITE-CLAUDE-MD | Create this file | done 50d9d9e |
| SITE-BATCH-07 | Built-out fix + live playlists | done |
| SITE-BATCH-08 | UX polish + DIAG + canonical logging | done |
| LIVE-SHUFFLE-01 | YouTube shuffle URL helper | done 6630276 |
| RESULTS-WRITER-01 | results.md feed + write-result.sh + pipeline hook + site fetch | done |
| SIRI-INTEGRATION-01 | Siri shortcuts + voice Claude template | done |
| SIRI-SHORTCUTS-02 | Shortcut install page | done 8a11b9a |
| DEBRIEF-FORMAT-01 | Plain English debrief format | done |
| SITE-OVERNIGHT-05 | Full overnight batch | this |
| GH-AUTOMERGE-01 | Auto-merge workflow for claude/** PRs | done 4afba62 |
---
## SIGN-OFF TAGS
Claude Chat: -- FROM: CLAUDE CHAT
Cowork: -- FROM: COWORK
Code: -- FROM: CODE
Aaron: -- FROM: AARON
ChatGPT: -- FROM: CHATGPT

---
## OPML-ONLY HARDENING (OPML-WORKFLOW-HARDEN-01)
- Canonical path: ~/GrapplingMap/exports/grappling.opml (only source)
- Fingerprint: md5 logged as OPML_FINGERPRINT on every pipeline run
- Watcher: OPML_SOURCE + OPML_MTIME + OPML_FINGERPRINT logged; lock file prevents overlap
- Patch system: ~/GrapplingMap/tools/apply_patches.py
  --dry-run (default), --apply, archive before every apply,
  stale-guard (abort if OPML older than last patch), deletion threshold (>5 = abort)
- Lock file: ~/GrapplingMap/exports/.pipeline_lock (watcher + patches share)
- Mindomo exports: optional "challenge" inputs. Never silently overwrite canonical.
  Downloads copy only if newer AND change event from Downloads.
---
## SESSION LOG — 2026-03-19
### New learnings:
COWORK RULE ADDITION: Schema verification = visual expand + scroll only.
Using find tool or read_page for programmatic search is a rule violation.
Call it out each time.
TECHNIQUE CONTENT INCIDENT (DP-06): Claude issued a prompt containing invented
technique names including Gi techniques (bow and arrow choke, collar choke)
and a non-existent technique (straight jacket choke). All were removed from Mindomo.
Rule hardened permanently: Claude never provides technique names in any prompt.
This applies to Chat, Code, and Cowork.
LIVE FOOTAGE: 574 technique folders created. Commit 93c5b88.
Phase 1 operational. Phase 2 (YouTube upload) pending.
SCHEMA FULLY VERIFIED (2026-03-19):
- All 12 Guard positions: Passer + Guard player + 6 headings correct.
- Berimbolo + Crab ride + Grounded 50/50: all verified.
- Side bodylock + Wrestling rear bodylock: both verified.
- OT restructure complete: HGP, RDLR, K guard, Grounded 50/50 all cleaned.
- 0 schema flags remaining.
BARE OT DESTINATIONS STILL PENDING (Aaron to provide context labels):
- Half Guard Passing Passer OT: bare "Mount"
- Reverse de la riva Guard player OT: bare "Crab ride"
Note: Cowork's find tool reported these as not found — may have been cleaned
in OT restructure. Code to verify after next pipeline run.
DEMO GIF: ~/Downloads/grappling-map-demo-v2.gif (235KB).
Shows: rotating graph, BUILT-OUT filter, Turtle panel, REF navigation.
Graph shows: Back Control, Turtle, Mount, Berimbolo, Side Control,
North South, Front Headlock, Crab ride all visible with edges. Demo-ready.
CLAUDE.md UPDATE RULE: Read CLAUDE.md at start of every session.
Update it at least once per session with new decisions, fixes, and state.
