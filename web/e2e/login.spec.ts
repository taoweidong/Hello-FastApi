import { test, expect } from "@playwright/test";

/**
 * 登录流程测试
 *
 * 该用例需要「未登录」状态，因此显式覆盖全局 storageState。
 */
test.use({ storageState: { cookies: [], origins: [] } });

test.describe("登录流程", () => {
  test("登录页面加载正常", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveTitle(/登录|vue|pure|admin/i);
  });

  test("使用默认管理员账号登录成功并跳转首页", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const usernameInput = page
      .locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]')
      .first();
    const passwordInput = page.locator('input[type="password"]').first();

    await expect(usernameInput).toBeVisible({ timeout: 10000 });
    await usernameInput.fill("admin");
    await passwordInput.fill("admin123");

    await page.locator('button:has-text("登录"), button[type="submit"]').first().click();

    // 登录成功后应离开登录页
    await expect(page).not.toHaveURL(/login/, { timeout: 20000 });
    await page.waitForLoadState("networkidle");

    // 侧边栏渲染说明动态路由已加载
    await expect(page.locator(".el-menu").first()).toBeVisible({ timeout: 15000 });
  });

  test("错误的密码应登录失败", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    await page
      .locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]')
      .first()
      .fill("admin");
    await page.locator('input[type="password"]').first().fill("wrong-password");

    await page.locator('button:has-text("登录"), button[type="submit"]').first().click();

    // 应停留在登录页，并出现错误提示
    await expect(page).toHaveURL(/login/, { timeout: 15000 });
    const tip = page.locator(".el-message--error, .el-form-item__error").first();
    await expect(tip).toBeVisible({ timeout: 10000 });
  });

  test("空密码登录应被拦截", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    await page
      .locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]')
      .first()
      .fill("admin");
    await page.locator('input[type="password"]').first().fill("");

    await page.locator('button:has-text("登录"), button[type="submit"]').first().click();

    await expect(page).toHaveURL(/login/, { timeout: 15000 });
  });
});
