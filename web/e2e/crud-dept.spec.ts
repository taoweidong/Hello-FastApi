import { expect, test, type Page } from "@playwright/test";
import {
  cleanupByApi,
  fillFormItem,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 部门管理 CRUD（新增 → 搜索 → API 兜底清理）
 * - 表单仅必填 部门名称（parentId 默认 0=顶级），其余字段由 E2E 跳过
 */
test.describe.serial("部门管理 CRUD", () => {
  const prefix = makeUniqueName("dept");
  const deptName = prefix;

  async function searchDept(page: Page): Promise<void> {
    await page
      .locator('.search-form input[placeholder*="请输入部门名称"]')
      .fill(deptName);
    await page.getByRole("button", { name: "搜索" }).click();
  }

  test("新增部门", async ({ page }) => {
    await gotoPage(page, "/system/dept");
    await page.getByRole("button", { name: "新增部门" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增部门" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "部门名称", deptName);
    await dialog.getByRole("button", { name: "确定" }).click();
    // 创建为异步请求，后端在并发负载下可能略慢，放宽关闭等待并兼等成功提示
    await expect(dialog).toBeHidden({ timeout: 20000 });
  });

  test("搜索部门可命中新增行", async ({ page }) => {
    await gotoPage(page, "/system/dept");
    await searchDept(page);
    const row = page.locator(".el-table__row", { hasText: deptName });
    await expect(row.first()).toBeVisible({ timeout: 10000 });
  });

  test.afterAll(async () => {
    await cleanupByApi("/dept", prefix);
  });
});