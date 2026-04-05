# Stage 1 Live Deployment — Exact Steps

**Project:** https://app.supabase.com/projects/rejalrfmievikabgsakf  

---

## Deployment Checklist

### Step 1: Deploy Migration

1. **Open SQL Editor:**
   ```
   https://app.supabase.com/projects/rejalrfmievikabgsakf/sql/new
   ```

2. **Copy entire migration file:**
   - File: `supabase/migrations/20260405_001_multi_provider_health.sql`
   - Opens in IDE: Double-click the file
   - Select all (Cmd+A)
   - Copy (Cmd+C)

3. **Paste into Supabase SQL Editor:**
   - Paste (Cmd+V) into the SQL editor window
   - Click **RUN** button

4. **Verify success:**
   - Look for green checkmark or "Query executed successfully"
   - If error: Fix syntax and retry (or screenshot error for debugging)

**Tables created:** `provider_connections`, `daily_metrics`, `provider_imports`

---

### Step 2: Deploy health-import Function

1. **Open Edge Functions:**
   ```
   https://app.supabase.com/projects/rejalrfmievikabgsakf/functions
   ```

2. **Create new function:**
   - Click "Create a new function"
   - **Name:** `health-import` (exactly this)
   - Click "Create function"

3. **Copy function code:**
   - File: `supabase/functions/health-import/index.ts`
   - Select all and copy

4. **Paste into Supabase editor:**
   - Delete template code
   - Paste entire code from index.ts

5. **Deploy:**
   - Click "Deploy" button
   - Wait for "Deployed" status

**Expected:** Green "Deployed" badge + no error logs

---

### Step 3: Deploy health-status Function

1. **Create another new function:**
   - Click "Create a new function"
   - **Name:** `health-status` (exactly this)
   - Click "Create function"

2. **Copy function code:**
   - File: `supabase/functions/health-status/index.ts`
   - Select all and copy

3. **Paste into Supabase editor:**
   - Delete template code
   - Paste entire code from index.ts

4. **Deploy:**
   - Click "Deploy" button
   - Wait for "Deployed" status

**Expected:** Green "Deployed" badge + no error logs

---

## Verification (After Deployment)

### Database Tables

Open SQL editor and run:

```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('provider_connections', 'daily_metrics', 'provider_imports')
ORDER BY table_name;
```

**Expected:** 3 rows returned (daily_metrics, provider_connections, provider_imports)

---

### RLS Policies

```sql
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE tablename IN ('provider_connections', 'daily_metrics', 'provider_imports')
ORDER BY tablename, policyname;
```

**Expected:** 8 rows (2-3 policies per table)

---

### Function Logs

In Supabase UI:
1. Go to Edge Functions
2. Click "health-import"
3. Go to "Invocations" tab
4. No red error badges

Same for "health-status"

---

## Browser Testing (Production Site)

### Before Deployment
1. Open: https://aarontmaher.github.io/Chat-gpt/
2. Open browser DevTools (F12)
3. Click on health tab
4. Try uploading Polar file
5. **Check console:** Should show either:
   - "Polar backend call error" (before deployment — expected)
   - Or no backend message (if error silently caught)

### After Deployment
1. Same steps
2. **Check console:**
   - ✅ Should show: `Polar import stored serverside: <UUID>`
   - ✅ No errors about "Unauthorized" or "Unauthorized"
   - ✅ Modal closes normally
   - ✅ Local data synced (UI updates)

### Network Tab (Dev Tools)
1. Open DevTools → Network tab
2. Upload Polar file
3. **Look for:**
   - ✅ POST to `health-import` endpoint
   - ✅ Status 200 (success)
   - ✅ Response body has `import_id` field

---

## Database Verification (After Upload)

In SQL editor, run:

```sql
-- Check daily metrics were created
SELECT user_id, date, provider, recovery_score, hrv_ms
FROM daily_metrics 
WHERE provider = 'polar' 
ORDER BY date DESC 
LIMIT 5;
```

**Expected:** ≥ 1 row with today's data

---

```sql
-- Check provider_connections status
SELECT user_id, provider, status, connection_mode, last_sync_at
FROM provider_connections 
WHERE provider = 'polar' 
LIMIT 1;
```

**Expected:** status = `'manual_import'` (not `'manual_only'`)

---

```sql
-- Check provider_imports tracking
SELECT import_id, user_id, provider, record_count, status
FROM provider_imports 
WHERE provider = 'polar' 
ORDER BY created_at DESC 
LIMIT 1;
```

**Expected:** 1 row with `record_count ≥ 1`, `status = 'pending'` or `'completed'`

---

## Troubleshooting

### Issue: Migration fails with "table already exists"
**Cause:** Schema already deployed
**Action:** This is OK — skip to Step 2 (functions)

### Issue: Edge function shows "Unauthorized" error
**Cause:** Auth header not being sent
**Action:** Check browser console for auth errors, verify UserStore._getAuthHeaders() works

### Issue: Health-import returns 400 "Missing provider"
**Cause:** Request body malformed
**Action:** Check Network tab → Request tab for sent JSON, verify it matches schema

### Issue: No data appears in daily_metrics
**Cause:** RLS policy blocking insert
**Action:** Verify `auth.uid() = user_id` in policy, check user is authenticated

---

## Success Criteria (All must be ✅)

- [ ] Migration runs successfully (no errors)
- [ ] health-import shows "Deployed" status
- [ ] health-status shows "Deployed" status
- [ ] 3 database tables exist
- [ ] 8 RLS policies exist
- [ ] Browser console shows `Polar import stored serverside` after upload
- [ ] Network tab shows 200 response from health-import
- [ ] At least 1 row in daily_metrics after upload
- [ ] provider_connections.status = 'manual_import' for Polar
- [ ] No "Unauthorized" errors in console or network log

---

## What This Deployment Enables

Once all steps complete and verification passes:

✅ **Polar manual upload now writes to backend**
- Local data synced to STATE.polarData (UI works)
- Backend call fires silently (logs to console)
- Data stored server-side in daily_metrics table
- Connection status updated to 'manual_import'

✅ **Production behavior stays honest**
- Polar UI still says "manual import"
- No fake "connected" state
- WHOOP flow unchanged

✅ **Ready for Stage 2**
- Can add "Refresh" button to Polar card
- Can read last_sync_at from backend
- Can prevent duplicate imports

---

## Files Involved

| File | Purpose | Action |
|------|---------|--------|
| supabase/migrations/20260405_001_multi_provider_health.sql | Schema | Copy → Paste → Run in SQL editor |
| supabase/functions/health-import/index.ts | Backend handler | Copy → Create function → Deploy |
| supabase/functions/health-status/index.ts | Status reader | Copy → Create function → Deploy |
| index.html | Frontend wiring | Already deployed (commit 65ed2f6) |

---

## Timeline

- **Deployment:** 5–10 minutes (manual steps)
- **Verification:** 2–3 minutes (run tests)
- **Troubleshooting:** 0 mins if all passes, ↑ if issues

---

## Next Steps After Successful Deployment

1. **Store this deployment guide** for future reference
2. **Run verification checks** to confirm
3. **Test Polar upload** on live site and check browser console
4. **Stage 2 planning:** Better repeat import UX (refresh button, etc.)

---

## Questions?

- If migration fails: Check error message and SQL syntax
- If functions won't deploy: Verify names are exactly `health-import` and `health-status`
- If data doesn't persist: Check browser console for auth errors
