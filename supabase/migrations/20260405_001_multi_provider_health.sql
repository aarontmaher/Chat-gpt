-- Multi-Provider Health Backend Schema
-- Phase 1: Backend-backed file upload + normalization
-- Supports: WHOOP, Polar, Apple Health, Health Connect, manual import

-- ─── PROVIDER CONNECTIONS ───────────────────────────────────────────────────
-- Per-user per-provider connection metadata, tokens, sync status
CREATE TABLE IF NOT EXISTS provider_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  provider TEXT NOT NULL, -- 'whoop', 'polar', 'apple_health', 'health_connect'
  connection_mode TEXT NOT NULL, -- 'oauth', 'manual_import', 'file_upload', 'api_key'
  
  -- Connection status (truthful labels)
  status TEXT NOT NULL DEFAULT 'manual_only',
  -- Possible values:
  --   'connected'         - Real OAuth/API connection (Stage 3 only)
  --   'manual_only'       - No auto-sync; file imports only
  --   'manual_import'     - Recently imported file; no further sync attempted
  --   'sync_failed'       - Auto-sync tried but errored
  --   'needs_reconnect'   - Token expired or OAuth/API needs refresh
  --   'not_connected'     - Never connected
  
  -- OAuth / API tokens (encrypted at rest in Supabase)
  access_token TEXT,
  refresh_token TEXT,
  expires_at TIMESTAMPTZ,
  provider_account_id TEXT, -- e.g., Polar user ID, WHOOP user_id
  
  -- Sync metadata
  last_sync_at TIMESTAMPTZ,
  last_error TEXT,
  sync_failed_count INTEGER DEFAULT 0,
  last_status_check TIMESTAMPTZ,
  
  -- Audit
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(user_id, provider)
);

CREATE INDEX idx_provider_connections_user ON provider_connections(user_id);
CREATE INDEX idx_provider_connections_status ON provider_connections(user_id, status);

ALTER TABLE provider_connections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own provider connections" 
  ON provider_connections FOR ALL 
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- ─── DAILY METRICS (Normalized) ──────────────────────────────────────────────
-- Common health data normalized across all providers
CREATE TABLE IF NOT EXISTS daily_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  date DATE NOT NULL, -- ISO format YYYY-MM-DD
  provider TEXT NOT NULL, -- 'whoop', 'polar', 'apple_health', 'health_connect'
  
  -- Normalized fields (all providers map to these)
  recovery_score NUMERIC,
  readiness_label TEXT, -- 'high', 'moderate', 'low', 'unknown'
  hrv_ms NUMERIC,
  resting_hr NUMERIC,
  sleep_hours NUMERIC,
  sleep_performance_pct NUMERIC,
  daily_strain NUMERIC,
  step_count INTEGER,
  
  -- Provenance
  import_id UUID REFERENCES provider_imports(id) ON DELETE SET NULL,
  last_updated TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(user_id, date, provider)
);

CREATE INDEX idx_daily_metrics_user_date ON daily_metrics(user_id, date DESC);
CREATE INDEX idx_daily_metrics_date_range 
  ON daily_metrics(user_id, date DESC) 
  WHERE date >= CURRENT_DATE - INTERVAL '90 days';

ALTER TABLE daily_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own metrics" 
  ON daily_metrics FOR ALL 
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- ─── PROVIDER IMPORTS (Raw Payloads) ─────────────────────────────────────────
-- Records of file uploads / API imports; stores raw provider payloads
CREATE TABLE IF NOT EXISTS provider_imports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  import_mode TEXT NOT NULL, -- 'file_upload', 'api_batch', 'oauth_sync', 'manual_entry'
  
  -- Raw payload (exact JSON from provider / user upload)
  raw_payload JSONB NOT NULL,
  
  -- Import summary
  record_count INTEGER, -- how many daily records in this import
  date_range_start DATE,
  date_range_end DATE,
  
  -- Status
  status TEXT DEFAULT 'pending', -- 'pending', 'processed', 'failed', 'partial'
  error_message TEXT,
  
  -- Audit
  imported_by TEXT, -- 'user_upload', 'oauth_sync', 'api_batch'
  created_at TIMESTAMPTZ DEFAULT now(),
  processed_at TIMESTAMPTZ
);

CREATE INDEX idx_provider_imports_user ON provider_imports(user_id);
CREATE INDEX idx_provider_imports_status ON provider_imports(user_id, status);

ALTER TABLE provider_imports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own imports" 
  ON provider_imports FOR ALL 
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
