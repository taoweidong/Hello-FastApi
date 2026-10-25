import { expect, test, type Page } from "@playwright/test";
import {
  cleanupByApi,
  confirmMessageBox,
  fillFormItem,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 岗位管理 CRUD：新增岗位 → 搜索命中 → 修改 → 批量删除
 * - 弹窗标题：`${title}岗位`（新增岗位 / 修改岗位）
 * - 必填：岗位编码 + 岗位名称（状态开关有默认值，无需交互）
 * - 删除链路：选中行 → 工具栏「批量删除」popconfirm
 */
test.describe.serial("岗位管理 CRUD", () => {
  const prefix = makeUniqueName("post");
  const postCode = `e2e_${prefix}`;
  const postName = `${prefix}岗位`;
  const newPostName = `${prefix}新岗位`;

  async function searchPost(page: Page, text: string): Promise<void> {
    await page
      .locator('.search-form input[placeholder*="请输入岗位名称"]')
      .fill(text);
    await page.getByRole("button", { name: "搜索" }).click();
  }

  function postRow(page: Page, text: string) {
    return page.locator(".el-table__row", { hasText: text });
  }

  test("新增岗位", async ({ page }) => {
    await gotoPage(page, "/system/post");
    await page.getByRole("button", { name: "新增岗位" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增岗位" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "岗位编码", postCode);
    await fillFormItem(dialog, "岗位名称", postName);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });

    await searchPost(page, postName);
    await expect(postRow(page, postName).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("修改岗位名称", async ({ page }) => {
    await gotoPage(page, "/system/post");
    await searchPost(page, postName);
    const row = postRow(page, postName).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "修改" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "修改岗位" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "岗位名称", newPostName);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });

    await searchPost(page, newPostName);
    await expect(postRow(page, newPostName).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("批量删除岗位", async ({ page }) => {
    await gotoPage(page, "/system/post");
    await searchPost(page, newPostName);
    const row = postRow(page, newPostName).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    await row.locator(".el-checkbox").click();
    await page.getByRole("button", { name: "批量删除" }).click();
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();
    // useCrudTable.handleBatchDelete 还会再弹一层 ElMessageBox.confirm
    await confirmMessageBox(page);
    await expect(postRow(page, newPostName)).toHaveCount(0, { timeout: 10000 });
  });

  test.afterAll(async () => {
    await cleanupByApi("/post", prefix);
  });
});
