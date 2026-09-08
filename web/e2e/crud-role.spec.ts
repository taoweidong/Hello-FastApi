import { expect, test, type Page } from "@playwright/test";
import {
  cleanupByApi,
  fillFormItem,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 角色管理 CRUD 全流程：新增 → 修改 → 删除
 * - describe.serial + crud project workers=1 保证全流程串行
 * - 角色名称在修改步骤会变更，删除/搜索一律用唯一角色标识（code）锚定
 * - 数据唯一命名（e2e_ 前缀），afterAll 走 API 兜底清理
 */
test.describe.serial("角色管理 CRUD", () => {
  const uniquePrefix = makeUniqueName("role");
  const name = `${uniquePrefix}角色`;
  const newName = `${uniquePrefix}新角色`;
  const code = `${uniquePrefix}code`;

  /** 按唯一角色标识搜索过滤，保证目标行位于当前页 */
  async function searchRole(page: Page): Promise<void> {
    await page
      .locator('.search-form input[placeholder*="请输入角色标识"]')
      .fill(code);
    await page.getByRole("button", { name: "搜索" }).click();
  }

  /** 定位角色表格中的目标行（按文本子串匹配） */
  function roleRow(page: Page, text: string) {
    return page.locator(".el-table__row", { hasText: text });
  }

  test("新增角色", async ({ page }) => {
    await gotoPage(page, "/system/role");
    await page.getByRole("button", { name: "新增角色" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增角色" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "角色名称", name);
    await fillFormItem(dialog, "角色标识", code);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });

    await searchRole(page);
    await expect(roleRow(page, name).first()).toBeVisible({ timeout: 10000 });
  });

  test("修改角色名称", async ({ page }) => {
    await gotoPage(page, "/system/role");
    await searchRole(page);
    const row = roleRow(page, code);
    await expect(row.first()).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "修改" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "修改角色" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "角色名称", newName);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });
    await expect(roleRow(page, newName).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("删除角色", async ({ page }) => {
    await gotoPage(page, "/system/role");
    await searchRole(page);
    const row = roleRow(page, newName);
    await expect(row.first()).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "删除" }).click();
    // el-popconfirm 确认（title: 是否确认删除角色名称为...）
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();
    // ElMessageBox 系统提示确认
    const box = page.locator(".el-message-box");
    await expect(box).toBeVisible();
    await box.getByRole("button", { name: "确定" }).click();
    await expect(box).toBeHidden({ timeout: 10000 });
    await expect(roleRow(page, newName)).toHaveCount(0);
  });

  test.afterAll(async () => {
    await cleanupByApi("/role", uniquePrefix);
  });
});
