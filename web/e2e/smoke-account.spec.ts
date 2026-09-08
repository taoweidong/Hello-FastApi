import { expect, test } from "@playwright/test";
import { MODULES, gotoModule, waitTableReady } from "./helpers";

/**
 * 账户设置页：个人信息、安全日志等
 */
test.describe("账户设置", () => {
  test("账户设置页面正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.accountSettings);

    await expect(page).toHaveURL(/account-settings/);
    await expect(page.locator("body")).toContainText(/账户设置|个人信息|安全/);
    await waitTableReady(page);
  });
});
