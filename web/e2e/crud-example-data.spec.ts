import { expect, test } from "@playwright/test";
import { gotoPage } from "./utils/helpers";

test.describe("示例数据表（Univer 表格 CRUD）", () => {
  /** Univer 冷启动渲染较重（引擎初始化 2~10s）：页面内轮询画布出现 */
  async function waitForGrid(page: import("@playwright/test").Page) {
    await page.waitForFunction(
      () => document.querySelectorAll("#example-data-univer canvas").length > 0,
      { timeout: 30000 }
    );
  }

  test.beforeEach(async ({ page }, testInfo) => {
    page.on("console", m => {
      if (m.text().includes("[example-data]") || m.type() === "error") {
        console.log(`[browser:${testInfo.title}] ${m.type()}: ${m.text().slice(0, 200)}`);
      }
    });
    page.on("pageerror", e => console.log(`[browser:${testInfo.title}] PAGEERROR: ${String(e).slice(0, 300)}`));
  });

  test("页面加载：Univer 画布渲染、工具栏按钮就位", async ({ page }) => {
    await gotoPage(page, "/system/example-data");
    // Univer 渲染容器出现（canvas）
    await waitForGrid(page);
    // 工具栏按钮（管理员：example:add/edit/delete 均可见）
    await expect(page.getByRole("button", { name: "新增行" })).toBeVisible();
    await expect(page.getByRole("button", { name: "保存变更" })).toBeVisible();
    await expect(page.getByRole("button", { name: "删除选中行" })).toBeVisible();
    await expect(page.getByText("已加载")).toBeVisible();
  });

  test("新增行 → 未填写名称直接保存 → 提示跳过空行", async ({ page }) => {
    await gotoPage(page, "/system/example-data");
    await waitForGrid(page);
    await page.getByRole("button", { name: "新增行" }).click();
    await expect(page.getByText("未保存变更 1 处")).toBeVisible();

    await page.getByRole("button", { name: "保存变更" }).click();
    await expect(
      page.getByText(/没有需要保存的变更（跳过 1 个空行）/)
    ).toBeVisible({ timeout: 10000 });
  });

  test("未选中行点删除 → 提示先选中", async ({ page }) => {
    await gotoPage(page, "/system/example-data");
    await waitForGrid(page);
    await page.getByRole("button", { name: "删除选中行" }).click();
    // Univer 默认选区在 A1（表头行）：实际提示为"表头不可删除"
    await expect(page.getByText("表头不可删除，请选中数据行")).toBeVisible({
      timeout: 10000
    });
  });
});
