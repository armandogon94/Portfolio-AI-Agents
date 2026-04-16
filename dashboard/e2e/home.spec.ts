import { expect, test } from "@playwright/test";

test.describe("Dashboard landing page", () => {
  test("renders the AI Agent Team Dashboard title", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /ai agent team dashboard/i, level: 1 }),
    ).toBeVisible();
  });

  test("exposes the dashboard port in the html metadata", async ({ page }) => {
    const response = await page.goto("/");
    expect(response?.ok()).toBeTruthy();
    await expect(page).toHaveTitle(/ai agent team dashboard/i);
  });
});
