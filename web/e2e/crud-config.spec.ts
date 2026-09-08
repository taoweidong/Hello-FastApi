import { expect, test } from "@playwright/test";
import {
  MODULES,
  fillDialog,
  gotoModule,
  search,
  submitDialog,
  uniqueName,
  waitTableReady
} from "./helpers";

/**
 * 系统配置端到端全流程：列表 → 新增 → 搜索 → 删除
 */
test.describe("系统管理 - 系统配置", () => {
  const configKey = uniqueName("e2e.config");

  test("配置列表页面正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.config);
    await expect(page.locator(".el-table").first()).toBeVisible();
  });

  test("新增配置后可被搜索到（随后清理）", async ({ page }) => {
    await gotoModule(page, MODULES.config);

    await page.locator('button:has-text("新增")').first().click();
    await fillDialog(page, {
      请输入配置键: configKey,
      "请输入配置值(JSON格式)": '{"enabled":true}',
      请输入描述: "E2E 自动化测试创建"
    });
    await submitDialog(page);
    await waitTableReady(page);

    await search(page, "请输入配置键", configKey);
    await expect(page.locator(".el-table__body-wrapper").first()).toContainText(configKey);

    // 清理
    await page.locator(".el-table__body-wrapper .el-table__row").first().hover();
    await page.locator('.el-table__row:first-child button:has-text("删除")').first().click();
    await page.locator(".el-message-box").last().locator('button:has-text("确定")').click();
    await waitTableReady(page);
  });
});
