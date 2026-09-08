import { expect, test } from "@playwright/test";
import { SMOKE_PAGES, gotoPage, trackPageErrors } from "./utils/helpers";

/**
 * 全页面只读冒烟测试
 * - 遍历 SMOKE_PAGES 注册表（22 个页面：路由权威来源 service/src/domain/rbac_defaults.py 动态菜单 + 前端静态路由）
 * - 每页断言关键锚点元素渲染成功（表格 / 树 / 卡片等）
 * - 全程收集 console.error / pageerror / /api/system/ 4xx+ 响应，结束后统一断言为零
 */
test.describe("全页面只读冒烟", () => {
  const errors: string[] = [];

  test.beforeEach(({ page }) => {
    trackPageErrors(page, errors);
  });

  test.afterAll(() => {
    expect(errors, "冒烟期间出现 console/网络错误").toEqual([]);
  });

  for (const { path, anchor } of SMOKE_PAGES) {
    test(`页面可访问：${path}`, async ({ page }) => {
      await gotoPage(page, path);
      await expect(page.locator(anchor).first()).toBeVisible({
        timeout: 10000
      });
    });
  }
});
