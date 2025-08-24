import { test, expect } from '@playwright/test';

test('login → navigate to demo', async ({ page }) => {
  await page.goto('http://localhost:5173/login');
  await page.fill('input[type="email"]', 'user@example.com');
  await page.fill('input[type="password"]', 'demo');
  await page.click('button:has-text("Sign In")');
  await page.waitForURL('**/');
  await expect(page).toHaveURL(/localhost:5173/);
  await page.goto('http://localhost:5173/demo');
  await expect(page).toHaveURL(/\/demo/);
});



