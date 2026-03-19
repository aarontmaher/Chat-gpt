# GrapplingMap — CLAUDE.md
# Single source of truth for all agents (Chat/Cowork/Code/Aaron/ChatGPT).
# Update after every major decision or state change.
# Do NOT bake in counts, node totals, edge numbers, or physics constants — these drift.
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
| Exports path | ~/GrapplingMap/exports/grappling.opml (single source of truth — always use this) |
| Live footage root | ~/GrapplingMap/live-footage/ |
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
| Code | Repo/website implementer. Edits, commits, pushes only. Verifies localhost before pushing. |
| Aaron | All decisions + all technique names + all OT context labels. |
| ChatGPT | OPML analysis, prompt QA, technical advice. No direct edits. |
### Claude Chat rules:
- Read-only monitoring allowed: may reload/scroll/read live site passively.
- No state-changing clicks, no JS execution, no DevTools commands.
- Never invents BJJ technique names or OT context labels.
- Never issues prompts without sufficient evidence.
- If a prompt needs technique names or OT labels: ask Aaron first, wait, then issue prompt.
### Cowork rules:
- Mindomo UI-only. No JavaScript tools anywhere ever.
- Does not invent technique names or content.
- May reorganize existing nodes (rename, move, delete duplicates, add empty schema headings).
- For verification: may access live site for binary pass/fail checklists only. No exploration, no JS.
- Dismiss popups: prefer Cancel/close. If a popup blocks work, report it and stop.
- Export goes to ~/Downloads/ — always report "needs pipeline copy".
### Aaron provides:
- ALL BJJ technique names and content.
- ALL OT context labels (left side of arrow in transition lines).
- ALL canonical name and destination decisions.
---
## HARD RULES (no exceptions)
1. Claude never invents technique names. Aaron adds all content directly in Mindomo.
2. No-Gi only. Never add Gi techniques (bow and arrow choke, collar choke = Gi examples).
3. Cowork UI-only always. No JavaScript anywhere.
4. Knee on belly = PERMANENT HOLD. Never redirect, never delete, always flag.
5. OT format = "Context label → ExactCanonicalNodeName". Single arrow, leaf only.
6. Bare arrows (no left label before →) = FLAG. Never parse as graph edges.
7. Never delete unless confirmed true duplicate or empty shell already replaced.
8. Technique content = Aaron's domain. Ask Aaron before any content prompt.
9. Exits / Transitions = instructional text only. NOT graph edges. Never parsed as edges.
---
## SCHEMA (LOCKED)
### A) Dominant Positions
- Perspectives: Attacker / Defender (Defender = bottom player)
- Headings (6, exact): Setups/Entries, Control, Offence, Defence/Escapes, Submissions, Offensive transitions
- Canonical positions: Turtle, Front Headlock, Mount, Side Control, North South, Back Control
### B) Guard
- Perspectives: Passer / Guard player
- Headings (6, exact): Setups/Entries, Control, Offence, Defence/Escapes, Submissions, Offensive transitions
- Half guard is canonical — must remain canonical.
- Canonical positions (19):
  Shin pin, Supine Guard, J point, Closed Guard, Headquarters,
  Quarter guard, Half Guard Passing, Butterfly guard, Half butterfly,
  Knee shield half guard, K guard, De la riva, Reverse de la riva,
  Butterfly ashi, Outside ashi, X guard, Single leg X, Seated Guard, Half guard
