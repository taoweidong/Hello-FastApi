import { expect, test } from "@playwright/test";
import { gotoPage } from "./utils/helpers";

/**
 * 日志管理：登录日志批量删除（选中行，scoped）+ 操作日志按模块搜索 + 清空日志
 * - 成功提示：批量删除「已删除序号为 X 的数据」；清空「已删除所有日志数据」
 * - 清空只作用于操作日志（纯 API 审计噪声，E2E 自身持续产生，无审计价值损失）；
 *   登录日志仅做选中行批量删除，不做整表清空
 */
test.describe.serial("日志管理", () => {
  test("登录日志：批量删除选中行", async ({ page }) => {
    await gotoPage(page, "/monitor/log/login");
    await expect(page.locator(".el-table").first()).toBeVisible();
    const firstRow = page.locator(".el-table__row").first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });

    await firstRow.locator(".el-checkbox").click();
    await page.getByRole("button", { name: "批量删除" }).click();
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();
    await expect(page.getByText("已删除序号为")).toBeVisible({
      timeout: 10000
    });
  });

  test("操作日志：按所属模块搜索", async ({ page }) => {
    await gotoPage(page, "/monitor/log/operation");
    await expect(page.locator(".el-table").first()).toBeVisible();
    await page
      .locator('.search-form input[placeholder*="请输入所属模块"]')
      .fill("dictionary");
    await page.getByRole("button", { name: "搜索" }).click();
    // 同轮 crud-dictionary 已先行执行，必然有 dictionary 模块的操作记录
    await expect(page.locator(".el-table__row").first()).toBeVisible({
      timeout: 10000
    });
  });

  test("操作日志：清空日志", async ({ page }) => {
    await gotoPage(page, "/monitor/log/operation");
    await page.getByRole("button", { name: "清空日志" }).click();
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();
    await expect(page.getByText("已删除所有日志数据")).toBeVisible({
      timeout: 10000
    });
    // 清空后此前由字典 CRUD 测试产生的 dictionary 模块日志应消失；
    // 不直接断言整表为空（清空动作自身会留一条审计日志，模块非 dictionary）。
    await page
      .locator('.search-form input[placeholder*="请输入所属模块"]')
      .fill("dictionary");
    await page.getByRole("button", { name: "搜索" }).click();
    await expect(
      page.locator(".el-table__row", { hasText: "dictionary" })
    ).toHaveCount(0, { timeout: 10000 });
  });
});
