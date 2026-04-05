#!/bin/bash
# Stage 1 Live Deployment Script
# Deploys migration and edge functions to Supabase via REST API
# 
# Requirements:
# - SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ACCESS_TOKEN (set as env var)
# - jq (for JSON parsing)
#
# Usage:
#   export SUPABASE_SERVICE_ROLE_KEY="<your_key>"
#   bash deploy-stage1-live.sh
#

set -e

PROJECT_REF="rejalrfmievikabgsakf"
SUPABASE_URL="https://${PROJECT_REF}.supabase.co"
API_URL="https://api.supabase.com"
FUNCTIONS_BASE_URL="${SUPABASE_URL}/functions/v1"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Stage 1 Live Deployment${NC}\n"
echo "Project: ${SUPABASE_URL}"
echo "Date: $(date)"
echo ""

# Check for credentials
if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ] && [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
    echo -e "${RED}✗ Error: Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_ACCESS_TOKEN set${NC}"
    echo ""
    echo "To deploy, run:"
    echo "  export SUPABASE_SERVICE_ROLE_KEY='eyJ...'"
    echo "  bash deploy-stage1-live.sh"
    echo ""
    echo "Or use GitHub CLI:"
    echo "  gh secret set SUPABASE_SERVICE_ROLE_KEY --body '<key>'"
    exit 1
fi

TOKEN="${SUPABASE_SERVICE_ROLE_KEY:-$SUPABASE_ACCESS_TOKEN}"

# Step 1: Deploy Migration via SQL
echo -e "${BLUE}📋 Step 1: Deploy Migration${NC}"
echo "Executing: supabase/migrations/20260405_001_multi_provider_health.sql"

MIGRATION_SQL=$(cat supabase/migrations/20260405_001_multi_provider_health.sql)

echo "Sending migration to Supabase..."
curl -s -X POST \
  "${SUPABASE_URL}/rest/v1/rpc/exec_sql" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"sql\": $(echo "$MIGRATION_SQL" | jq -Rs '.')}" \
  2>&1 | jq . || echo "Note: exec_sql endpoint may not exist. Manual SQL deployment required."

echo ""

# Alternative: SQL via Postgres connection
echo -e "${YELLOW}ℹ️  Alternative: Deploy via SQL Editor${NC}"
echo "If curl failed, deploy manually:"
echo "1. Go to: https://app.supabase.com/projects/${PROJECT_REF}/sql/new"
echo "2. Paste entire contents of: supabase/migrations/20260405_001_multi_provider_health.sql"
echo "3. Click RUN"
echo ""

# Step 2: Deploy Edge Functions
echo -e "${BLUE}📋 Step 2: Deploy Edge Functions${NC}"
echo ""

# health-import function
echo "Deploying health-import function..."
HEALTH_IMPORT_CODE=$(cat supabase/functions/health-import/index.ts)

# Note: The Supabase Management API requires different endpoints
# This would typically be done via CLI: supabase functions deploy health-import
echo -e "${YELLOW}⚠️  Edge function deployment requires Supabase CLI${NC}"
echo ""
echo "To deploy health-import:"
echo "  supabase functions deploy health-import"
echo ""
echo "To deploy health-status:"
echo "  supabase functions deploy health-status"
echo ""
echo "Or via Supabase dashboard:"
echo "  1. Go to: https://app.supabase.com/projects/${PROJECT_REF}/functions"
echo "  2. Click 'Create a new function'"
echo "  3. Name: health-import"
echo "  4. Paste code from: supabase/functions/health-import/index.ts"
echo "  5. Deploy"
echo "  6. Repeat for health-status"
echo ""

# Step 3: Verify deployment
echo -e "${BLUE}📋 Step 3: Verify Deployment${NC}"
echo ""
echo "Testing health-status endpoint..."

RESPONSE=$(curl -s -X GET \
  "${FUNCTIONS_BASE_URL}/health-status?provider=polar" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  2>&1)

echo "Response:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
echo ""

echo "Testing health-import endpoint..."
RESPONSE=$(curl -s -X POST \
  "${FUNCTIONS_BASE_URL}/health-import" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "polar",
    "import_mode": "manual_upload",
    "raw_payload": {
      "date": "2026-04-05",
      "recovery_score": 75,
      "hrv_ms": 42,
      "sleep_hours": 7,
      "daily_strain": 8.5
    }
  }' 2>&1)

echo "Response:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
echo ""

echo -e "${GREEN}✓ Deployment script complete${NC}"
echo ""
echo "Summary of deployment steps:"
echo "1. Run migration SQL in Supabase editor"
echo "2. Deploy health-import via CLI or dashboard"
echo "3. Deploy health-status via CLI or dashboard"
echo "4. Verify endpoints respond correctly"
echo ""
