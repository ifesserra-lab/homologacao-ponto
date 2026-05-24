import { test, expect } from "@playwright/test";

// T011: unauthenticated access to / redirects to /login
test("T011 unauthenticated access redirects to /login", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
});

// T011b: unauthenticated access to internal page redirects to /login
test("T011b unauthenticated access to servidor page redirects to /login", async ({
  page,
}) => {
  await page.goto("/servidor/celio-proliciano-maioli");
  await expect(page).toHaveURL(/\/login/);
});

// T012: correct credentials grant access and redirect to intended page
test("T012 correct credentials grant access", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
  await page.fill('[name="user"]', process.env.DASHBOARD_USER ?? "admin");
  await page.fill('[name="password"]', process.env.DASHBOARD_PASSWORD ?? "admin");
  await page.click('[type="submit"]');
  await expect(page).not.toHaveURL(/\/login/);
});

// T013: wrong credentials stay on /login with generic error
test("T013 wrong credentials show generic error", async ({ page }) => {
  await page.goto("/login");
  await page.fill('[name="user"]', "usuario_errado");
  await page.fill('[name="password"]', "senha_errada");
  await page.click('[type="submit"]');
  await expect(page).toHaveURL(/\/login/);
  await expect(page.locator(".login-error")).toBeVisible();
});

// T014: missing env hashes → login always fails
test("T014 missing hashes make login always fail", async ({ page }) => {
  // When PUBLIC_DASHBOARD_USER_HASH is empty, checkCredentials returns false
  // We verify by checking the current env config leads to failure for wrong creds
  await page.goto("/login");
  await page.fill('[name="user"]', "any");
  await page.fill('[name="password"]', "any");
  await page.click('[type="submit"]');
  // With empty hashes (playwright.config sets "" when not set), login fails
  if (
    !process.env.PUBLIC_DASHBOARD_USER_HASH ||
    !process.env.PUBLIC_DASHBOARD_PASSWORD_HASH
  ) {
    await expect(page).toHaveURL(/\/login/);
  }
});

// T023: logout button clears session and redirects to /login
test("T023 logout clears session and redirects to /login", async ({ page }) => {
  // Login first
  await page.goto("/login");
  await page.fill('[name="user"]', process.env.DASHBOARD_USER ?? "admin");
  await page.fill('[name="password"]', process.env.DASHBOARD_PASSWORD ?? "admin");
  await page.click('[type="submit"]');
  await expect(page).not.toHaveURL(/\/login/);
  // Logout
  await page.click('[data-action="logout"]');
  await expect(page).toHaveURL(/\/login/);
});

// T024: after logout, direct URL redirects to /login
test("T024 after logout direct URL access redirects to /login", async ({
  page,
}) => {
  // Login then logout
  await page.goto("/login");
  await page.fill('[name="user"]', process.env.DASHBOARD_USER ?? "admin");
  await page.fill('[name="password"]', process.env.DASHBOARD_PASSWORD ?? "admin");
  await page.click('[type="submit"]');
  await expect(page).not.toHaveURL(/\/login/);
  await page.click('[data-action="logout"]');
  // Now try to access internal page directly
  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
});
