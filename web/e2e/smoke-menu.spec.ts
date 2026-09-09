import { expect, test } from "@playwright/test";
import { gotoPage } from "./utils/helpers";

/**
 * 菜单管理冒烟：列表加载 + 行级新增弹窗打开/取消
 * - 已知应用缺陷：菜单页"新增根菜单"按钮仅设置了 showEditPanel=true，
 *   但 menu/index.vue 模板中缺少对应的 <el-drawer> 渲染入口（dead control）。
 *   因此冒烟只验证可用的行级"新增"按钮（打开 el-dialog）。
 */
test.describe("系统管理 - 菜单管理", () => {
  test("菜单表格正常加载", async ({ page }) => {
    await gotoPage(page, "/system/menu");
    await expect(page.locator(".el-table").first()).toBeVisible();
    // 菜单表格为树形（懒加载/默认折叠），不做行数严格断言，仅确认工具栏渲染
    await expect(
      page.getByRole("button", { name: "新增根菜单" })
    ).toBeVisible();
  });

  test("行级新增菜单弹窗可正常打开与取消", async ({ page }) => {
    await gotoPage(page, "/system/menu");
    const firstRow = page.locator(".el-table__row").first();
    await firstRow.hover();
    await firstRow.getByRole("button", { name: "新增" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增菜单" });
    await expect(dialog).toBeVisible({ timeout: 10000 });
    await dialog.getByRole("button", { name: "取消" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });
  });
});