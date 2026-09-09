import { expect, test, type Page } from "@playwright/test";
import {
  cleanupByApi,
  fillFormItem,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * IP 规则管理 CRUD（新增 → 表格可见验证 → API 兜底清理）
 * - 搜索表单不含 IP 地址输入框，仅有 规则类型/状态下拉，因此不验证搜索，改为表格行可见验证
 */
test.describe.serial("IP 规则管理 CRUD", () => {
  const prefix = makeUniqueName("ipr");
  const ipAddress = `192.168.${Math.floor(Math.random() * 250) + 1}.${
    Math.floor(Math.random() * 250) + 1
  }`;

  async function gotoIpRuleAndSearch(page: Page): Promise<void> {
    await gotoPage(page, "/system/ip-rule");
    // 选择规则类型为黑名单并搜索，缩小结果集以稳定定位新增行
    await page
      .locator('.search-form .el-select')
      .first()
      .click();
    await page.getByRole("option", { name: "黑名单" }).first().click();
    await page.getByRole("button", { name: "搜索" }).click();
    await page.waitForTimeout(500);
  }

  test("新增 IP 规则", async ({ page }) => {
    await gotoPage(page, "/system/ip-rule");
    await page.getByRole("button", { name: "新增规则" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增IP规则" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "IP地址", ipAddress);
    await fillFormItem(dialog, "原因", "E2E 自动化测试");
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });
  });

  test("表格可定位到新增 IP", async ({ page }) => {
    await gotoIpRuleAndSearch(page);
    const row = page.locator(".el-table__row", { hasText: ipAddress });
    await expect(row.first()).toBeVisible({ timeout: 10000 });
  });

  test.afterAll(async () => {
    await cleanupByApi("/ip-rule", prefix);
  });
});