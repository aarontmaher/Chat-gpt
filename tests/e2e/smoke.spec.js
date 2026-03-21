const { test, expect } = require('@playwright/test');

test.describe('GrapplingMap smoke suite', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('https://aarontmaher.github.io/Chat-gpt/');
    // Wait for debug API + data to be ready
    await page.waitForFunction(() =>
      typeof window.__APP_DEBUG__ !== 'undefined' &&
      window.__APP_DEBUG__.getState().guard > 0,
      { timeout: 20000 }
    );
  });

  test('Page loads with correct title', async ({ page }) => {
    await expect(page).toHaveTitle(/Grappling/i);
  });

  test('All four sections render', async ({ page }) => {
    // Section titles are rendered by JS into .section-title elements
    const sections = await page.locator('.section-title').allTextContents();
    const titles = sections.map(t => t.trim());
    expect(titles).toContain('Wrestling');
    expect(titles).toContain('Guard');
    expect(titles).toContain('Dominant Positions');
    expect(titles).toContain('Scrambles');
  });

  test('Stats show correct edge and guard counts', async ({ page }) => {
    const state = await page.evaluate(() => window.__APP_DEBUG__.getState());
    // _diagNet may not be available until 3D tab is opened; read directly
    const netData = await page.evaluate(() => {
      var net = window._diagNet || {};
      return { edgeCount: net.edgeCount || 0, nodeCount: net.nodeCount || 0,
        inNetwork: net.nodes ? net.nodes.filter(function(n){return n.in_network;}).length : 0 };
    });
    expect(netData.edgeCount).toBe(57);
    expect(state.guard).toBe(19);
    expect(state.sections).toBe(4);
  });

  test('Built-out count is at least 11', async ({ page }) => {
    const state = await page.evaluate(() => window.__APP_DEBUG__.getState());
    expect(state.builtOut).toBeGreaterThanOrEqual(11);
  });

  test('In-network nodes present', async ({ page }) => {
    const netData = await page.evaluate(() => {
      var net = window._diagNet || {};
      return net.nodes ? net.nodes.filter(function(n){return n.in_network;}).length : 0;
    });
    expect(netData).toBeGreaterThanOrEqual(20);
  });

  test('3D graph tab loads canvas', async ({ page }) => {
    await page.click('[data-view="graph3d"]');
    const canvas = page.locator('#g3dCanvas');
    await expect(canvas).toBeVisible({ timeout: 10000 });
  });

  test('Search input focuses on / key', async ({ page }) => {
    // Switch to Reference view first for consistent test
    await page.click('[data-view="reference"]');
    await page.keyboard.press('/');
    const searchInput = page.locator('#refSearch');
    await expect(searchInput).toBeFocused({ timeout: 3000 });
  });

  test('Search filters reference tree', async ({ page }) => {
    // Switch to Reference view first (default is now Network)
    await page.click('[data-view="reference"]');
    const result = await page.evaluate(() => window.__APP_DEBUG__.focusSearch());
    expect(result).toBe('focused');
    await page.keyboard.type('rear naked');
    await page.waitForTimeout(400); // debounce
    // Some tree items should be hidden
    const hiddenCount = await page.evaluate(() => {
      return document.querySelectorAll('.tree-item[style*="display: none"]').length;
    });
    expect(hiddenCount).toBeGreaterThan(0);
  });

  test('Keyboard help panel opens with ?', async ({ page }) => {
    await page.keyboard.press('?');
    const panel = page.locator('#kbdHelpPanel');
    await expect(panel).toBeVisible({ timeout: 3000 });
  });

  test('DIAG panel opens via debug API', async ({ page }) => {
    const result = await page.evaluate(() => window.__APP_DEBUG__.openDiag());
    expect(result).toBe('opened');
    const panel = page.locator('#diagPanel');
    await expect(panel).toBeVisible({ timeout: 3000 });
  });

  test('Section expands on click', async ({ page }) => {
    // Switch to Reference view first (default is now Network)
    await page.click('[data-view="reference"]');
    // Click Dominant Positions section header to expand
    await page.click('.section-title:has-text("Dominant Positions")');
    await page.waitForTimeout(300);
    // After expanding, depth-0 position labels should be visible (e.g. Turtle, Mount)
    // These are direct children of the section, not nested deep
    const sectionBody = page.locator('.section[data-section="Dominant Positions"] .section-body');
    await expect(sectionBody).toBeVisible({ timeout: 5000 });
    // Check that at least one position-level label is visible
    const posLabel = page.locator('.section[data-section="Dominant Positions"] .tree > .tree-item > .node .node-label');
    const count = await posLabel.count();
    expect(count).toBeGreaterThan(0);
  });

  test('No console errors on load', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.reload();
    await page.waitForFunction(() =>
      typeof window.__APP_DEBUG__ !== 'undefined' &&
      window.__APP_DEBUG__.getState().guard > 0,
      { timeout: 20000 }
    );
    await page.waitForTimeout(1000);
    // Filter out expected non-errors (favicon, etc.)
    const real = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('404') &&
      !e.includes('net::ERR')
    );
    expect(real).toHaveLength(0);
  });

});
