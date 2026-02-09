
import { test, expect } from '@playwright/test';

test('login page loads correctly', async ({ page }) => {
    await page.goto('/login');

    // Expect to see the "Health AI Login" heading
    await expect(page.getByRole('heading', { name: /Health AI Login/i })).toBeVisible();

    // Expect to see "Sign in with Google" button
    await expect(page.getByRole('button', { name: /Sign in with Google/i })).toBeVisible();
});

test('Google Login Flow (Mocked)', async ({ page }) => {
    // Inject the TEST_MODE flag before script execution
    await page.addInitScript(() => {
        // @ts-ignore
        window._TEST_MODE_AUTH = true;
    });

    await page.goto('/login');

    // Click "Sign in with Google"
    await page.getByRole('button', { name: /Sign in with Google/i }).click();

    // Expect successful toast
    await expect(page.getByText(/Successfully signed in with Google/i)).toBeVisible();

    // In a real app with AuthContext handling, this might update state.
    // However, since we mock the signInWithGoogle function to just show toast in AuthContext,
    // we verify the toast appears.
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
