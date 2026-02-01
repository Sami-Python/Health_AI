
import { test, expect } from '@playwright/test';

test('landing page has title and login button', async ({ page }) => {
    await page.goto('/');

    // Expect a title "to contain" a substring.
    await expect(page).toHaveTitle(/Health AI/);

    // Expect to see the "Personal AI Coach" heading
    await expect(page.getByRole('heading', { name: /Personal AI Coach/i })).toBeVisible();

    // Expect to see a "Log In" button
    const loginButton = page.getByRole('button', { name: /Log In/i });
    await expect(loginButton).toBeVisible();
});
