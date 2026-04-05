/**
 * Stage 1 Verification Script
 * Run in browser console on the deployed site AFTER backend is deployed
 * 
 * Copy and paste entire script into browser console, then call:
 *   verifyStage1()
 */

const Stage1Verify = {
  SUPABASE_URL: 'https://rejalrfmievikabgsakf.supabase.co',
  FUNCTIONS_BASE: 'https://rejalrfmievikabgsakf.supabase.co/functions/v1',
  
  results: {
    passed: [],
    failed: [],
    warnings: []
  },

  log(level, msg) {
    const prefix = {
      pass: '✅',
      fail: '❌',
      warn: '⚠️',
      info: 'ℹ️',
    }[level];
    console.log(`${prefix} ${msg}`);
    if (level === 'pass') this.results.passed.push(msg);
    if (level === 'fail') this.results.failed.push(msg);
    if (level === 'warn') this.results.warnings.push(msg);
  },

  async testHealthStatus() {
    console.log('\n🧪 Test 1: health-status endpoint');
    try {
      const headers = await UserStore._getAuthHeaders();
      const url = `${this.FUNCTIONS_BASE}/health-status?provider=polar`;
      const response = await fetch(url, { headers });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status) {
          this.log('pass', `health-status reachable (status: ${data.status})`);
          return true;
        }
      } else {
        this.log('fail', `health-status returned ${response.status}`);
      }
    } catch (e) {
      this.log('fail', `health-status error: ${e.message}`);
    }
    return false;
  },

  async testHealthImport() {
    console.log('\n🧪 Test 2: health-import endpoint');
    try {
      const headers = await UserStore._getAuthHeaders();
      const url = `${this.FUNCTIONS_BASE}/health-import`;
      const payload = {
        provider: 'polar',
        import_mode: 'manual_upload',
        raw_payload: {
          date: new Date().toISOString().split('T')[0],
          recovery_score: 75,
          hrv_ms: 42,
          sleep_hours: 7,
          daily_strain: 8.5
        }
      };

      const response = await fetch(url, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.import_id) {
          this.log('pass', `health-import successful (import_id: ${data.import_id})`);
          return true;
        }
      } else {
        this.log('fail', `health-import returned ${response.status}`);
        const error = await response.json();
        console.log('Error details:', error);
      }
    } catch (e) {
      this.log('fail', `health-import error: ${e.message}`);
    }
    return false;
  },

  async testProviderRequest() {
    console.log('\n🧪 Test 3: providerRequest function');
    if (typeof providerRequest !== 'function') {
      this.log('fail', 'providerRequest function not found');
      return false;
    }
    
    try {
      // Test read-only endpoint
      const result = await providerRequest('health-status', 'GET');
      if (result && !result.error) {
        this.log('pass', 'providerRequest working (health-status accessible)');
        return true;
      } else {
        this.log('warn', `providerRequest returned: ${JSON.stringify(result)}`);
      }
    } catch (e) {
      this.log('fail', `providerRequest error: ${e.message}`);
    }
    return false;
  },

  async testPolarSync() {
    console.log('\n🧪 Test 4: Polar sync integration');
    if (typeof syncPolarData !== 'function') {
      this.log('fail', 'syncPolarData function not found');
      return false;
    }
    
    try {
      // Create test data
      const testData = {
        date: new Date().toISOString().split('T')[0],
        recovery_score: 70,
        hrv_ms: 40,
        sleep_hours: 7,
        daily_strain: 8
      };

      // Call sync (should update local state and make backend call)
      const result = syncPolarData(testData);
      
      if (result) {
        this.log('pass', 'Polar sync executed (check console for backend call messages)');
        
        // Wait a moment for async backend call
        await new Promise(r => setTimeout(r, 1500));
        return true;
      } else {
        this.log('fail', 'Polar sync returned false');
      }
    } catch (e) {
      this.log('fail', `Polar sync error: ${e.message}`);
    }
    return false;
  },

  printResults() {
    console.log('\n\n📊 STAGE 1 VERIFICATION RESULTS');
    console.log('================================\n');
    
    console.log(`✅ Passed: ${this.results.passed.length}`);
    this.results.passed.forEach(p => console.log(`   • ${p}`));
    
    if (this.results.warnings.length > 0) {
      console.log(`\n⚠️  Warnings: ${this.results.warnings.length}`);
      this.results.warnings.forEach(w => console.log(`   • ${w}`));
    }
    
    if (this.results.failed.length > 0) {
      console.log(`\n❌ Failed: ${this.results.failed.length}`);
      this.results.failed.forEach(f => console.log(`   • ${f}`));
    }

    const totalTests = this.results.passed.length + this.results.failed.length;
    const passRate = Math.round((this.results.passed.length / totalTests) * 100);
    
    console.log(`\nOverall: ${passRate}% (${this.results.passed.length}/${totalTests})\n`);
    
    if (this.results.failed.length === 0) {
      console.log('🎉 All tests passed! Stage 1 deployment is working.\n');
    } else {
      console.log('⚠️  Some tests failed. Check deployment steps.\n');
    }
  },

  async run() {
    console.clear();
    console.log('🚀 Stage 1 Verification Starting...\n');
    
    // Wait for auth system to initialize
    if (!UserStore || !UserStore._getAuthHeaders) {
      this.log('fail', 'UserStore not initialized. Refresh page and try again.');
      return;
    }

    await this.testHealthStatus();
    await this.testHealthImport();
    await this.testProviderRequest();
    await this.testPolarSync();
    
    this.printResults();
  }
};

// Run verification
verifyStage1 = () => Stage1Verify.run();

// Instructions
console.log(`
╔════════════════════════════════════════════════════════╗
║  Stage 1 Verification Ready                           ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Run:  verifyStage1()                                 ║
║                                                        ║
║  Or copy-paste in a new terminal after deployment:    ║
║                                                        ║
║  curl -H "Authorization: Bearer <TOKEN>" \\           ║
║    https://rejalrfmievikabgsakf.supabase.co\\         ║
║    /functions/v1/health-status?provider=polar       ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
`);
