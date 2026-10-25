import { expect, test, type Page } from "@playwright/test";
import {
  cleanupByApi,
  fillFormItem,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 菜单管理 CRUD：新增根菜单（工具栏按钮）→ 搜索命中 → 修改 → 删除
 * - 覆盖 2026-10-25 修复的「新增根菜单」死按钮（原 handleAddChild 只置了
 *   showEditPanel，模板缺少渲染入口，点击无反应；已改走 openDialog）
 * - 删除链路为双重确认：行内 el-popconfirm → hook 内 ElMessageBox
 * - 目录类型必填：路由名称 + 路由路径（菜单名称非必填但必填以验证回显）
 */
test.describe.serial("菜单管理 CRUD", () => {
  const prefix = makeUniqueName("menu");
  const menuTitle = `${prefix}目录`;
  const newTitle = `${prefix}新目录`;
  const routeName = `e2e_${prefix}`;
  const routePath = `/e2e-${prefix}`;

  /** 按菜单名称搜索（菜单表为标题客户端过滤） */
  async function searchMenu(page: Page, text: string): Promise<void> {
    await page
      .locator('.search-form input[placeholder*="请输入菜单名称"]')
      .fill(text);
    await page.getByRole("button", { name: "搜索" }).click();
  }

  /** 定位菜单表格行（菜单名称列显示 meta.title） */
  function menuRow(page: Page, text: string) {
    return page.locator(".el-table__row", { hasText: text });
  }

  test("新增根菜单（工具栏按钮）", async ({ page }) => {
    await gotoPage(page, "/system/menu");
    await page.getByRole("button", { name: "新增根菜单" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增菜单" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "菜单名称", menuTitle);
    await fillFormItem(dialog, "路由名称", routeName);
    await fillFormItem(dialog, "路由路径", routePath);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });

    await searchMenu(page, menuTitle);
    await expect(menuRow(page, menuTitle).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("修改菜单名称", async ({ page }) => {
    await gotoPage(page, "/system/menu");
    await searchMenu(page, menuTitle);
    const row = menuRow(page, menuTitle).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "修改" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "修改菜单" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "菜单名称", newTitle);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });

    await searchMenu(page, newTitle);
    await expect(menuRow(page, newTitle).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("删除菜单（popconfirm + 消息框双重确认）", async ({ page }) => {
    await gotoPage(page, "/system/menu");
    await searchMenu(page, newTitle);
    const row = menuRow(page, newTitle).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "删除" }).click();
    // 第一重：行内 el-popconfirm
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();
    // 第二重：hook 内 ElMessageBox 系统提示
    const box = page.locator(".el-message-box");
    await expect(box).toBeVisible();
    await box.getByRole("button", { name: "确定" }).click();
    await expect(box).toBeHidden({ timeout: 10000 });

    await searchMenu(page, newTitle);
    await expect(menuRow(page, newTitle)).toHaveCount(0);
  });

  test.afterAll(async () => {
    await cleanupByApi("/menu", prefix);
  });
});
