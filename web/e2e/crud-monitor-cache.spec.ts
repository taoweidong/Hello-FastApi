import { expect, test } from "@playwright/test";
import { gotoPage, trackPageErrors } from "./utils/helpers";

/**
 * 缓存监控页（/monitor/cache）交互覆盖：smoke 仅断言外层 .el-card，
 * 未验证 Redis 信息真实加载与「刷新」按钮可用。
 * - Redis 可用时展示「Redis 运行状态」及版本/内存等字段；不可用时展示「缓存服务不可用」。
 *   两者任一出现即视为数据加载正常，避免依赖 Redis 状态导致假失败。
 * - 点击「刷新」重复触发 getCacheInfo，确认无 /api/system/ 4xx 与控制台报错。
 */
test.describe("缓存监控页交互", () => {
  test("缓存监控：加载 Redis 信息，刷新可重复触发且无异常", async ({ page }) => {
    const errors: string[] = [];
    trackPageErrors(page, errors);
    await gotoPage(page, "/monitor/cache");

    // 数据加载：要么 Redis 运行状态，要么缓存不可用提示
    const dataLoaded = page.getByText("Redis 运行状态").or(
      page.getByText("缓存服务不可用")
    );
    await expect(dataLoaded).toBeVisible({ timeout: 10000 });

    // 点击「刷新」后信息仍正常渲染
    await page.getByRole("button", { name: "刷新" }).click();
    await expect(dataLoaded).toBeVisible({ timeout: 10000 });

    expect(errors, `页面报错: ${errors.join("; ")}`).toHaveLength(0);
  });
});
