import { expect, test, type Page } from "@playwright/test";
import {
  cleanupByApi,
  confirmMessageBox,
  fillFormItem,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 通知公告 CRUD：发布公告 → 搜索命中 → 修改 → 删除 → 批量删除
 * - 弹窗标题来自 useDialogForm：`${title}公告`（新增公告 / 修改公告）
 * - 公告类型下拉有默认值（noticeType=1），无需交互即可通过校验
 * - 删除链路：行内 el-popconfirm；批量删除：选中行 → 工具栏 popconfirm
 */
test.describe.serial("通知公告 CRUD", () => {
  const prefix = makeUniqueName("notice");
  const title = `${prefix}标题`;
  const newTitle = `${prefix}新标题`;
  const content = "E2E 自动化测试发布的公告内容";

  async function searchNotice(page: Page, text: string): Promise<void> {
    await page
      .locator('.search-form input[placeholder*="请输入公告标题"]')
      .fill(text);
    await page.getByRole("button", { name: "搜索" }).click();
  }

  function noticeRow(page: Page, text: string) {
    return page.locator(".el-table__row", { hasText: text });
  }

  test("发布公告", async ({ page }) => {
    await gotoPage(page, "/system/notice");
    await page.getByRole("button", { name: "发布公告" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增公告" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "公告标题", title);
    await fillFormItem(dialog, "公告内容", content);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });

    await searchNotice(page, title);
    await expect(noticeRow(page, title).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("修改公告标题", async ({ page }) => {
    await gotoPage(page, "/system/notice");
    await searchNotice(page, title);
    const row = noticeRow(page, title).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "修改" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "修改公告" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "公告标题", newTitle);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });

    await searchNotice(page, newTitle);
    await expect(noticeRow(page, newTitle).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("批量删除公告", async ({ page }) => {
    await gotoPage(page, "/system/notice");
    await searchNotice(page, newTitle);
    const row = noticeRow(page, newTitle).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    // 勾选首行（selection 列）
    await row.locator(".el-checkbox").click();
    await page.getByRole("button", { name: "批量删除" }).click();
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();
    // useCrudTable.handleBatchDelete 还会再弹一层 ElMessageBox.confirm
    await confirmMessageBox(page);
    await expect(noticeRow(page, newTitle)).toHaveCount(0, { timeout: 10000 });
  });

  test("删除公告（行内）", async ({ page }) => {
    // 重新发布一条，验证行内删除链路
    await gotoPage(page, "/system/notice");
    await page.getByRole("button", { name: "发布公告" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增公告" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "公告标题", title);
    await fillFormItem(dialog, "公告内容", content);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 15000 });

    await searchNotice(page, title);
    const row = noticeRow(page, title).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "删除" }).click();
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();
    // useCrudTable.handleDelete 还会再弹一层 ElMessageBox.confirm
    await confirmMessageBox(page);
    await expect(noticeRow(page, title)).toHaveCount(0, { timeout: 10000 });
  });

  test.afterAll(async () => {
    await cleanupByApi("/notice", prefix);
  });
});
