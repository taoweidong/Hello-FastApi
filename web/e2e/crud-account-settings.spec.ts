import { expect, test, type Page } from "@playwright/test";
import { gotoPage, trackPageErrors } from "./utils/helpers";

/**
 * 账号设置页（全屏 remaining 路由）交互覆盖。
 * 该页是 smoke 未覆盖的交互面，且改动 admin 资料/密码有风险，故本 spec 严格规避破坏性操作：
 *   - 个人信息「更新信息」：表单 onMounted 已从 getMine 回填，直接同值保存（幂等，不改实质数据）
 *   - 账户管理「修改密码」：只打开对话框并点「确定」（表单为空 → el-form 校验拦截，不发起 API），
 *     避免用错误旧密码触发后端 401 —— 本项目 401 会被全局拦截器重定向到登录页，破坏 admin 会话
 *   - 偏好设置开关 / 安全日志表格：纯前端或只读，无破坏性
 * - 切换 Tab 通过侧边 `.el-menu-item` 文本点击；仅当前 Tab 的组件会被渲染（<component :is>）
 * - 用 getByRole("heading") 断言面板标题，避免与侧边栏同名菜单项的严格模式冲突
 */
test.describe("账号设置页交互", () => {
  /** 点击侧边栏 Tab（菜单项文本） */
  async function clickTab(page: Page, label: string): Promise<void> {
    await page.locator(".el-menu-item", { hasText: label }).click();
  }

  test("个人信息：更新信息（同值保存，安全）", async ({ page }) => {
    const errors: string[] = [];
    trackPageErrors(page, errors);
    await gotoPage(page, "/account-settings");

    // 默认进入「个人信息」Tab，含「更新信息」按钮
    const saveBtn = page.getByRole("button", { name: "更新信息" });
    await expect(saveBtn).toBeVisible({ timeout: 10000 });
    await saveBtn.click();
    await expect(page.getByText(/更新信息成功/)).toBeVisible({ timeout: 6000 });

    expect(errors, `页面报错: ${errors.join("; ")}`).toHaveLength(0);
  });

  test("账户管理：打开修改密码对话框并校验拦截（不发起 API，不破坏会话）", async ({
    page
  }) => {
    await gotoPage(page, "/account-settings");
    await clickTab(page, "账户管理");
    await expect(page.getByRole("heading", { name: "账户管理" })).toBeVisible({
      timeout: 10000
    });

    // 账户管理面板内第一个「修改」= 账户密码（其余两个仅弹 info 提示）
    await page.getByRole("button", { name: "修改" }).first().click();
    const dialog = page.locator(".el-dialog", { hasText: "修改账户密码" });
    await expect(dialog).toBeVisible({ timeout: 10000 });

    // 表单为空直接点「确定」：el-form 校验拦截（必填项报错），不会发起 change-password API，
    // 从而不会触发 401 → 登录页重定向，破坏后续用例的 admin 会话
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(
      dialog.locator(".el-form-item__error").first()
    ).toBeVisible({ timeout: 5000 });
    // 关闭对话框（验证失败不会关闭，需手动取消）
    await dialog.getByRole("button", { name: "取消" }).click();
    await expect(dialog).toBeHidden({ timeout: 8000 });
  });

  test("偏好设置：切换通知开关并提示成功", async ({ page }) => {
    await gotoPage(page, "/account-settings");
    await clickTab(page, "偏好设置");
    await expect(page.getByRole("heading", { name: "偏好设置" })).toBeVisible({
      timeout: 10000
    });

    const sw = page.locator(".el-switch").first();
    await expect(sw).toBeVisible({ timeout: 10000 });
    await sw.click();
    // onChange 弹出「{title}设置成功」
    await expect(page.getByText(/设置成功/)).toBeVisible({ timeout: 6000 });
  });

  test("安全日志：渲染登录记录表格", async ({ page }) => {
    await gotoPage(page, "/account-settings");
    await clickTab(page, "安全日志");
    await expect(page.getByRole("heading", { name: "安全日志" })).toBeVisible({
      timeout: 10000
    });
    await expect(page.locator(".el-table").first()).toBeVisible({ timeout: 10000 });
  });
});
