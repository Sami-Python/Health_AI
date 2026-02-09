
import { test, expect } from '@playwright/test';

test.describe('Dashboard (Authenticated)', () => {

    // Bypass authentication for this group
    test.use({
        extraHTTPHeaders: {
            'x-test-auth': 'true'
        }
    });

    test.beforeEach(async ({ page }) => {
        // Mock backend APIs to ensure deterministic rendering
        await page.route('*/**/api/workouts/upcoming', async route => {
            await route.fulfill({ json: [] });
        });

        await page.route('*/**/api/workouts/weekly-status', async route => {
            await route.fulfill({ json: { current_load: 150, planned_load: 300, breakdown: {} } });
        });

        await page.route('*/**/api/readiness', async route => {
            await route.fulfill({ json: { readiness: 85, date: new Date().toISOString() } });
        });

        await page.route('*/**/api/goals', async route => {
            await route.fulfill({ json: [] });
        });

        // Enable Test Mode in Frontend
        // We set the env var in the browser context if possible, or we rely on the build time env.
        // But since we can't change build env at runtime easily without rebuilding, 
        // we might need to rely on a different mechanism if the env var approach isn't sufficient for runtime switching.
        // However, for this implementation, we assume the app is running with the env var OR we can mock the return of `useAuth`.
        // Actually, the previous implementation checks `process.env`.
        // If the app is already running (via `webServer`), we can't change its process.env.
        // BUT, Next.js 'public' env vars are inlined at build time.
        // If we want dynamic switching, we should check `window.TEST_MODE`.
        // Let's modify AuthContext to ALSO check window.TEST_MODE for easier Playwright injection.
    });

    // We will assume for now we can inject window property
    test('loads dashboard components', async ({ page }) => {
        // Inject the TEST_MODE flag before script execution
        // Inject the TEST_MODE flag before script execution
        await page.addInitScript(() => {
            // @ts-ignore
            window._TEST_MODE_AUTH = true;
        });

        await page.goto('/dashboard');

        // Use a slight delay to allow the effect to run
        await page.waitForTimeout(1000);

        // Verify key components
        // Verify key components

        // 1. Check for User Menu (Avatar) as a proxy for successful auth/nav loaded
        // It usually is a button with an image or initials
        await expect(page.locator('button').filter({ hasText: /TU|Test User/i }).first()).toBeVisible({ timeout: 10000 }).catch(() => {
            // Fallback: look for the user menu trigger generally if text match fails
            return expect(page.getByRole('button', { name: /open user menu/i })).toBeVisible();
        });

        // 2. Headings (e.g. "Weekly Status", "Readiness")
        // The dashboard might not have a single h1 "Dashboard" visible if it uses cards.
        // Let's look for "Weekly Status" or similar known widgets.
        await expect(page.getByText(/Weekly Status/i)).toBeVisible();

        // 3. Check for specific widgets if possible (using text locators)
        // await expect(page.getByText(/Current Load/i)).toBeVisible();
    });
});
