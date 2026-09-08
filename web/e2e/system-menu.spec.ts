import { expect, test } from "@playwright/test";
import { MODULES, gotoModule, rowCount, submitDialog, waitTableReady } from "./helpers";

/**
 * 菜单管理：树形列表加载、展开、新增弹窗
 */
test.describe("系统管理 - 菜单管理", () => {
  test("菜单树形列表正常加载且存在数据", async ({ page }) => {
    await gotoModule(page, MODULES.menu);
    await expect(page.locator(".el-table").first()).toBeVisible();
    expect(await rowCount(page)).toBeGreaterThan(0);
  });

  test("新增菜单弹窗可正常打开与取消", async ({ page }) => {
    await gotoModule(page, MODULES.menu);

    await page.locator('button:has-text("新增")').first().click();
    const dialog = page.locator(".el-dialog:visible, .el-drawer:visible").last();
    await expect(dialog).toBeVisible({ timeout: 10000 });
    await dialog.locator('button:has-text("取消")').last().click();
    await waitTableReady(page);
  });
});
