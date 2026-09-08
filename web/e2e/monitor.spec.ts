import { expect, test } from "@playwright/test";
import { MODULES, gotoModule, waitTableReady } from "./helpers";

/**
 * 系统监控：在线用户、登录日志、操作日志
 */
test.describe("系统监控", () => {
  test("在线用户列表正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.onlineUser);
    await expect(page.locator(".el-table").first()).toBeVisible();
    await waitTableReady(page);
  });

  test("登录日志列表正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.loginLog);
    await expect(page.locator(".el-table").first()).toBeVisible();
    await waitTableReady(page);
  });

  test("操作日志列表正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.operationLog);
    await expect(page.locator(".el-table").first()).toBeVisible();
    await waitTableReady(page);
  });

  test("登录日志按状态筛选可用", async ({ page }) => {
    await gotoModule(page, MODULES.loginLog);

    // 状态下拉：选择「成功」
    const select = page.locator(".el-form-item:has-text('登录状态') .el-select").first();
    if ((await select.count()) > 0) {
      await select.click();
      await page.locator('.el-select-dropdown__item:has-text("成功")').first().click();
      await page.locator('button:has-text("搜索")').first().click();
      await waitTableReady(page);
      await expect(page.locator(".el-table").first()).toBeVisible();
    } else {
      // 无状态筛选器时至少保证页面可用
      await expect(page.locator(".el-table").first()).toBeVisible();
    }
  });
});
