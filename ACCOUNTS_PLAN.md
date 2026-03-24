# ACCOUNTS & ACCESS ARCHITECTURE PLAN
Created: 2026-03-24
Prompt-ID: ACCESS-AND-ACCOUNTS-BUILD-01

---

## 1. ACCESS SPLIT

### PUBLIC / GUEST (no account)
| Feature | Access |
|---------|--------|
| 3D Position Map (full graph) | ✅ Full — rotate, zoom, click all nodes |
| Node names + structure | ✅ Full |
| Section list + position list | ✅ Full |
| Limited technique preview | ✅ 2–3 sample techniques per position |
| Start Here / onboarding | ✅ Full |
| "What is this product" understanding | ✅ Full |
| Locked-content indicators | ✅ Shown — "X more techniques — create account" |

### PREVIEW-ONLY (guest can see but not use)
| Feature | Access |
|---------|--------|
| Technique depth beyond preview | 🔒 Teaser visible, content locked |
| Video thumbnails | 🔒 Visible but playback locked |
| Progress indicators | 🔒 Visible (shows what tracking looks like) but non-functional |
| Drill mode | 🔒 Visible in UI but triggers signup prompt |

### MEMBER-ONLY (paid account required)
| Feature | Access |
|---------|--------|
| Full technique depth (all nodes) | 🔓 |
| Full reference library | 🔓 |
| Full video library (instructional + live) | 🔓 |
| Saved progress (drilling/learned/want) | 🔓 |
| Success logging | 🔓 |
| Build Your Game recommendations | 🔓 |
| Drill mode + timer | 🔓 |
| Notes on techniques | 🔓 |
| Recently viewed | 🔓 |
| Filters (MY GAME, DRILLING, LEARNED) | 🔓 |
| White/Blue belt syllabus (full) | 🔓 |
| Personalized next-move suggestions | 🔓 |
| Export/import data | 🔓 |

### FUTURE (needs billing — NOT yet)
| Feature | Access |
|---------|--------|
| Stripe subscription management | ⏳ |
| Tier-based access (free tier vs premium) | ⏳ |
| Team/gym accounts | ⏳ |
| Coach mode | ⏳ |

---

## 2. DATA MODEL (Supabase Postgres + RLS)

### profiles
```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  email TEXT,
  membership_status TEXT NOT NULL DEFAULT 'member',  -- 'member', 'trial', 'expired', 'admin'
  stripe_customer_id TEXT,          -- placeholder for future Stripe
  stripe_subscription_id TEXT,      -- placeholder for future Stripe
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
-- RLS: users can only read/write their own row
```

### user_progress
```sql
CREATE TABLE user_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  technique_key TEXT NOT NULL,       -- KEY_VERSION=2 path key
  status TEXT NOT NULL DEFAULT 'none', -- 'none', 'want', 'drilling', 'learned'
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, technique_key)
);
-- RLS: users can only access their own rows
```

### user_notes
```sql
CREATE TABLE user_notes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  technique_key TEXT NOT NULL,
  note_text TEXT,
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, technique_key)
);
```

### success_log
```sql
CREATE TABLE success_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  technique_key TEXT NOT NULL,
  logged_at TIMESTAMPTZ DEFAULT now()
);
-- RLS: users can only access their own rows
-- Index on (user_id, logged_at DESC) for recent queries
```

### user_preferences
```sql
CREATE TABLE user_preferences (
  user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  last_tab TEXT DEFAULT 'reference',
  last_selected_node TEXT,
  recent_viewed JSONB DEFAULT '[]',
  last_practiced JSONB DEFAULT '{}',
  videos_watched JSONB DEFAULT '{}',
  key_version INTEGER DEFAULT 2,
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

### Row Level Security (all tables)
```sql
-- Same pattern for all user tables:
ALTER TABLE [table] ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own data" ON [table]
  FOR ALL USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
