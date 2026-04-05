# Stage 1 Status Report — End-to-End Wiring

**Date:** 2026-04-05  
**Commits:** `dd0751c` (Phase 1 schema + functions) → `65ed2f6` (Stage 1 wiring)

---

## Executive Summary

**Stage 1 is code-complete and committed.** The backend-backed manual import infrastructure is ready for Supabase deployment. Code is tested (23/23 smoke tests pass) and production-honest (Polar remains manual-import, no auto-connection).

**Status:**
- ✅ Schema created (3 tables with DATE types, RLS policies)
- ✅ Backend functions created (health-import normalization, health-status reader)
- ✅ Frontend wired (Polar upload → health-import)
- ✅ Tests passing (no regressions)
- ✅ Code committed and pushed
- ⏳ **Awaiting Supabase deployment** (manual steps required)
- ⏳ **Awaiting backend verification** (post-deployment)

---

## What Is Live Now

### Local State
- **Polar file upload:** Still works locally (drag-drop → syncPolarData → normalized state)
- **Backend wiring code:** In place (syncPolarData calls health-import async)
- **Tests:** 23/23 passing (no behavior change yet)

### Supabase Live
- ❌ Migration NOT applied (SQL schema tables do NOT exist)
- ❌ health-import function NOT deployed (endpoint 404)
- ❌ health-status function NOT deployed (endpoint 404)
- ✅ Project exists: https://rejalrfmievikabgsakf.supabase.co

### Production Site
- ✅ Polar is still manual-upload only
- ✅ No fake "connected" status
- ✅ WHOOP flow unchanged (providerRequest rename is transparent)
- ⚠️ Health-import calls will fail silently (backend endpoints not live yet)

---

## What Changes on Deployment

### Step 1: Deploy Migration
**File:** `supabase/migrations/20260405_001_multi_provider_health.sql`

**Tables created:**
```sql
provider_connections (
  id UUID,
  user_id UUID,
  provider TEXT ('polar', 'apple_health', 'whoop', etc.),
  connection_mode TEXT ('oauth', 'manual_upload'),
  status TEXT ('manual_only', 'manual_import', 'sync_failed', 'needs_reconnect', 'connected'),
  access_token TEXT (encrypted),
  refresh_token TEXT (encrypted),
  expires_at TIMESTAMP,
  last_sync_at TIMESTAMP,
  last_error TEXT
  -- + indexes, RLS policies
)

daily_metrics (
  id UUID,
  user_id UUID,
  date DATE,
  provider TEXT,
  recovery_score INT,
  hrv_ms INT,
  resting_hr INT,
  sleep_hours DECIMAL,
  daily_strain DECIMAL,
  readiness_state TEXT,
  import_id UUID (FK to provider_imports),
  synced_at TIMESTAMP
  -- + indexes, RLS policies, dedup key on (user_id, date, provider)
)

provider_imports (
  id UUID,
  user_id UUID,
  provider TEXT,
  import_mode TEXT ('manual_upload'),
  raw_payload JSONB,
  record_count INT,
  date_range_start DATE,
  date_range_end DATE,
  status TEXT ('pending', 'completed', 'failed'),
  created_at TIMESTAMP,
  error_message TEXT
  -- + RLS policies
)
```

### Step 2: Deploy health-import Function
**File:** `supabase/functions/health-import/index.ts`

**Behavior:**
```
Input: POST /health-import
  {
    provider: 'polar',
    import_mode: 'manual_upload',
    raw_payload: { ... Polar JSON ... }
  }

Process:
  1. Validate auth (via Supabase JWT)
  2. Store raw payload in provider_imports(status: 'pending')
  3. Normalize daily records from raw payload
  4. Upsert into daily_metrics (dedup by user/date/provider)
  5. Update provider_connections with status='manual_import' + last_sync_at
  6. Return { ok: true, import_id, record_count, date_range }

Error handling:
  - auth_required: User not authenticated
  - normalization_failed: Payload malformed
  - storage_failed: Database error
```

### Step 3: Deploy health-status Function
**File:** `supabase/functions/health-status/index.ts`

**Behavior:**
```
Input: GET /health-status?provider=polar

Process:
  1. Validate auth
  2. Query provider_connections for given provider
  3. Return status + sync metadata

Output: 
  {
    ok: true,
    status: 'manual_import',  // or 'manual_only', 'sync_failed', etc.
    connection_mode: 'manual_upload',
    last_sync_at: ISO8601,
    last_error: null or error text
  }
```

---

## Frontend Changes (Already Deployed)

**File:** `index.html`

**Function:** `syncPolarData(data)`

**Change:**
```javascript
// Before (dd0751c):
function syncPolarData(data) {
  // 1. Normalize Polar JSON
  // 2. Store in STATE.polarData (localStorage)
  // 3. Update UI + AI card
  return true;
}

// After (65ed2f6):
function syncPolarData(data) {
  // 1. Normalize Polar JSON (same as before)
  // 2. Store in STATE.polarData (same as before)
  // 3. Update UI + AI card (same as before)
  // 4. PLUS: Fire async backend call to health-import
  //    - Uses providerRequest('health-import', 'POST', {...})
  //    - Fire-and-forget IIFE
  //    - Logs success/error to console
  //    - Does NOT block UI
  return true; // Returns synchronously (local sync success)
}
```

**Impact on user:**
- ✅ Polar upload still works (no UI change)
- ✅ Local data still synced to STATE.polarData
- ✅ Backend call happens silently in background
- ⚠️ If backend unreachable: Warning logged to console, but UI doesn't break

