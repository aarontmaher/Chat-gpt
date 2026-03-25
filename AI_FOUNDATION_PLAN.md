# AI FOUNDATION PLAN
Created: 2026-03-25

## Architecture
```
User → In-App AI Panel → Local JS Actions → App State (SECTIONS, STATE, NET_*)
                       → Supabase Edge Functions (future) → LLM API
                       → MCP Server (later) → External AI clients
```

## Phase 1: Local AI Actions (no LLM needed)
The AI assistant can do a LOT without calling any external AI API — just by reading the existing app state intelligently.

### Actions the AI can perform locally:
| Action | Data Source | Guest? |
|--------|-----------|--------|
| "What should I drill next?" | STATE.progress + NET_EDGES | Member only |
| "Show my weak areas" | STATE.progress vs SECTIONS coverage | Member only |
| "Build me a drill session" | STATE.progress (drilling) + random | Member only |
| "Summarize my training" | STATE.successLog + drillingStarted | Member only |
| "What's connected to [position]?" | NET_EDGES | Everyone |
| "Explain [position]" | SECTIONS tree | Everyone |
| "Show my game on the map" | STATE.progress + NET_NODES | Member only |
| "Filter to my belt" | Belt syllabus files + STATE | Member only |
| "What techniques have video?" | SECTIONS (node.v/node.l) | Everyone |
| "Find path from A to B" | NET_EDGES (BFS) | Everyone |

### Why local-first matters:
- Zero latency
- Zero API cost
- Works offline
- Can ship immediately
- LLM layer adds natural language later, not core functionality

## Phase 2: API Layer (Supabase Edge Functions)
When per-user cloud data exists:
```
GET  /api/profile          → user profile + membership
GET  /api/progress         → user's tracked techniques
GET  /api/success-log      → user's success history
GET  /api/drills           → user's current drilling queue
GET  /api/recommendations  → next-move suggestions (computed)
GET  /api/syllabus/:belt   → belt syllabus content
GET  /api/graph/path       → shortest path between positions
POST /api/progress         → update tracking status
POST /api/success-log      → log a success
```

## Phase 3: LLM Integration
- Supabase Edge Function wrapping Claude/OpenAI API
- System prompt with user context (progress, belt, recent activity)
- Tool use: calls the Phase 2 APIs as tools
- In-app chat panel sends messages to edge function

## Phase 4: MCP Server
- Expose Phase 2 APIs as MCP tools
- External AI clients (Claude Desktop, etc.) can access user's grappling data
- Auth via Supabase JWT

## UI Design

### AI Panel
- Bottom-sheet on mobile, side panel on desktop
- Chat-style interface
- Quick action buttons: "What to drill?" / "My weak areas" / "Build session"
- Works without LLM (Phase 1 = local actions only)

## Implementation Batches

### Batch 1: AI Action Layer + Panel Shell ← SAFE TO START NOW
1. Create `AIActions` object with local-only smart actions
2. Add AI panel shell (bottom-sheet mobile, side panel desktop)
3. Quick action buttons that call AIActions
4. No LLM, no API, no external calls
5. Pure JS reading existing STATE + SECTIONS + NET_*

### Batch 2: Rich AI Responses
1. Format AIActions responses as cards/lists (not plain text)
2. Clickable results (jump to technique, start drill)
3. Context-aware suggestions based on current view

### Batch 3: API Contract + Edge Functions
1. Define API endpoints in Supabase Edge Functions
2. Move user data operations from localStorage to API
3. Auth-gated endpoints with RLS

### Batch 4: LLM Integration
1. Edge function wrapping LLM API
2. System prompt with user context
3. Tool use for structured actions
4. Natural language chat in AI panel

### Batch 5: MCP Server
1. Express/Deno MCP server exposing APIs as tools
2. Auth via Supabase JWT
3. Tool definitions matching Phase 2 API shape

---

## DATA INTELLIGENCE LAYERS

### Layer 1 — Private User Data
Per-user, auth-protected, never exposed cross-user.

| Resource | Current Location | Future Location |
|----------|-----------------|----------------|
| Profile | AUTH_USER in memory | Supabase profiles table |
| Belt state | localStorage (gm_current_belt) | Supabase user_preferences |
| Progress (track/want/drilling/learned) | localStorage | Supabase user_progress |
| Success log | localStorage (successLog[]) | Supabase success_log |
| Drilling started timestamps | localStorage (drillingStarted{}) | Supabase user_progress.started_at |
| Notes | localStorage (notes{}) | Supabase user_notes |
| Recent viewed | localStorage (recentViewed[]) | Supabase user_preferences |
| Videos watched | localStorage (videosWatched{}) | Supabase user_preferences |
| Last practiced | localStorage (lastPracticed{}) | Supabase user_preferences |

**API shape (future):**
```
GET  /api/me/profile
GET  /api/me/progress
GET  /api/me/success-log
GET  /api/me/drills
GET  /api/me/notes
POST /api/me/progress    { technique_key, status }
POST /api/me/success-log { technique_key }
POST /api/me/notes       { technique_key, text }
```

### Layer 2 — Shared Aggregate Intelligence
Anonymous product-level patterns, safe for all users.

| Signal | How Computed | Use |
|--------|-------------|-----|
| Most tracked techniques | COUNT across all user_progress | "Popular techniques" |
| Most hit techniques | COUNT across all success_log | "What people are hitting" |
| Common transitions | NET_EDGES weight + success frequency | "Common paths" |
| Common next moves | After technique X, users often track Y | "Suggested additions" |
| Weak-point clusters | Positions with high track-to-abandon rate | "Common trouble spots" |
| Belt distribution | COUNT profiles by belt state | "Community progress" |

**API shape (future):**
```
GET /api/aggregate/popular-techniques
GET /api/aggregate/common-paths
GET /api/aggregate/next-move?from=technique_key
GET /api/aggregate/community-stats
```

**Rules:**
- No PII in aggregate queries
- Results are pre-computed or cached (not real-time scans)
- Safe for guests to see aggregate data
- Members get personalized overlay (their data + aggregate)

### Layer 3 — AI Assistant Behavior

**Guest AI:**
- Can use: map structure, aggregate data, technique explanations
- Cannot use: personal progress, drills, notes, success log
- Example: "What positions connect to Mount?" / "What's popular?"

**Member AI:**
- Can use: everything from Layer 1 + Layer 2 + map structure
- Example: "What should I drill?" / "Show my weak areas" / "Build a session"
- Future LLM: system prompt includes user context from Layer 1

**How AI combines layers:**
```
User asks: "What should I work on next?"

AI reads:
  Layer 1: user's progress, success log, drilling queue
  Layer 2: what similar users prioritized after same patterns
  Structure: NET_EDGES connections from user's strong positions

AI responds:
  "You've been hitting Toreando from J point. People with similar
   patterns often add Leg drag next. Your Mount submissions are
   a gap — consider adding Head arm choke."
```

## Blockers
| Blocker | Owner | Needed for |
|---------|-------|------------|
| None | — | Batch 1 (local actions) |
| None | — | Batch 2 (rich responses) |
| Supabase Edge Functions setup | Aaron | Batch 3 |
| LLM API key (Claude/OpenAI) | Aaron | Batch 4 |
| MCP server hosting | Aaron | Batch 5 |

**Batch 1 has ZERO blockers.**
