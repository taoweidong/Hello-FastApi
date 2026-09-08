import { expect, test, type Page } from "@playwright/test";
import {
  cleanupByApi,
  fillFormItem,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 字典管理 CRUD 全流程（最复杂交互链路）：
 * 新增子典（类型）→ 新增字典详情 → 修改详情 → 删除详情 → 删除类型
 * - 必须先删详情再删类型：handleDeleteType 检测到子项时会拒绝删除
 * - 树节点更多操作走 el-dropdown（trigger=click，菜单渲染在 body 下）
 * - 数据唯一命名（e2e_ 前缀），类型与详情同表，afterAll 统一按 API 兜底清理
 */
test.describe.serial("字典管理 CRUD", () => {
  const uniquePrefix = makeUniqueName("dict");
  const dictName = `${uniquePrefix}字典`;
  const label = `${uniquePrefix}标签`;
  const newLabel = `${uniquePrefix}新标签`;
  const dictValue = `${uniquePrefix}value`;

  /** 定位左侧字典树节点 */
  function treeNode(page: Page, text: string) {
    return page.locator(".el-tree-node", { hasText: text });
  }

  /** 定位右侧详情表格行 */
  function detailRow(page: Page, text: string) {
    return page.locator(".el-table__row", { hasText: text });
  }

  test("新增子典", async ({ page }) => {
    await gotoPage(page, "/system/dictionary");
    await page.getByRole("button", { name: "新增子典" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增字典类型" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "字典名称", dictName);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });
    await expect(treeNode(page, dictName).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("新增字典详情", async ({ page }) => {
    await gotoPage(page, "/system/dictionary");
    const node = treeNode(page, dictName).first();
    await expect(node).toBeVisible({ timeout: 10000 });
    await node.click();
    await page.getByRole("button", { name: "新增字典详情" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "新增字典详情" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "显示标签", label);
    await fillFormItem(dialog, "字典值", dictValue);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });
    await expect(detailRow(page, label).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("修改字典详情", async ({ page }) => {
    await gotoPage(page, "/system/dictionary");
    await treeNode(page, dictName).first().click();
    const row = detailRow(page, label).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "修改" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "修改字典" });
    await expect(dialog).toBeVisible();
    await fillFormItem(dialog, "显示标签", newLabel);
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });
    await expect(detailRow(page, newLabel).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("删除字典详情", async ({ page }) => {
    await gotoPage(page, "/system/dictionary");
    await treeNode(page, dictName).first().click();
    const row = detailRow(page, newLabel).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    await row.getByRole("button", { name: "删除" }).click();
    // el-popconfirm 确认（title: 是否确认删除字典标签为...）
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();
    // ElMessageBox 系统提示确认
    const box = page.locator(".el-message-box");
    await expect(box).toBeVisible();
    await box.getByRole("button", { name: "确定" }).click();
    await expect(box).toBeHidden({ timeout: 10000 });
    await expect(detailRow(page, newLabel)).toHaveCount(0);
  });

  test("删除字典类型", async ({ page }) => {
    await gotoPage(page, "/system/dictionary");
    const node = treeNode(page, dictName).first();
    await expect(node).toBeVisible({ timeout: 10000 });
    await node.click();
    // 点节点行内更多图标（ri/more-2-fill，渲染在内容区末尾的 el-icon）
    await node.locator(".el-tree-node__content .el-icon").last().click();
    // dropdown 菜单位于 body 下（非树内），点「删除」
    await page
      .locator(".el-dropdown-menu:visible")
      .getByText("删除", { exact: true })
      .click();
    // ElMessageBox 系统提示确认
    const box = page.locator(".el-message-box");
    await expect(box).toBeVisible();
    await box.getByRole("button", { name: "确定" }).click();
    await expect(box).toBeHidden({ timeout: 10000 });
    await expect(treeNode(page, dictName)).toHaveCount(0);
  });

  test.afterAll(async () => {
    await cleanupByApi("/dictionary", uniquePrefix);
  });
});
