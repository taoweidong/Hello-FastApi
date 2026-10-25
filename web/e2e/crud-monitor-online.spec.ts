import { expect, test } from "@playwright/test";
import { apiFetch, apiLogin, gotoPage } from "./utils/helpers";

/**
 * 在线用户管理：搜索 + 强制下线（强退）
 *
 * 关键前提：**不能强退 admin 会话**——E2E 全流程复用 auth.setup 保存的
 * admin storageState，踢掉它会导致后续全部用例 401。因此这里先用 API
 * 造一个临时用户并登录（产生独立的在线会话），再强退该会话。
 *
 * 链路：admin 创建用户 → 临时用户登录（登记在线会话）→ UI 按用户名搜索
 * → 行内「强退」→ popconfirm 确认 → 成功提示 → 再搜该用户行数为 0。
 */
test.describe.serial("在线用户管理", () => {
  const username = `e2e_kick_${Date.now()}`;
  const password = "Test@123456";
  let userId = "";

  test.beforeAll(async () => {
    const token = await apiLogin("admin", "admin123");
    // 1. 创建临时用户（登录无角色要求，isActive=1 即可）
    const created = await apiFetch("POST", "/api/system/user/create", {
      token,
      body: { username, password, nickname: "E2E强退测试用户", isActive: 1 }
    });
    expect(created.status, `创建临时用户失败: ${JSON.stringify(created.body)}`).toBeLessThan(300);
    userId = created.body?.data?.id;
    expect(userId, "创建响应缺少用户 id").toBeTruthy();

    // 2. 以临时用户登录，登记在线会话
    const login = await apiFetch("POST", "/api/system/login", {
      body: { username, password }
    });
    expect(login.status, `临时用户登录失败: ${JSON.stringify(login.body)}`).toBeLessThan(300);
  });

  test.afterAll(async () => {
    if (userId) {
      const token = await apiLogin("admin", "admin123");
      await apiFetch("DELETE", `/api/system/user/${userId}`, { token });
    }
  });

  test("强退指定用户的在线会话", async ({ page }) => {
    await gotoPage(page, "/monitor/online-user");
    await expect(page.locator(".el-table").first()).toBeVisible();

    // 按临时用户名搜索（服务端过滤），目标行必然位于当前页
    await page
      .locator('.search-form input[placeholder*="请输入用户名"]')
      .fill(username);
    await page.getByRole("button", { name: "搜索" }).click();

    const row = page.locator(".el-table__row", { hasText: username }).first();
    await expect(row).toBeVisible({ timeout: 10000 });

    // 强退：popconfirm 确认
    await row.getByRole("button", { name: "强退" }).click();
    await page
      .locator(".el-popconfirm:visible")
      .getByRole("button", { name: "确定" })
      .click();

    // 会话被踢后再次搜索，该用户行应消失
    await expect(
      page.locator(".el-table__row", { hasText: username })
    ).toHaveCount(0, { timeout: 10000 });
  });

  test("搜索不存在的用户返回空列表", async ({ page }) => {
    await gotoPage(page, "/monitor/online-user");
    await page
      .locator('.search-form input[placeholder*="请输入用户名"]')
      .fill("e2e_no_such_user_zzz");
    await page.getByRole("button", { name: "搜索" }).click();
    // 空数据时 pure-table 渲染「暂无数据」占位
    await expect(page.locator(".el-table__empty-text").first()).toBeVisible({
      timeout: 10000
    });
  });
});
