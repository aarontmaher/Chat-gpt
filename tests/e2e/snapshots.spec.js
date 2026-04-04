const { test, expect } = require('@playwright/test');

test.describe('Visual snapshots', () => {

  test('Reference panel default state', async ({ page }) => {
    await page.goto('https://www.lauburugrapplingmap.com/');
    await page.waitForFunction(() =>
      typeof window.__APP_DEBUG__ !== 'undefined' &&
      window.__APP_DEBUG__.getState().guard > 0,
      { timeout: 20000 }
    );
    await page.waitForTimeout(500);
    await expect(page).toHaveScreenshot('reference-default.png', { maxDiffPixels: 200 });
  });

  test('3D graph loaded state', async ({ page }) => {
    await page.goto('https://www.lauburugrapplingmap.com/');
    await page.waitForFunction(() =>
      typeof window.__APP_DEBUG__ !== 'undefined' &&
      window.__APP_DEBUG__.getState().guard > 0,
      { timeout: 20000 }
    );
    await page.click('[data-view="graph3d"]');
    await page.waitForSelector('#g3dCanvas', { timeout: 10000 });
    await page.waitForTimeout(3000); // let rotation + force sim settle
    await expect(page).toHaveScreenshot('3d-graph-loaded.png', { maxDiffPixels: 500 });
  });

  test('Section expanded state', async ({ page }) => {
    await page.goto('https://www.lauburugrapplingmap.com/');
    await page.waitForFunction(() =>
      typeof window.__APP_DEBUG__ !== 'undefined' &&
      window.__APP_DEBUG__.getState().guard > 0,
      { timeout: 20000 }
    );
    await page.click('.section-title:has-text("Dominant Positions")');
    await page.waitForTimeout(500);
    await expect(page).toHaveScreenshot('section-expanded.png', { maxDiffPixels: 200 });
  });

});
