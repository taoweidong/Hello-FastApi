import { test as setup, expect } from "@playwright/test";

/** 登录 admin 并保存 storageState（供 smoke/crud project 复用，规避后端登录限流 100 次/分钟） */
setup("登录并保存登录态", async ({ page }) => {
  await page.goto("/#/login");
  // 定位：登录页用户名/密码输入框 + 登录按钮（与 login.spec.ts 已验证的选择器一致）
  const usernameInput = page
    .locator(
      'input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]'
    )
    .first();
  const passwordInput = page.locator('input[type="password"]').first();
  const loginBtn = page
    .locator('button:has-text("登录"), button[type="submit"]')
    .first();

  await usernameInput.fill("admin");
  await passwordInput.fill("admin123");
  await loginBtn.click();

  // 落地首页：根路由 / → /welcome，用轮询断言而非 networkidle
  await page.waitForURL(/welcome/, { timeout: 15000 });
  await expect(page.locator(".sidebar-container").first()).toBeVisible({
    timeout: 15000
  });

  // 持久化登录态（Cookie authorized-token/multiple-tabs + localStorage user-info）
  await page.context().storageState({ path: "test-results/.auth/admin.json" });
});
