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
 * IP 规则管理端到端全流程：列表 → 新增 → 搜索 → 删除
 */
test.describe("系统管理 - IP 规则管理", () => {
  // 使用测试网段，避免影响真实访问
  const ip = `10.200.${Math.floor(Math.random() * 200) + 1}.${Math.floor(Math.random() * 200) + 1}`;

  test("IP 规则列表页面正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.ipRule);
    await expect(page.locator(".el-table").first()).toBeVisible();
  });

  test("新增 IP 规则后可被搜索到（随后清理）", async ({ page }) => {
    await gotoModule(page, MODULES.ipRule);

    await page.locator('button:has-text("新增")').first().click();
    await fillDialog(page, {
      请输入IP地址: ip,
      请输入原因: "E2E 自动化测试"
    });
    await submitDialog(page);
    await waitTableReady(page);

    await search(page, "请输入IP地址", ip);
    await expect(page.locator(".el-table__body-wrapper").first()).toContainText(ip);

    // 清理
    await page.locator(".el-table__body-wrapper .el-table__row").first().hover();
    await page.locator('.el-table__row:first-child button:has-text("删除")').first().click();
    await page.locator(".el-message-box").last().locator('button:has-text("确定")').click();
    await waitTableReady(page);
  });
});
