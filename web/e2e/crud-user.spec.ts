import { expect, test, type Page } from "@playwright/test";
import {
  cleanupByApi,
  fillFormItem,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 用户管理 CRUD 全流程：新增 → 修改 → 删除
 * - describe.serial + crud project workers=1 保证全流程串行，避免数据竞争
 * - 数据唯一命名（e2e_ 前缀），afterAll 走 API 兜底清理
 */
test.describe.serial("用户管理 CRUD", () => {
  const uniquePrefix = makeUniqueName("user");
  const username = `${uniquePrefix}账号`;
  const nickname = `${uniquePrefix}昵称`;
  const newNickname = `${uniquePrefix}新昵称`;
  const password = "Test@123456";

  /** 按唯一用户名搜索过滤，保证目标行位于当前页 */
  async function searchUser(page: Page): Promise<void> {
    await page
      .locator('.search-form input[placeholder*="请输入用户名称"]')
      .fill(username);
    await page.getByRole("button", { name: "搜索" }).click();
  }

  /** 定位用户表格中的目标行（按文本子串匹配） */
  function userRow(page: Page, text: string) {
    return page.locator(".el-table__row", { hasText: text });
  }

  test("新增用户", async ({ page }) => {
    await gotoPage(page, "/system/user");
    await page.getByRole("button", { name: "新增用户" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增用户" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "用户名称", username);
    await fillFormItem(dialog, "用户昵称", nickname);
    await fillFormItem(dialog, "用户密码", password);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });

    await searchUser(page);
    await expect(userRow(page, username).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("修改用户昵称", async ({ page }) => {
    await gotoPage(page, "/system/user");
    await searchUser(page);
    const row = userRow(page, username);
    await expect(row.first()).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "修改" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "修改用户" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "用户昵称", newNickname);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });
    await expect(userRow(page, newNickname).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("删除用户", async ({ page }) => {
    await gotoPage(page, "/system/user");
    await searchUser(page);
    const row = userRow(page, username);
    await expect(row.first()).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "删除" }).click();
    // el-popconfirm 确认（title: 是否确认删除用户编号为...）
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();
    // ElMessageBox 系统提示确认
    const box = page.locator(".el-message-box");
    await expect(box).toBeVisible();
    await box.getByRole("button", { name: "确定" }).click();
    await expect(box).toBeHidden({ timeout: 10000 });
    await expect(userRow(page, username)).toHaveCount(0);
  });

  test.afterAll(async () => {
    await cleanupByApi("/user", uniquePrefix);
  });
});