### C) Scrambles
- Perspectives: Initiative / Defensive
- Headings (6, exact): Setups/Entries, Control, Offence, Defence/Escapes, Submissions, Offensive transitions
- Exits / Transitions = instructional only. NOT graph edges.
- Canonical positions: Berimbolo, Crab ride, Grounded 50/50
### D) Wrestling (general shots/takedowns)
- Perspectives: Attacker / Defender
- Headings (6, exact): Setups/Entries, Control, Offence, Defence (NOT Defence/Escapes), Submissions, Offensive transitions
- Canonical shot nodes: Head inside single leg, Head outside single leg, Double leg, Low ankle
- Shots container name: "Shots" (renamed from "Shots (NEW)")
### E) Hand Fighting (NEW) — inside Wrestling
- Perspectives: You / Opponent
- Headings (5 — NO Submissions): Setups/Entries, Control, Offence, Defence, Offensive transitions
- If Submissions heading present and empty: delete it. If has content: flag.
- Sub-nodes: Outside tie, Inside tie, Collar tie, Underhook, Overhook, 2-on-1, Over/Under
- HF Offensive transitions feeds shot Offensive transitions.
### F) Wrestling Bodylock (container canonical)
- Perspectives: Attacker / Defender + 6 headings (Defence not Defence/Escapes).
- General bodylock content stays at container level.
- Sub-positions are canonical when they have perspective layers.
  Current sub-positions: Side bodylock, Wrestling rear bodylock.
  Canonical detection must work at any nesting depth (not just direct children).
- Side bodylock renamed from "Wrestling side bodylock".
---
## TRANSITION RULES (LOCKED)
Format: "Context-specific label → ExactCanonicalNodeName"
- Single arrow only.
- Leaf nodes only (no children under transition line except Instructional video / Live video media).
- Left side: HOW/WHEN transition happens. NEVER a bare destination.
- Right side: exact canonical node name (case + spelling must match map exactly).
- Mojibake alias: â†' = → (opml_to_sections.py handles automatically).
### Confirmed canonical destinations:
- Dominant Positions: Turtle, Front Headlock, Mount, Side Control, North South, Back Control
- Scrambles: Berimbolo, Crab ride, Grounded 50/50
- Wrestling: Head inside single leg, Head outside single leg, Double leg, Low ankle,
  Wrestling bodylock, Side bodylock, Wrestling rear bodylock
- Guard: all 19 listed above
### NOT canonical — hold:
- Knee on belly: PERMANENT HOLD. Never redirect, never delete.
- Saddle: not defined yet. Hold until Aaron decides canonical name.
- Any node without a perspective layer child.
---
## DATA RULES (GLOBAL)
- No-Gi only. Permanent.
- Notes rule: explanations/examples → child node named "Notes" under relevant item (not peers).
- Media rule: "Instructional video" / "Live video" stay as children of technique item.
  Render as inline buttons on technique row. NOT standalone list rows.
- Deletion rule: delete ONLY true duplicates (same name + same parent) + empty shells already replaced.
- OT structure rule: Offensive transitions headings contain ONLY arrow-format leaf edges.
  If technique/positional content found under Offensive transitions:
  → Move to Offence (if attacks) or Control (if positional states).
  → Move entire subtree as one unit. Aaron reorganises further later.
