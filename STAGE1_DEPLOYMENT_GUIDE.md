# Stage 1 Deployment Guide

## Overview
This guide deploys the backend-backed manual import infrastructure to Supabase.

**Project:** https://rejalrfmievikabgsakf.supabase.co  
**Deployment Scope:**
1. PostgreSQL migration (3 tables + RLS policies)
2. Two Deno edge functions (health-import, health-status)
3. Frontend code (already committed in dd0751c)

---

## Step 1: Deploy Migration (SQL Schema)

**Location:** `supabase/migrations/20260405_001_multi_provider_health.sql`

**Action:**
1. Open Supabase dashboard: https://app.supabase.com/projects/rejalrfmievikabgsakf/sql/new
2. Copy the entire contents of `supabase/migrations/20260405_001_multi_provider_health.sql`
3. Paste into SQL editor
4. Click **Run**

**Verification:**
```sql
-- Run in Supabase SQL editor to verify deployed tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('provider_connections', 'daily_metrics', 'provider_imports');
```

**Expected Output:** 3 rows (provider_connections, daily_metrics, provider_imports)

---

## Step 2: Deploy health-import Edge Function

**Location:** `supabase/functions/health-import/`

**Action:**
1. In Supabase dashboard, go to **Edge Functions**
2. Click **Create a new function**
3. Name: `health-import`
4. Copy entire contents of `supabase/functions/health-import/index.ts`
5. Paste as function body
6. Click **Save and Deploy**

**Expected:** Function shows "Deployed" status

---

## Step 3: Deploy health-status Edge Function

**Location:** `supabase/functions/health-status/`

**Action:**
1. In Supabase dashboard, go to **Edge Functions**
2. Click **Create a new function**
3. Name: `health-status`
4. Copy entire contents of `supabase/functions/health-status/index.ts`
5. Paste as function body
6. Click **Save and Deploy**

**Expected:** Function shows "Deployed" status

---

## Step 4: Verify Endpoint Availability

**Action:** Run this from terminal or JavaScript console on deployed site:

```javascript
// Test health-status endpoint (read-only, safe to test)
const result = await providerRequest('health-status', 'GET?provider=polar');
console.log('health-status result:', result);
```

**Expected Results:**
- If user not authenticated: `{ok: false, error: "auth_required"}`
- If user authenticated: `{ok: true, status: "not_connected", ...}` or similar

---

## Step 5: Test Polar Manual Upload End-to-End

**Action:**
1. Open deployed site in browser
2. Open health/training modal
3. Upload a sample Polar JSON file
4. Verify toast shows "Polar data synced for [DATE]"
5. Check browser console for `Polar import stored serverside: [ID]`

**Expected Backend Effects:**
```sql
-- In Supabase SQL editor
SELECT * FROM daily_metrics WHERE user_id = (SELECT id FROM auth.users LIMIT 1) AND provider = 'polar';
SELECT * FROM provider_connections WHERE provider = 'polar' LIMIT 1;
SELECT * FROM provider_imports WHERE provider = 'polar' LIMIT 1;
```

---

## Step 6: Verify Readback

**Action:**
1. On site, navigate to health modal (or refresh page)
2. Verify Polar data persists (either from localStorage or backend readback)
3. Check browser console logs for backend fetch calls

**Expected:** No console errors related to health-import or health-status

---

## Rollback Plan

If deployment fails:

1. **Drop tables (if needed):**
```sql
DROP POLICY IF EXISTS "enable_select_daily_metrics_for_user" ON daily_metrics;
DROP POLICY IF EXISTS "enable_insert_daily_metrics_for_user" ON daily_metrics;
DROP POLICY IF EXISTS "enable_select_provider_connections_for_user" ON provider_connections;
DROP POLICY IF EXISTS "enable_insert_provider_connections_for_user" ON provider_connections;
DROP POLICY IF EXISTS "enable_update_provider_connections_for_user" ON provider_connections;
DROP POLICY IF EXISTS "enable_select_provider_imports_for_user" ON provider_imports;
DROP POLICY IF EXISTS "enable_insert_provider_imports_for_user" ON provider_imports;
DROP TABLE IF EXISTS provider_imports;
DROP TABLE IF EXISTS daily_metrics;
DROP TABLE IF EXISTS provider_connections;
```

2. **Delete functions:** In Supabase UI, click **Delete** on health-import and health-status

3. **Revert code:** `git revert dd0751c` (only if necessary; frontend code is backward-compatible)

---

## Status Tracking

**Last Verified:** 2026-04-05 (commit dd0751c)

| Component | Status | Verification |
|-----------|--------|--------------|
| Migration SQL | Ready | ✅ File created, reviewed |
| health-import function | Ready | ✅ File created, reviewed |
| health-status function | Ready | ✅ File created, reviewed |
| Frontend wiring | ✅ Deployed | Commit dd0751c (index.html modified) |
| Tests | ✅ Passing | 23/23 smoke tests pass |

---

## Troubleshooting

### Issue: `auth_required` error on providerRequest calls
**Cause:** User not signed in to Supabase Auth
**Solution:** Test with Supabase Auth user, or mock auth headers

### Issue: Function not found (404)
**Cause:** Function not deployed to Supabase
**Solution:** Follow Step 2–3 again, verify function shows "Deployed" status

### Issue: RLS policy blocks insert
**Cause:** User ID mismatch
**Solution:** Verify RLS policy in migration allows inserts, check `auth.users` table

### Issue: Data not persisting
**Cause:** Manual import call succeeded locally but backend call failed silently
**Solution:** Check browser console for `Polar backend call error` warnings, verify network tab for failed requests

---

## Success Criteria

Stage 1 is complete when:
1. ✅ Migration applied successfully (3 tables exist)
2. ✅ Both edge functions deployed (show "Deployed" status)
3. ✅ Polar file upload no longer shows console errors
4. ✅ Polar data stored in `daily_metrics` table (visible in Supabase UI)
5. ✅ `provider_connections.status` updated to `"manual_import"` for Polar
6. ✅ No production behavior change (Polar still shows as "manual import")
7. ✅ WHOOP flow unchanged (confirms providerRequest rename is transparent)
