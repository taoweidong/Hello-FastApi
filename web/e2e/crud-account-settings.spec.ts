import { expect, test, type Page } from "@playwright/test";
import { gotoPage, trackPageErrors } from "./utils/helpers";

/**
 * 账号设置页（全屏 remaining 路由）交互覆盖。
 * 该页是 smoke 未覆盖的交互面，且改动 admin 资料/密码有风险，故本 spec 严格规避破坏性操作：
 *   - 个人信息「更新信息」：表单 onMounted 已从 getMine 回填，直接同值保存（幂等，不改实质数据）
 *   - 账户管理「修改密码」：只打开对话框并点「确定」（表单为空 → el-form 校验拦截，不发起 API），
 *     避免用错误旧密码触发后端 401 —— 本项目 401 会被全局拦截器重定向到登录页，破坏 admin 会话
 *   - 偏好设置开关 / 安全日志表格：纯前端或只读，无破坏性
 * - 2026-11 重构后无侧栏 Tab：头部用户信息卡 + 栅格分区卡片，
 *   个人信息/账户管理/偏好设置/安全日志四个分区同屏直出，无需切换即可断言
 * - 各分区定位统一收口到「含分区标题文本的 el-card」内，避免跨分区选择器歧义
 */
test.describe("账号设置页交互", () => {
  /** 定位包含指定分区标题（h3）的栅格分区卡片 */
  function sectionCard(page: Page, heading: string) {
    return page.locator(".el-card", { hasText: heading });
  }

  test("个人信息：更新信息（同值保存，安全）", async ({ page }) => {
    const errors: string[] = [];
    trackPageErrors(page, errors);
    await gotoPage(page, "/account-settings");

    // 页面直出四个分区卡片，先确认「个人信息」分区渲染
    const card = sectionCard(page, "个人信息");
    await expect(card).toBeVisible({ timeout: 10000 });

    // 表单由 getMine 异步回填：等昵称非空后再保存，否则空表单触发「昵称必填」校验拦截
    const nicknameInput = card.locator('input[placeholder="请输入昵称"]');
    await expect(nicknameInput).toBeVisible({ timeout: 10000 });
    await expect(nicknameInput).toHaveValue(/.+/, { timeout: 10000 });

    const saveBtn = card.getByRole("button", { name: "更新信息" });
    await expect(saveBtn).toBeVisible({ timeout: 10000 });
    await saveBtn.click();
    await expect(page.getByText(/更新信息成功/)).toBeVisible({
      timeout: 15000
    });

    expect(errors, `页面报错: ${errors.join("; ")}`).toHaveLength(0);
  });

  test("账户管理：打开修改密码对话框并校验拦截（不发起 API，不破坏会话）", async ({
    page
  }) => {
    await gotoPage(page, "/account-settings");
    const card = sectionCard(page, "账户管理");
    await expect(card.getByRole("heading", { name: "账户管理" })).toBeVisible({
      timeout: 10000
    });

    // 账户管理卡片内第一个「修改」= 账户密码（其余两个仅弹 info 提示）
    await card.getByRole("button", { name: "修改" }).first().click();
    const dialog = page.locator(".el-dialog", { hasText: "修改账户密码" });
    await expect(dialog).toBeVisible({ timeout: 10000 });

    // 表单为空直接点「确定」：el-form 校验拦截（必填项报错），不会发起 change-password API，
    // 从而不会触发 401 → 登录页重定向，破坏后续用例的 admin 会话
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(dialog.locator(".el-form-item__error").first()).toBeVisible({
      timeout: 5000
    });
    // 关闭对话框（验证失败不会关闭，需手动取消）
    await dialog.getByRole("button", { name: "取消" }).click();
    await expect(dialog).toBeHidden({ timeout: 8000 });
  });

  test("偏好设置：切换通知开关并提示成功", async ({ page }) => {
    await gotoPage(page, "/account-settings");
    const card = sectionCard(page, "偏好设置");
    await expect(card.getByRole("heading", { name: "偏好设置" })).toBeVisible({
      timeout: 10000
    });

    // 开关同屏直出（无需切 Tab），取偏好设置卡片内第一个开关
    const sw = card.locator(".el-switch").first();
    await expect(sw).toBeVisible({ timeout: 10000 });
    await sw.click();
    // onChange 弹出「{title}设置成功」
    await expect(page.getByText(/设置成功/)).toBeVisible({ timeout: 6000 });
  });

  test("安全日志：渲染登录记录表格", async ({ page }) => {
    await gotoPage(page, "/account-settings");
    const card = sectionCard(page, "安全日志");
    await expect(card.getByRole("heading", { name: "安全日志" })).toBeVisible({
      timeout: 10000
    });
    await expect(card.locator(".el-table").first()).toBeVisible({
      timeout: 10000
    });
  });
});