- Example: prefix = belongs under Notes child, not a standalone Offensive transitions line.
- Duplicate dedup: pipeline handles identical sibling text in convert_node().
---
## WEBSITE SPEC (LOCKED)
### Key generation (KEY_VERSION=2)
Format: section|position|perspective|heading|itemLabel (normalized, lowercase, trimmed).
No migration on version mismatch — clean reset.
### Canonical position detection
isCanonical = has at least one direct perspective child
(Attacker, Defender, Passer, Guard player, You, Opponent, Initiative, Defensive).
Detection must work at any depth in OPML tree (not just top-level).
### Built-out spec
- Computed from SECTIONS data (not DOM).
- Position built-out if ≥3 canonical headings contain ≥1 real technique.
- Real technique = non-empty node, not in SCHEMA_NAMES, not media placeholder.
- Exclude Hand Fighting (You/Opponent schema) from built-out calculation.
- Fail-safe: if built-out set is empty → do NOT fade everything, log warning.
### 3D Graph
- Nodes: canonical positions only.
- in_network = participates in ≥1 valid transition edge.
- Edge direction: source context → canonical destination (one-way).
- Edge weight: count occurrences of same (contextLabel → destination) pair.
- Node size: indegree + 1.
- Orphan nodes: shown at reduced opacity (not hidden).
- Built-out filter: built-out = bright, not built-out = dimmed.
- Auto-rotation on load, stops on user interaction.
### Boot sequence (locked order)
1. loadState()
2. initDataFromSections() → window._techPositionMap
3. buildSections()
4. markBuiltOut() → window._builtOutMap
5. updateStats()
6. initGraph3D()
### Reference panel
- Heading click: scroll + yellow highlight ~2s + expand only. No SELECTED_NODE change.
- Technique click: opens detail view (name, status, Notes, media buttons inline).
- Technique selection: persists across tab switches, clears on filter/collapse/Esc.
- Breadcrumb: Position → Perspective → Heading always visible.
### 3D Panel
- SECTIONS-driven (not DOM).
- Shows: position name, section, IN/OUT counts, perspective toggle, headings + technique counts.
- Connections clickable → navigate Reference to source position.
### Filters
- DRILLING / LEARNED / MY GAME: position-level (show positions with ≥1 tracked technique).
- MY GAME = union of DRILLING + LEARNED.
- VIDEO: has Instructional video OR Live video child.
- BUILT-OUT: real content across ≥3 of 6 canonical headings.
- Empty state: graph stays visible at low opacity + overlay message.
### Progress
- localStorage per device. KEY_VERSION=2. Clean reset on version mismatch.
---
## LIVE FOOTAGE SYSTEM (Phase 1 — locked)
Concept: per-technique YouTube playlists.
Film rolling → export from CapCut → drop in folder → playlist created when ≥5 clips.
### Folder structure
~/GrapplingMap/live-footage/<section>/<position>/<perspective>/<heading>/<technique>/
Mirrors Mindomo path. Changes handled via manifest move detection — no auto-deletions.
### Rules
- COMMIT_MIN = 5 clips per technique folder before playlist is created.
- Playlists are per technique (not per position).
- Non-destructive: additive only. Never auto-delete folders, playlists, or Mindomo nodes.
- Orphan folders (removed from Mindomo):
  - Contains video files → keep (or move to _TRASH, never delete).
  - Empty → safe to trash via sync script --hard-delete flag only.
### Workflow
1. Aaron exports clips from CapCut → drops in correct technique folder (search Finder).
2. bash ~/GrapplingMap/tools/sync-live-footage.sh --dry-run → preview PENDING/COMMIT.
3. When ≥5 clips: script creates YouTube playlist + updates live-playlists.json + outputs mindomo_live_patch.md.
4. Cowork applies mindomo_live_patch.md (adds "Live video" child with playlist URL under technique node).
5. Site shows "▶ Live footage" button on technique row if playlist ID exists.
### Scripts
~/GrapplingMap/tools/live_folders_from_opml.py   — auto-runs after each pipeline push (fail-soft)
~/GrapplingMap/tools/sync-live-footage.sh         — --dry-run to preview, --apply to execute
~/GrapplingMap/live-footage/live-index.json       — manifest: nodeKey → folder path + clip count
~/Chat-gpt/live-playlists.json                    — keyed by technique path key (KEY_VERSION=2)
---
## OPML PIPELINE
Single source of truth: ~/GrapplingMap/exports/grappling.opml
Watcher copies newest Downloads OPML → exports/grappling.opml on each run.
Pipeline and all downstream tools must read from exports/, not raw Downloads files.
# Check watcher status
tail -3 ~/Chat-gpt/tools/watch-and-push.log
# Manual pipeline run
cp ~/Downloads/grappling*.opml ~/GrapplingMap/exports/grappling.opml
cd ~/Chat-gpt && python3 tools/opml_to_sections.py ~/GrapplingMap/exports/grappling.opml index.html
# Confirm last push
git -C ~/Chat-gpt log -1 --format="%h %s %ci"
---
## CURRENT SNAPSHOT
# Regenerate this section after major pipeline runs. Do not trust stale numbers.
# Run: open DIAG panel on localhost after hard refresh.
Last verified: 2026-03-19
Transition edges: 33 (Python) — check DIAG for current
NO_DEST warnings: 0
MALFORMED: 1 (bare → Knee on belly — HELD by design, not a bug)
Guard positions schema: 12/12 verified correct
Wrestling sub-positions: Side bodylock + Wrestling rear bodylock both verified
Scrambles: Berimbolo + Crab ride + Grounded 50/50 all verified
Built-out set (8): J point, K guard, Quarter guard, Supine Guard, Mount, Turtle, Berimbolo, Grounded 50/50
---
## PENDING TASKS (update regularly)
### Code queue
- PIPE-09: Process COWORK-OVERNIGHT-03 export
- PIPE-LIVE-01B: Verify live-playlists.json + Live footage button in index.html
### Cowork queue
- Bare OT context labels — awaiting Aaron:
  - Half Guard Passing Passer: bare "Mount" needs context label
  - Reverse de la riva Guard player: bare "Crab ride" needs context label
