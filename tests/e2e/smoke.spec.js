const { test, expect } = require('@playwright/test');

test.describe('GrapplingMap smoke suite', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('https://www.lauburugrapplingmap.com/');
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
    // Headless Chromium may lack WebGL support, causing the app to replace
    // the canvas with a graceful fallback message. Accept either outcome.
    const canvas = page.locator('#g3dCanvas');
    const fallback = page.locator('#graph3dView:has-text("Network view is not available")');
    const result = await Promise.race([
      canvas.waitFor({ state: 'visible', timeout: 10000 }).then(() => 'canvas'),
      fallback.waitFor({ state: 'visible', timeout: 10000 }).then(() => 'fallback'),
    ]);
    expect(['canvas', 'fallback']).toContain(result);
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

  test('Journal opens via J key', async ({ page }) => {
    await page.keyboard.press('j');
    const overlay = page.locator('#sparringJournalOverlay');
    await expect(overlay).toBeVisible({ timeout: 5000 });
  });

  test('Coach opens via C key', async ({ page }) => {
    await page.keyboard.press('c');
    const overlay = page.locator('#coachOverlay');
    await expect(overlay).toBeVisible({ timeout: 5000 });
  });

  test('Keyboard help shows J and C shortcuts', async ({ page }) => {
    await page.keyboard.press('?');
    const panel = page.locator('#kbdHelpPanel');
    await expect(panel).toBeVisible({ timeout: 3000 });
    const text = await panel.textContent();
    expect(text).toContain('J');
    expect(text).toContain('C');
  });

  test('Menu contains new items', async ({ page }) => {
    await page.click('#headerMenuToggle');
    const menu = page.locator('#headerMenu');
    await expect(menu).toBeVisible({ timeout: 3000 });
    const text = await menu.textContent();
    expect(text).toContain('Sparring Journal');
    expect(text).toContain('Coach');
    expect(text).toContain('Chains');
    expect(text).toContain('Game Summary');
  });

  test('Daily suggestion card exists in DOM', async ({ page }) => {
    await page.click('[data-view="reference"]');
    const card = page.locator('#dailySuggestionCard');
    // Card exists in the DOM (may be hidden if no progress data)
    await expect(card).toHaveCount(1);
  });

  test('Search alias resolves', async ({ page }) => {
    // CW51: BJJ alias system — "armbar" should resolve to "arm bar"
    await page.click('[data-view="reference"]');
    const result = await page.evaluate(() => window.__APP_DEBUG__.focusSearch());
    expect(result).toBe('focused');
    await page.keyboard.type('armbar');
    await page.waitForTimeout(400); // debounce
    // At least one tree item should still be visible (alias resolved)
    const visibleCount = await page.evaluate(() => {
      return document.querySelectorAll('.tree-item:not([style*="display: none"])').length;
    });
    expect(visibleCount).toBeGreaterThan(0);
  });

  test('Filter buttons exist and are clickable', async ({ page }) => {
    await page.click('[data-view="reference"]');
    const filterBtns = page.locator('#refBottomBar .g3d-tb-btn[data-filter]');
    const count = await filterBtns.count();
    expect(count).toBeGreaterThanOrEqual(3);
    // Click "All" button — verify no error
    const allBtn = page.locator('#refBottomBar .g3d-tb-btn[data-filter="all"]');
    await allBtn.click();
  });

  test('Share button exists', async ({ page }) => {
    await page.click('[data-view="reference"]');
    // Expand a section and select a position
    await page.click('.section-title:has-text("Guard")');
    await page.waitForTimeout(300);
    const posLabel = page.locator('.section[data-section="Guard"] .tree > .tree-item > .node .node-label');
    await posLabel.first().click();
    await page.waitForTimeout(300);
    // Verify a share button or share icon is visible
    const shareBtn = page.locator('[id*="share"], [class*="share"], button:has-text("Share"), [title*="Share"], [aria-label*="Share"]');
    const shareCount = await shareBtn.count();
    expect(shareCount).toBeGreaterThan(0);
  });

  test('Recenter button on graph', async ({ page }) => {
    await page.click('[data-view="graph3d"]');
    // Headless Chromium may lack WebGL — accept button in DOM or fallback
    const fallback = page.locator('#graph3dView:has-text("Network view is not available")');
    const recenterBtn = page.locator('#g3dRecenterBtn');
    const result = await Promise.race([
      recenterBtn.waitFor({ state: 'attached', timeout: 10000 }).then(() => 'button'),
      fallback.waitFor({ state: 'visible', timeout: 10000 }).then(() => 'fallback'),
    ]);
    expect(['button', 'fallback']).toContain(result);
  });

  test('Legend exists on graph', async ({ page }) => {
    await page.click('[data-view="graph3d"]');
    // Headless Chromium may lack WebGL — accept legend or fallback
    const fallback = page.locator('#graph3dView:has-text("Network view is not available")');
    const legendContainer = page.locator('#g3dLegend');
    const result = await Promise.race([
      legendContainer.waitFor({ state: 'attached', timeout: 10000 }).then(async () => {
        // Legend container exists; wait for pills to be populated
        await page.waitForTimeout(2000);
        const pills = await page.locator('#g3dLegend [data-sec-idx]').count();
        return pills >= 1 ? 'legend' : 'empty';
      }),
      fallback.waitFor({ state: 'visible', timeout: 10000 }).then(() => 'fallback'),
    ]);
    expect(['legend', 'fallback']).toContain(result);
  });

  test('Game Summary opens from menu', async ({ page }) => {
    await page.click('#headerMenuToggle');
    const menu = page.locator('#headerMenu');
    await expect(menu).toBeVisible({ timeout: 3000 });
    await page.click('#headerMenu >> text=Game Summary');
    await page.waitForTimeout(500);
    // Verify the list panel opens with Game Summary content
    const panel = page.locator('#gameSummaryOverlay, #gameSummaryPanel, [class*="game-summary"], #listPanel:has-text("Game Summary")');
    const count = await panel.count();
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
      !e.includes('net::ERR') &&
      !e.includes('WebGL') // headless Chromium may lack WebGL support
    );
    expect(real).toHaveLength(0);
  });

});
