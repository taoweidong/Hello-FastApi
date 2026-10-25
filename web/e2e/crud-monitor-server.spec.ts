import { expect, test } from "@playwright/test";
import { gotoPage } from "./utils/helpers";

/**
 * 服务器监控页交互验证（原 smoke 仅断言外层 .el-card 渲染，本用例验证
 * 真实数据加载：CPU/内存/磁盘 进度环、系统信息与进程信息，并验证「刷新」按钮
 * 可重复触发且不产生 /api/system/ 4xx 错误）。
 */
test.describe("服务器监控页交互验证", () => {
  test("服务器监控：加载 CPU/内存/磁盘 与系统/进程信息，刷新无异常", async ({
    page
  }) => {
    const errors: string[] = [];
    page.on("response", res => {
      if (res.url().includes("/api/system/") && res.status() >= 400) {
        errors.push(`HTTP ${res.status()}: ${res.url()}`);
      }
    });

    await gotoPage(page, "/monitor/server");

    // 标题与加载态结束
    await expect(page.getByText("服务器监控").first()).toBeVisible({
      timeout: 10000
    });

    // 等待服务器信息加载完成（CPU/内存/磁盘 进度环出现，说明 /server-info 返回 200）
    await expect(page.locator(".el-progress").first()).toBeVisible({
      timeout: 15000
    });

    // 系统信息区块
    await expect(page.getByText("主机名称").first()).toBeVisible();
    await expect(page.getByText("Python 版本").first()).toBeVisible();
    // 进程信息区块
    await expect(page.getByText("进程 ID").first()).toBeVisible();

    // 点击「刷新」：重新拉取数据，不应报错
    await page.getByRole("button", { name: "刷新" }).click();
    await expect(page.locator(".el-progress").first()).toBeVisible({
      timeout: 15000
    });

    expect(errors, "监控页出现 /api/system/ 4xx 以上错误").toEqual([]);
  });
});