### Open decisions (Aaron)
- Context label for bare "Mount" (Half Guard Passing Passer OT)
- Context label for bare "Crab ride" (Reverse de la riva Guard player OT)
- K guard GP: "Transition to standard 50/50" + "Transition to saddle" moved to Control — Saddle canonical name TBD
---
## LOCKED DECISIONS (permanent — never re-debate)
| Decision | Resolution |
|----------|-----------|
| Technique content | Aaron adds all techniques. Claude NEVER invents names. |
| No-Gi only | Confirmed permanent. |
| Half guard | Canonical — must remain canonical. |
| Knee on belly | PERMANENT HOLD. Never redirect, never delete. |
| Saddle canonical name | Not defined — hold until Aaron decides. |
| Wrestling heading | "Defence" (not "Defence / Escapes") |
| Guard heading | "Defence / Escapes" (not "Defence") |
| Side bodylock name | "Side bodylock" (renamed from "Wrestling side bodylock") |
| Shots container name | "Shots" (renamed from "Shots (NEW)") |
| 2-on-1 canonical name | "2-on-1 (You)" — OT destination uses this exact name |
| KEY_VERSION | 2 — path-aware keys |
| Built-out filter | Excludes Hand Fighting (You/Opponent schema) |
| COMMIT_MIN | 5 videos per technique folder |
| Playlists | Per technique (not per position) |
| OT nested content | Move entire subtree to Control as-is. Aaron reorganises later. |
| Chest to chest (HGP) | Moved to Passer + Guard player Control |
| Diving to crab x (RDLR) | Moved to Passer + Guard player Control |
| Opponent backsteps (K guard) | Moved to Guard player Control |
| Grounded 50/50 OT | "Exit grounded 50/50 to side control → Side Control" |
| Exits / Transitions | Instructional text only. NOT graph edges. |
| Technique selection | Persists across tabs, clears on filter/collapse/Esc |
| in_network | Transition edges only (never structural hierarchy) |
| Boot sequence | loadState → initDataFromSections → buildSections → markBuiltOut → updateStats → initGraph3D |
---
## PROMPT-ID LOG (append always)
| ID | Task | Status |
|----|------|--------|
| SITE-BATCH-01 to 06 | Website fixes + demo hardening | done |
| SITE-OVERNIGHT-02 to 03 | Overnight export processing | done / running |
| PIPE-01 to 08 | Pipeline copies + re-runs | done |
| PIPE-09 | COWORK-OVERNIGHT-03 export | pending |
| PIPE-LIVE-01A | Live footage folder system 574 folders | done 93c5b88 |
| PIPE-LIVE-01B | live-playlists.json + button wiring | pending verify |
| COWORK-BATCH-01 to 07 | Schema + OT fixes | done |
| COWORK-OVERNIGHT-02 | Schema verify all sections | done |
| COWORK-OVERNIGHT-03 | OT restructure + Guard verify | done |
| WREST-01 to 07 | Wrestling fixes | done |
| DP-01 to 06 | Dominant Positions fixes | done |
| SCR-01 to 04 | Scrambles fixes | done |
| GUARD-01 | Guard built-out OT check | pending |
| SITE-CLAUDE-MD | Create this file | this commit |
---
## SIGN-OFF TAGS (mandatory on every message)
| Origin | Tag |
|--------|-----|
| Claude Chat | — FROM: CLAUDE CHAT |
| Cowork | — FROM: COWORK |
| Code | — FROM: CODE |
| Aaron | — FROM: AARON |
| ChatGPT | — FROM: CHATGPT |
