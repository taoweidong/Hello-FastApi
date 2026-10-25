import { expect, test, type Page, type Locator } from "@playwright/test";
import {
  apiFetch,
  apiLogin,
  cleanupByApi,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 用户管理 - 行内「更多」下拉的三个交互动作覆盖：
 *   上传头像（裁剪对话框）、重置密码、分配角色
 * - beforeAll 通过 API 创建一个隔离测试用户，afterAll 删除
 * - 三个测试互相独立：各自导航 → 搜索定位行 → 打开下拉 → 操作 → 断言
 * - 依赖 crud project（admin storageState、workers=1），与 crud-user.spec.ts 同序执行
 */
test.describe("用户管理-行内操作（上传头像/重置密码/分配角色）", () => {
  const username = makeUniqueName("uaction");
  const password = "Test@123456";
  let createdId = "";

  /** 按唯一用户名搜索过滤，保证目标行位于当前页 */
  async function searchUser(page: Page): Promise<void> {
    await page
      .locator('.search-form input[placeholder*="请输入用户名称"]')
      .fill(username);
    await page.getByRole("button", { name: "搜索" }).click();
  }

  /** 定位用户表格中的目标行（按文本子串匹配） */
  function userRow(page: Page) {
    return page.locator(".el-table__row", { hasText: username });
  }

  /** 打开行内「更多」下拉并点击指定菜单项 */
  async function openRowAction(
    page: Page,
    row: Locator,
    actionName: string
  ): Promise<void> {
    await row.locator(".el-dropdown").getByRole("button").first().click();
    await page
      .locator(".el-dropdown-menu__item", { hasText: actionName })
      .click();
  }

  test.beforeAll(async () => {
    const token = await apiLogin("admin", "admin123");
    const res = await apiFetch("POST", "/api/system/user/create", {
      token,
      body: {
        username,
        password,
        nickname: "E2E动作测试",
        isActive: 1
      }
    });
    createdId = res.body?.data?.id ?? "";
    if (!createdId) {
      throw new Error(`测试用户创建失败: ${JSON.stringify(res.body)}`);
    }
  });

  test("上传头像：打开裁剪对话框并关闭", async ({ page }) => {
    await gotoPage(page, "/system/user");
    await searchUser(page);
    const row = userRow(page);
    await expect(row.first()).toBeVisible({ timeout: 10000 });

    await openRowAction(page, row, "上传头像");
    const dialog = page.locator(".el-dialog", { hasText: "裁剪、上传头像" });
    await expect(dialog).toBeVisible({ timeout: 10000 });
    // 裁剪区（ReCropperPreview）已渲染
    await expect(dialog.locator(".cropper-container, .re-cropper, canvas").first()).toBeAttached({
      timeout: 10000
    });

    // 通过「取消」优雅关闭（该对话框确定不发起 API，仅关闭并刷新列表）
    await dialog.getByRole("button", { name: "取消" }).click();
    await expect(dialog).toBeHidden({ timeout: 8000 });
  });

  test("重置密码：填入新密码并提交成功", async ({ page }) => {
    await gotoPage(page, "/system/user");
    await searchUser(page);
    const row = userRow(page);
    await expect(row.first()).toBeVisible({ timeout: 10000 });

    await openRowAction(page, row, "重置密码");
    const dialog = page.locator(".el-dialog", {
      hasText: `重置 ${username} 用户的密码`
    });
    await expect(dialog).toBeVisible({ timeout: 10000 });

    // 新密码输入框只有 placeholder，无 label，按 placeholder 定位
    await dialog
      .locator('input[placeholder="请输入新密码"]')
      .fill("NewPass@2026");
    await dialog.getByRole("button", { name: "确定" }).click();

    // 成功路径 beforeSure 调用 done() 关闭对话框，并弹出成功提示
    await expect(dialog).toBeHidden({ timeout: 8000 });
    await expect(page.getByText(/已成功重置/)).toBeVisible({ timeout: 6000 });
  });

  test("分配角色：选择角色并提交成功", async ({ page }) => {
    await gotoPage(page, "/system/user");
    await searchUser(page);
    const row = userRow(page);
    await expect(row.first()).toBeVisible({ timeout: 10000 });

    await openRowAction(page, row, "分配角色");
    const dialog = page.locator(".el-dialog", {
      hasText: `分配 ${username} 用户的角色`
    });
    await expect(dialog).toBeVisible({ timeout: 10000 });

    // 打开角色多选下拉，选择第一个可见角色
    // 注意：页面上可能存在多个 el-select 的 popper（含隐藏态），必须按「可见」过滤，
    // 否则会命中隐藏 popper 里的 option 导致 click 超时（元素不可见）。
    await dialog.locator(".el-select").click();
    const firstRole = page
      .locator(".el-select-dropdown__item")
      .filter({ visible: true })
      .first();
    await expect(firstRole).toBeVisible({ timeout: 5000 });
    await firstRole.click();
    // 多选下拉选择后 popper 仍展开，会遮住底部「确定」按钮，先 Esc 收起
    await page.keyboard.press("Escape");
    await dialog.getByRole("button", { name: "确定" }).click();

    await expect(dialog).toBeHidden({ timeout: 8000 });
    await expect(page.getByText(/已成功为用户/)).toBeVisible({ timeout: 6000 });
  });

  test.afterAll(async () => {
    if (createdId) {
      const token = await apiLogin("admin", "admin123");
      await apiFetch("DELETE", `/api/system/user/${createdId}`, { token });
    }
    // 兜底：按名称清理，防止 beforeAll 拿到 id 失败时的残留
    await cleanupByApi("/user", username);
  });
});