```

---

## 3. AUTH FLOW

### Guest browsing
1. User opens site → no auth check needed
2. App detects `authState === 'guest'`
3. Full 3D map loads, sections render with preview limits
4. Locked content shows upgrade prompts

### Create account / Join boundary
Triggered when guest tries to:
- View full technique depth (clicks "See all" or locked content)
- Use drill mode, success logging, filters
- Save progress

Shows modal: "Create your account to unlock the full map"
→ Supabase Auth signup (email + password, or magic link)
→ On success: migrate any localStorage preview state to Supabase
→ Set `authState = 'member'`

### Member login
- Login button in header (visible when guest)
- Supabase Auth signin (email/password or magic link)
- On success: load user data from Supabase → populate STATE
- Replace header login button with user avatar/menu

### Member logout
- Logout option in user menu
- Supabase signOut()
- Clear in-memory STATE, revert to guest view
- localStorage cleared of user data (keep KEY_VERSION)

### Session handling
- Supabase handles JWT refresh automatically
- On page load: `supabase.auth.getSession()` → if valid, load member state
- If session expired: show login prompt, don't lose page position

---

## 4. UI / AUTH STATES

### Guest state
- Header: shows "Log in" / "Create Account" buttons
- 3D Map: fully functional
- Reference: sections visible, positions visible, techniques limited (2-3 per heading)
- Locked items: show count + "🔒 Create account to see all"
- Filters: hidden (member-only)
- Progress bar: hidden
- Stats: show total positions/techniques (not personal progress)
- Drill/Success: button visible but triggers signup modal

### Logged-in member state
- Header: shows user display name + dropdown (Settings, Logout)
- All content unlocked
- Progress tracking active
- Filters visible and functional
- Stats show personal progress
- Full drill + success logging

### Locked-content state
- Technique rows beyond preview limit: dimmed with lock icon
- Click → signup/login modal
- Videos: thumbnail visible, play button → signup modal
- Clear message: "X techniques available with membership"

### Upgrade prompts
- Contextual: appear at the point of interest (not random popups)
- Non-aggressive: informational, not blocking exploration
- Examples:
  - Bottom of preview list: "12 more techniques → Create account"
  - Drill button: "Track your training → Create account"
  - Filter bar area: "Filter your game → Create account"

---

## 5. IMPLEMENTATION BATCHES

### BATCH 1 — User State Abstraction (NO Supabase needed) ✅ SAFE TO START
**Goal**: Decouple state management from direct localStorage calls so it can be swapped to Supabase later.

Tasks:
1. Create `UserStore` abstraction object in index.html
   - `UserStore.save(key, value)` / `UserStore.load(key)`
   - `UserStore.saveProgress()` / `UserStore.loadProgress()`
   - `UserStore.saveNotes()` / `UserStore.loadNotes()`
   - `UserStore.saveAppState()` / `UserStore.loadAppState()`
   - Currently delegates to localStorage (zero behavior change)
2. Add `AUTH_STATE` variable: `'guest'` or `'member'`
   - For now: always `'member'` (preserves current behavior exactly)
3. Add `isGuest()` / `isMember()` helper functions
4. Add `ACCESS_CONFIG` object defining preview limits
   - `GUEST_TECHNIQUE_LIMIT: 3` (per heading)
   - `GUEST_CAN_USE_FILTERS: false`
   - `GUEST_CAN_SAVE_PROGRESS: false`
   - `GUEST_CAN_DRILL: false`
5. Replace direct `localStorage` calls with `UserStore` calls

**Risk**: Zero — all behavior identical, just abstraction layer.

### BATCH 2 — Guest/Member Gating UI (NO Supabase needed)
**Goal**: Add UI scaffolding that responds to AUTH_STATE.

Tasks:
1. Auth button placeholder in header ("Log in" / user menu)
2. Content gating in reference view (limit techniques for guests)
3. Locked-content indicators ("🔒 Create account")
4. Signup modal shell (no backend wiring yet)
5. Gate drill/success/filter features behind `isMember()` check
6. Hide progress bar + personal stats for guests

**Risk**: Low — behind `AUTH_STATE` flag that defaults to `'member'`.

### BATCH 3 — Supabase Integration (NEEDS Supabase project)
**Goal**: Wire real auth + database.

**Blocker**: Aaron must create Supabase project and provide:
- Supabase project URL
- Supabase anon key (public)
- Run the SQL migrations from this plan

Tasks:
1. Add Supabase JS client (`<script>` tag from CDN)
2. Wire signup/login/logout to Supabase Auth
3. Create DB tables + RLS policies
4. Implement `UserStore.supabase` backend
5. Add localStorage → Supabase migration on first login
6. Session persistence (auto-login on return)

### BATCH 4 — Polish + Production Hardening
Tasks:
1. Offline fallback (if Supabase unreachable, use localStorage cache)
2. Loading states during auth checks
3. Error handling for network failures
4. Rate limiting awareness
5. Email verification flow

### BATCH 5 — Stripe (FUTURE — not yet)
Tasks:
1. Stripe checkout integration
2. Webhook for subscription status
3. Membership expiry handling
4. Billing portal link

---

## 6. MIGRATION STRATEGY

### localStorage → Supabase (on first login)
When a user creates an account or logs in for the first time:
1. Check localStorage for existing progress/notes/successLog
2. If found: upload to Supabase as their initial data
3. Clear localStorage user data (keep KEY_VERSION)
4. Show confirmation: "Your existing progress has been saved to your account"

This preserves Aaron's (and any early user's) existing data.

---

## 7. BLOCKERS

| Blocker | Owner | Needed for |
|---------|-------|------------|
| Supabase project creation | Aaron | Batch 3 |
| Supabase URL + anon key | Aaron | Batch 3 |
| SQL migration execution | Aaron/Code | Batch 3 |
| Stripe account | Aaron | Batch 5 |
| Domain/pricing decisions | Aaron | Batch 5 |

**Batches 1–2 have ZERO blockers and can proceed immediately.**
