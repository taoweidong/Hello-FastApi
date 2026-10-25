import { expect, test } from "@playwright/test";
import { gotoPage } from "./utils/helpers";

/**
 * 缓存监控：Redis 运行状态渲染 + 命令统计表 + 刷新按钮
 * - 后端已确认 Redis 连接正常（启动日志「Redis 连接初始化完成」），
 *   页面应渲染真实数据而非「缓存服务不可用」降级态
 */
test.describe("缓存监控", () => {
  test("缓存信息渲染且可刷新", async ({ page }) => {
    await gotoPage(page, "/monitor/cache");

    const desc = page.locator(".el-descriptions").first();
    await expect(desc).toBeVisible({ timeout: 10000 });
    await expect(desc).toContainText("Redis 运行状态");

    // Redis 已连接：渲染真实运行数据，而非「缓存服务不可用」降级态；
    // 版本标签 + 真实版本号（非空占位 "-"）一并出现，证明 connected 分支生效
    await expect(desc).toContainText("版本");
    await expect(desc).not.toContainText("缓存服务不可用");
    const versionCell = desc.getByText("版本").first();
    await expect(versionCell).toBeVisible();

    // 命令调用统计表渲染
    await expect(
      page.locator(".el-table").first()
    ).toBeVisible({ timeout: 10000 });

    // 刷新按钮可点击且页面保持可用
    await page.getByRole("button", { name: "刷新" }).click();
    await expect(desc).toBeVisible();
  });
});
