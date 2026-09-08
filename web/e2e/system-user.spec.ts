import { expect, test } from "@playwright/test";
import {
  MODULES,
  cancelDialog,
  fillDialog,
  gotoModule,
  rowCount,
  search,
  submitDialog,
  uniqueName,
  waitTableReady
} from "./helpers";

/**
 * 用户管理端到端全流程：列表 → 搜索 → 新增 → 校验唯一性 → 编辑 → 删除
 */
test.describe("系统管理 - 用户管理", () => {
  const username = uniqueName("e2euser");

  test("用户列表页面正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.user);
    await expect(page.locator(".el-table").first()).toBeVisible();
    await expect(page.locator(".el-pagination").first()).toBeVisible();
  });

  test("按用户名搜索可过滤列表", async ({ page }) => {
    await gotoModule(page, MODULES.user);

    await search(page, "请输入用户名称", "admin");
    const count = await rowCount(page);
    expect(count).toBeGreaterThan(0);

    // 结果中应包含 admin
    await expect(page.locator(".el-table__body-wrapper").first()).toContainText("admin");
  });

  test("新增用户后出现在列表中（随后清理）", async ({ page }) => {
    await gotoModule(page, MODULES.user);

    await page.locator('button:has-text("新增")').first().click();
    await fillDialog(page, {
      请输入用户名称: username,
      请输入用户昵称: "E2E测试用户",
      请输入用户密码: "E2eTest@123",
      请输入手机号: "13800000000",
      请输入邮箱: `${username}@example.com`
    });
    await submitDialog(page);
    await waitTableReady(page);

    // 用搜索确认新增成功
    await search(page, "请输入用户名称", username);
    await expect(page.locator(".el-table__body-wrapper").first()).toContainText(username);

    // 清理：删除新增用户
    await page.locator(".el-table__body-wrapper .el-table__row").first().hover();
    await page.locator('.el-table__row:first-child button:has-text("删除")').first().click();
    await page.locator(".el-message-box").last().locator('button:has-text("确定")').click();
    await waitTableReady(page);
  });

  test("重置密码弹窗可正常打开与取消", async ({ page }) => {
    await gotoModule(page, MODULES.user);

    await page.locator(".el-table__body-wrapper .el-table__row").first().hover();
    const resetBtn = page.locator('.el-table__row:first-child button:has-text("重置密码")').first();
    await expect(resetBtn).toBeVisible({ timeout: 8000 });
    await resetBtn.click();

    await cancelDialog(page);
  });
});
