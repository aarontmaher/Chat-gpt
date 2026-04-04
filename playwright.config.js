const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: 'https://www.lauburugrapplingmap.com/',
    headless: true,
    viewport: { width: 1280, height: 720 },
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } }
  ],
  reporter: [['list'], ['json', { outputFile: 'tests/results.json' }]]
});
