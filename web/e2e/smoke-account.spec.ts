import { expect, test } from "@playwright/test";
import { MODULES } from "./helpers";
import { gotoPage } from "./utils/helpers";

/**
 * 账户设置页：个人信息、安全日志等（/account-settings 为 remaining 全屏路由，
 * 不渲染标准 .app-main 布局，故复用 utils/helpers 的 gotoPage 做 hash 导航）
 */
test.describe("账户设置", () => {
  test("账户设置页面正常加载", async ({ page }) => {
    await gotoPage(page, MODULES.accountSettings);

    await expect(page).toHaveURL(/account-settings/);
    await expect(page.locator("body")).toContainText(/账户设置|个人信息|安全/);
  });
});
