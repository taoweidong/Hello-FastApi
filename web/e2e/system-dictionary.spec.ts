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
 * 字典管理端到端全流程：列表 → 新增顶级字典 → 搜索 → 删除
 */
test.describe("系统管理 - 字典管理", () => {
  const dictName = uniqueName("e2edict");

  test("字典列表正常加载", async ({ page }) => {
    await gotoModule(page, MODULES.dictionary);
    await expect(page.locator(".el-table").first()).toBeVisible();
  });

  test("新增字典后可被搜索到（随后清理）", async ({ page }) => {
    await gotoModule(page, MODULES.dictionary);

    await page.locator('button:has-text("新增")').first().click();
    await fillDialog(page, {
      请输入字典名称: dictName,
      请输入字典值: "e2e_value",
      请输入显示标签: "E2E测试字典"
    });
    await submitDialog(page);
    await waitTableReady(page);

    await search(page, "请输入字典名称", dictName);
    await expect(page.locator(".el-table__body-wrapper").first()).toContainText(dictName);

    // 清理
    await page.locator(".el-table__body-wrapper .el-table__row").first().hover();
    await page.locator('.el-table__row:first-child button:has-text("删除")').first().click();
    await page.locator(".el-message-box").last().locator('button:has-text("确定")').click();
    await waitTableReady(page);
  });
});
