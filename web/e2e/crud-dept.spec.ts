import { expect, test } from "@playwright/test";
import {
  MODULES,
  fillDialog,
  gotoModule,
  search,
  submitDialog,
  uniqueName,
  waitTableReady
} from "./helpers";

/**
 * 部门管理端到端全流程：树形列表 → 新增 → 搜索 → 删除
 */
test.describe("系统管理 - 部门管理", () => {
  const deptName = uniqueName("e2edept");

  test("部门树形列表正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.dept);
    await expect(page.locator(".el-table").first()).toBeVisible();
  });

  test("新增部门后可被搜索到（随后清理）", async ({ page }) => {
    await gotoModule(page, MODULES.dept);

    await page.locator('button:has-text("新增")').first().click();
    await fillDialog(page, {
      请输入部门名称: deptName,
      请输入部门负责人: "E2E负责人",
      请输入邮箱: `${deptName}@example.com`
    });
    await submitDialog(page);
    await waitTableReady(page);

    await search(page, "请输入部门名称", deptName);
    await expect(page.locator(".el-table__body-wrapper").first()).toContainText(deptName);

    // 清理
    await page.locator(".el-table__body-wrapper .el-table__row").first().hover();
    await page.locator('.el-table__row:first-child button:has-text("删除")').first().click();
    await page.locator(".el-message-box").last().locator('button:has-text("确定")').click();
    await waitTableReady(page);
  });
});
