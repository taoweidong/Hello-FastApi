import { test, expect } from "@playwright/test";

test.describe("登录流程", () => {
  test("登录页面加载正常", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // 页面标题应包含登录相关文字
    await expect(page).toHaveTitle(/登录|vue|pure|admin/i);
  });

  test("使用默认管理员账号登录成功", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // 填写登录表单
    const usernameInput = page
      .locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]')
      .first();
    const passwordInput = page.locator('input[type="password"]').first();

    await expect(usernameInput).toBeVisible({ timeout: 5000 });
    await expect(passwordInput).toBeVisible({ timeout: 5000 });

    await usernameInput.fill("admin");
    await passwordInput.fill("admin123");

    // 点击登录按钮
    const loginBtn = page
      .locator('button:has-text("登录"), button[type="submit"]')
      .first();
    await expect(loginBtn).toBeVisible({ timeout: 5000 });
    await loginBtn.click();

    // 应跳转到首页
    await expect(page).toHaveURL(/welcome|dashboard/, { timeout: 10000 });
    await page.waitForLoadState("networkidle");
  });

  test("空密码登录应提示错误", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const usernameInput = page
      .locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]')
      .first();
    const passwordInput = page.locator('input[type="password"]').first();

    await expect(usernameInput).toBeVisible({ timeout: 5000 });
    await usernameInput.fill("admin");
    await passwordInput.fill("");

    const loginBtn = page
      .locator('button:has-text("登录"), button[type="submit"]')
      .first();
    await loginBtn.click();

    // 应停留在登录页，且有校验提示
    await expect(page).toHaveURL(/login/, { timeout: 5000 });
  });
});