---

## Verification Plan (Post-Deployment)

### Automated Checks
```bash
# After deploying to Supabase, run:
bash STAGE1_VERIFICATION.sh
```

### Manual Verification
1. **Migration applied:**
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' AND table_name IN (...);
   -- Expected: 3 rows
   ```

2. **Functions deployed:** Check Supabase UI → Edge Functions → both show "Deployed"

3. **Polar upload end-to-end:**
   - Upload sample Polar JSON file
   - Check browser console: `Polar import stored serverside: [UUID]`
   - Query Supabase:
     ```sql
     SELECT * FROM daily_metrics WHERE provider = 'polar' LIMIT 1;
     SELECT * FROM provider_connections WHERE provider = 'polar';
     ```

4. **WHOOP flow unchanged:**
   - Test WHOOP connect/refresh flows
   - Verify they still work (providerRequest rename is transparent)

---

## Files Changed

### Committed (dd0751c)
| File | Purpose | Status |
|------|---------|--------|
| `supabase/migrations/20260405_001_multi_provider_health.sql` | PostgreSQL schema | ✅ Created |
| `supabase/functions/health-import/index.ts` | Normalizer + storage | ✅ Created |
| `supabase/functions/health-status/index.ts` | Status reader | ✅ Created |
| `index.html` (whoopRequest → providerRequest) | Generic naming | ✅ Renamed |

### Committed (65ed2f6)
| File | Purpose | Status |
|------|---------|--------|
| `index.html` (syncPolarData) | Polar backend wiring | ✅ Modified |
| `STAGE1_DEPLOYMENT_GUIDE.md` | Step-by-step deployment | ✅ Created |
| `STAGE1_VERIFICATION.sh` | Post-deployment checks | ✅ Created |

### Not Changed
- ✅ No Apple Health changes (kept as-is)
- ✅ No WHOOP changes (transparent rename)
- ✅ No UI changes (Polar still shows manual import)
- ✅ No production behavior changes

---

## Deployment Sequence

**To complete Stage 1:**

1. **Manual:** Deploy migration to Supabase SQL editor
   ```
   Copy: supabase/migrations/20260405_001_multi_provider_health.sql
   Paste into: https://app.supabase.com/projects/rejalrfmievikabgsakf/sql/new
   Run
   ```

2. **Manual:** Deploy health-import function
   ```
   Copy: supabase/functions/health-import/index.ts
   Paste into Supabase UI → Edge Functions → Create new → Name: health-import
   Save and Deploy
   ```

3. **Manual:** Deploy health-status function
   ```
   Copy: supabase/functions/health-status/index.ts
   Paste into Supabase UI → Edge Functions → Create new → Name: health-status
   Save and Deploy
   ```

4. **Automated (optional):** Run verification script
   ```bash
   bash STAGE1_VERIFICATION.sh
   ```

5. **Manual:** Test Polar upload on live site
   - Upload sample file
   - Check console for success messages
   - Query Supabase to verify data persisted

---

## Success Criteria (Stage 1 Complete)

✅ **All must be true:**

- [ ] Migration applied (3 tables exist in Supabase)
- [ ] health-import deployed (shows "Deployed" status)
- [ ] health-status deployed (shows "Deployed" status)
- [ ] Polar upload doesn't show console errors
- [ ] Console shows `Polar import stored serverside: [ID]` on upload
- [ ] `daily_metrics` table contains uploaded data
- [ ] `provider_connections` shows status='manual_import' for Polar
- [ ] WHOOP flow still works (no regressions)
- [ ] No production behavior change (Polar still manual-import)

---

## What Comes Next (Stage 2+)

**Blocked until Stage 1 verified:**

### Stage 2: Better Repeat Import UX (1–2 weeks)
- Add "Refresh" button to Polar connection card
- Show `last_sync_at` and `last_error` from backend
- Handle re-upload logic (skip if already imported today)

### Stage 3: Real Polar OAuth (2–4 weeks, if viable)
- Implement `polar-connect` endpoint (OAuth initiation)
- Implement `polar-auth-callback` (token exchange)
- Implement `polar-refresh` (auto-sync trigger)
- Gate behind feature flag for 2 weeks first

---

## Risk Assessment

**Risks (mitigated):**
1. **Backend endpoints down:** Polar upload still works locally (fire-and-forget, silent failure)
2. **Auth issues:** RLS policies protect user data (per-user access control)
3. **Duplicate imports:** Dedup key on (user_id, date, provider) prevents duplicates
4. **No production change:** Polar UI text still says "manual import" (no fake connection state)

**What could break:**
- If migration has syntax errors → rollback via SQL editor
- If function code has errors → view logs in Supabase UI, fix, redeploy
- If auth headers malformed → check UserStore._getAuthHeaders() implementation

---

## Current Git State

```
65ed2f6 (HEAD -> main, origin/main) Stage 1: Wire Polar manual upload to health-import backend
dd0751c Phase 1: Backend-backed multi-provider health import infrastructure
3a82a7f Revert "Add mock Polar Supabase edge functions for automatic connection"
```

**All code committed and pushed.** Ready for Supabase deployment.

---

## Questions for Aaron

1. **Ready to deploy to Supabase?** (migration + 2 functions manual steps)
2. **Test user credentials?** (for post-deployment verification)
3. **Timeline?** (Stage 1 complete vs Stage 2 start)
