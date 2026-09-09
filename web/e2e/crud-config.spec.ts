import { expect, test, type Page } from "@playwright/test";
import {
  cleanupByApi,
  fillFormItem,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 系统配置 CRUD（新增 → 搜索 → API 兜底清理）
 * - 使用 utils/helpers 的 robust 模式：getByRole / fillFormItem / cleanupByApi
 * - 避免旧 helpers 中 `button:has-text("新增")` 的脆弱匹配
 */
test.describe.serial("系统配置 CRUD", () => {
  const prefix = makeUniqueName("cfg");
  const configKey = `${prefix}_key`;
  const configValue = JSON.stringify({ enabled: true, source: "e2e" });

  async function searchKey(page: Page): Promise<void> {
    await page
      .locator('.search-form input[placeholder*="请输入配置键"]')
      .fill(configKey);
    await page.getByRole("button", { name: "搜索" }).click();
  }

  test("新增配置", async ({ page }) => {
    await gotoPage(page, "/system/config");
    await page.getByRole("button", { name: "新增配置" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增配置" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "配置键", configKey);
    await fillFormItem(dialog, "配置值", configValue);
    await fillFormItem(dialog, "描述", "E2E 自动化测试创建");
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });
  });

  test("搜索配置可命中新增行", async ({ page }) => {
    await gotoPage(page, "/system/config");
    await searchKey(page);
    const row = page.locator(".el-table__row", { hasText: configKey });
    await expect(row.first()).toBeVisible({ timeout: 10000 });
  });

  test.afterAll(async () => {
    await cleanupByApi("/config", prefix);
  });
});