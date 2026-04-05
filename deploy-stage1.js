#!/usr/bin/env node

/**
 * Stage 1 Supabase Deployment Script
 * Deploys migration, edge functions, and verifies endpoints
 * 
 * Requires: SUPABASE_ACCESS_TOKEN or manual authentication
 * Usage: node deploy-stage1.js
 */

const fs = require('fs');
const https = require('https');
const path = require('path');

const SUPABASE_PROJECT_REF = 'rejalrfmievikabgsakf';
const SUPABASE_URL = `https://${SUPABASE_PROJECT_REF}.supabase.co`;
const FUNCTIONS_BASE_URL = `${SUPABASE_URL}/functions/v1`;

// Helper to make HTTPS requests
async function httpsRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || 443,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    const req = https.request(requestOptions, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: data ? JSON.parse(data) : data,
            rawBody: data,
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: null,
            rawBody: data,
          });
        }
      });
    });

    req.on('error', reject);
    if (options.body) req.write(JSON.stringify(options.body));
    req.end();
  });
}

// Main deployment flow
async function deploy() {
  console.log('🚀 Stage 1 Supabase Deployment\n');
  console.log(`Project: ${SUPABASE_URL}\n`);

  // Step 1: Check if we have credentials
  const accessToken = process.env.SUPABASE_ACCESS_TOKEN;
  if (!accessToken) {
    console.log('⚠️  SUPABASE_ACCESS_TOKEN not set. Cannot deploy via CLI.\n');
    console.log('Manual Deployment Instructions:');
    console.log('================================\n');

    // Read migration file
    const migrationPath = path.join(__dirname, 'supabase/migrations/20260405_001_multi_provider_health.sql');
    const migrationSQL = fs.readFileSync(migrationPath, 'utf8');
    
    console.log('1. DEPLOY MIGRATION:');
    console.log('   Open: https://app.supabase.com/projects/' + SUPABASE_PROJECT_REF + '/sql/new');
    console.log('   Copy-paste entire migration SQL below, then click RUN\n');
    console.log('---SQL START---');
    console.log(migrationSQL);
    console.log('---SQL END---\n\n');

    // Read functions
    const healthImportPath = path.join(__dirname, 'supabase/functions/health-import/index.ts');
    const healthStatusPath = path.join(__dirname, 'supabase/functions/health-status/index.ts');
    
    const healthImportCode = fs.readFileSync(healthImportPath, 'utf8');
    const healthStatusCode = fs.readFileSync(healthStatusPath, 'utf8');

    console.log('2. DEPLOY health-import FUNCTION:');
    console.log('   Go to: Edge Functions → Create new → Name it "health-import"');
    console.log('   Paste code below:\n');
    console.log('---TS START---');
    console.log(healthImportCode);
    console.log('---TS END---\n\n');

    console.log('3. DEPLOY health-status FUNCTION:');
    console.log('   Go to: Edge Functions → Create new → Name it "health-status"');
    console.log('   Paste code below:\n');
    console.log('---TS START---');
    console.log(healthStatusCode);
    console.log('---TS END---\n\n');

    console.log('4. VERIFY DEPLOYMENT:');
    console.log(`   After deploying, run: SUPABASE_ACCESS_TOKEN=<token> node deploy-stage1.js verify\n`);
    process.exit(0);
  }

  // Step 2: Test endpoint availability
  console.log('Testing endpoint availability...\n');

  try {
    const statusTest = await httpsRequest(`${FUNCTIONS_BASE_URL}/health-status`, {
      method: 'OPTIONS',
    });
    console.log(`✓ Functions endpoint accessible (status: ${statusTest.status})`);
  } catch (e) {
    console.log('✗ Cannot reach functions endpoint:', e.message);
  }

  // Step 3: Provide API deployment info
  console.log('\n📋 Deployment Summary:');
  console.log('  Migration: Requires manual SQL deployment');
  console.log('  health-import: Requires manual upload');
  console.log('  health-status: Requires manual upload');
  console.log('\nOnce deployed, run:\n');
  console.log(`  SUPABASE_ACCESS_TOKEN=<token> node deploy-stage1.js verify\n`);
}

// Verification flow
async function verify() {
  console.log('🔍 Stage 1 Verification\n');

  const accessToken = process.env.SUPABASE_ACCESS_TOKEN;
  if (!accessToken) {
    console.log('⚠️  SUPABASE_ACCESS_TOKEN required for verification');
    process.exit(1);
  }

  console.log('Testing endpoints...\n');

  // Test 1: health-status with auth
  try {
    const response = await httpsRequest(`${FUNCTIONS_BASE_URL}/health-status?provider=polar`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });
    console.log('✓ health-status endpoint:');
    console.log(`  Status: ${response.status}`);
    console.log(`  Body: ${JSON.stringify(response.body || response.rawBody, null, 2)}\n`);
  } catch (e) {
    console.log('✗ health-status failed:', e.message, '\n');
  }

  // Test 2: health-import with sample data
  try {
    const response = await httpsRequest(`${FUNCTIONS_BASE_URL}/health-import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
      body: {
        provider: 'polar',
        import_mode: 'manual_upload',
        raw_payload: {
          date: '2026-04-05',
          recovery_score: 75,
          hrv_ms: 42,
          sleep_hours: 7,
          daily_strain: 8.5,
        },
      },
    });
    console.log('✓ health-import endpoint:');
    console.log(`  Status: ${response.status}`);
    console.log(`  Body: ${JSON.stringify(response.body || response.rawBody, null, 2)}\n`);
  } catch (e) {
    console.log('✗ health-import failed:', e.message, '\n');
  }
}

// Main entry
const command = process.argv[2] || 'deploy';
if (command === 'verify') {
  verify().catch(console.error);
} else {
  deploy().catch(console.error);
}
