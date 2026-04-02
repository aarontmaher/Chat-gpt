# LOCKED DECISIONS
Last updated: 2026-03-23

## Content
- Technique content: Aaron only. Claude NEVER invents.
- No-Gi only. Permanent.
- Half guard: canonical (19 Guard positions total)
- Knee on belly: sub-position under Side Control. PERMANENT HOLD. Never redirect/delete.
- Saddle canonical: "Saddle". Confirmed by Aaron 2026-04-02.
- Exits / Transitions: instructional text only. NOT graph edges.
- D'Arce: spelled "D'Arce" (apostrophe, capital D). Folder slug: "darce" or "reverse-darce".
- Von Flue: capitalized "Von Flue".
- Head arm choke: classified as a submission.
- Single arm chest wrap: classified as both a control sub-position and an offence family.
- Offence heading: contains messy attack families (chains, setups, combinations).
- Submissions heading: contains flat named finishes (arm bar, triangle, kimura, etc.).
- Offensive transitions: clean graph edges ONLY (arrow format). No technique content.
- When Aaron corrects guidance, restate the full updated answer with corrections integrated.

## Schema
- Dominant Positions: Attacker/Defender + 6 headings (Defence/Escapes)
- Guard: Passer/Guard player + 6 headings (Defence/Escapes)
- Scrambles: Initiative/Defensive + 6 headings (Defence/Escapes)
- Wrestling: Attacker/Defender + 6 headings (Defence, NOT Defence/Escapes)
- Hand Fighting: You/Opponent + 5 headings (NO Submissions)

## Workflow
- OPML-only workflow: grappling.opml = source of truth. Mindomo = viewer only.
- Cowork: RETIRED (2026-03-19)
- KEY_VERSION: 2
- Built-out filter: excludes Hand Fighting
- COMMIT_MIN: 5 videos per technique folder for playlists
- Automation: old KM bridge only (mark_done.sh + bridge_cycle.sh). Watcher flow retired.
- Belt syllabus: ALL technique selections must come from Aaron's existing mapped content only. Code must NOT invent or substitute techniques. Unconfirmed slots = "needs Aaron selection".

## Website
- Node size formula: pow(_w, 0.85) * 1.8
- Boot sequence: loadState→initDataFromSections→buildSections→markBuiltOut→updateStats→initGraph3D
- Keyboard shortcuts: / T D R S V G ? Esc arrows
- Automated testing: Playwright. npm run ready = deploy gate.
- Chat no longer checks feature existence — Playwright handles that.

## Naming
- Side bodylock (not "Wrestling side bodylock")
- Shots container: "Shots"
- 2-on-1 canonical: "2-on-1 (You)"
- Wrestling heading: "Defence" (not "Defence / Escapes")
- Guard heading: "Defence / Escapes"
