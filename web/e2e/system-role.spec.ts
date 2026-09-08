import { expect, test } from "@playwright/test";
import {
  MODULES,
  cancelDialog,
  fillDialog,
  gotoModule,
  search,
  submitDialog,
  uniqueName,
  waitTableReady
} from "./helpers";

/**
 * 角色管理端到端全流程：列表 → 新增 → 搜索 → 菜单权限弹窗 → 删除
 */
test.describe("系统管理 - 角色管理", () => {
  const roleName = uniqueName("e2erole");

  test("角色列表页面正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.role);
    await expect(page.locator(".el-table").first()).toBeVisible();
  });

  test("新增角色后可被搜索到（随后清理）", async ({ page }) => {
    await gotoModule(page, MODULES.role);

    await page.locator('button:has-text("新增")').first().click();
    await fillDialog(page, {
      请输入角色名称: roleName,
      请输入角色标识: roleName.toUpperCase(),
      请输入描述信息: "E2E 自动化测试创建"
    });
    await submitDialog(page);
    await waitTableReady(page);

    await search(page, "请输入角色名称", roleName);
    await expect(page.locator(".el-table__body-wrapper").first()).toContainText(roleName);

    // 清理
    await page.locator(".el-table__body-wrapper .el-table__row").first().hover();
    await page.locator('.el-table__row:first-child button:has-text("删除")').first().click();
    await page.locator(".el-message-box").last().locator('button:has-text("确定")').click();
    await waitTableReady(page);
  });

  test("菜单权限分配弹窗可正常打开与关闭", async ({ page }) => {
    await gotoModule(page, MODULES.role);

    await page.locator(".el-table__body-wrapper .el-table__row").first().hover();
    const menuBtn = page.locator('.el-table__row:first-child button:has-text("菜单权限")').first();
    await expect(menuBtn).toBeVisible({ timeout: 8000 });
    await menuBtn.click();

    // 权限抽屉/弹窗中应出现菜单树
    await expect(page.locator(".el-tree").first()).toBeVisible({ timeout: 10000 });
    await cancelDialog(page);
  });
});
