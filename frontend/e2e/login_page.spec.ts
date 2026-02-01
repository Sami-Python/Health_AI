
import { test, expect } from '@playwright/test';

test('login page loads correctly', async ({ page }) => {
    await page.goto('/login');

    // Expect to see the "Health AI Login" heading
    await expect(page.getByRole('heading', { name: /Health AI Login/i })).toBeVisible();

    // Expect to see "Sign in with Google" button
    await expect(page.getByRole('button', { name: /Sign in with Google/i })).toBeVisible();
});

test('navigation from landing to login works', async ({ page }) => {
    await page.goto('/');

    // Click "Log In"
    await page.getByRole('button', { name: /Log In/i }).click();

    // Expect URL to contain /login
    await expect(page).toHaveURL(/.*login/);

    // Verify heading
    await expect(page.getByRole('heading', { name: /Health AI Login/i })).toBeVisible();
});
