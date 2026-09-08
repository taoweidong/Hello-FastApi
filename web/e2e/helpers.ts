/**
 * E2E 公共助手
 *
 * 提供登录态复用、模块导航、表格等待、弹窗表单填写等通用能力，
 * 供各业务模块的端到端用例复用，避免每个 spec 重复实现登录流程。
 */
import { expect, type Page } from "@playwright/test";

/** 默认管理员账号（与 scripts.cli createsuperuser 初始化的账号保持一致） */
export const ADMIN = {
  username: "admin",
  password: "admin123"
};

/** 各业务模块的路由路径（来自后端 /api/system/get-async-routes 动态菜单） */
export const MODULES = {
  user: "/system/user",
  role: "/system/role",
  menu: "/system/menu",
  dept: "/system/dept",
  dictionary: "/system/dictionary",
  ipRule: "/system/ip-rule",
  config: "/system/config",
  onlineUser: "/monitor/online-user",
  loginLog: "/monitor/log/login",
  operationLog: "/monitor/log/operation",
  accountSettings: "/account-settings"
} as const;

/** 生成带时间戳的唯一名称，避免并发/重复执行时数据冲突 */
export function uniqueName(prefix: string): string {
  const ts = Date.now().toString().slice(-8);
  return `${prefix}_${ts}`;
}

/** 通过 UI 登录（用于需要独立登录态的用例，如登录流程测试） */
export async function loginViaUI(page: Page, username = ADMIN.username, password = ADMIN.password) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  const usernameInput = page
    .locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]')
    .first();
  const passwordInput = page.locator('input[type="password"]').first();

  await expect(usernameInput).toBeVisible({ timeout: 10000 });
  await usernameInput.fill(username);
  await passwordInput.fill(password);

  await page.locator('button:has-text("登录"), button[type="submit"]').first().click();
  await page.waitForURL(/welcome|dashboard|^\/\w/, { timeout: 20000 }).catch(() => {});
  await page.waitForLoadState("networkidle");
}

/** 进入指定模块页面并等待主内容渲染完成 */
export async function gotoModule(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  // 页面骨架渲染：表格或空状态至少出现其一
  await expect
    .poll(
      async () => {
        const table = await page.locator(".el-table, .pure-table").count();
        const empty = await page.locator(".el-empty, .el-table__empty-block").count();
        return table + empty;
      },
      { timeout: 15000 }
    )
    .toBeGreaterThan(0);
}

/** 等待表格请求完成（loading 遮罩消失） */
export async function waitTableReady(page: Page) {
  await page.locator(".el-loading-mask").waitFor({ state: "hidden", timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(300);
}

/** 获取表格数据行数 */
export async function rowCount(page: Page): Promise<number> {
  return page.locator(".el-table__body-wrapper .el-table__row").count();
}

/**
 * 在新增/编辑弹窗中按 placeholder 填写表单。
 *
 * @param page 页面对象
 * @param fields placeholder -> 值 的映射
 */
export async function fillDialog(page: Page, fields: Record<string, string>) {
  const dialog = page.locator(".el-dialog:visible, .el-drawer:visible").last();
  await expect(dialog).toBeVisible({ timeout: 10000 });

  for (const [placeholder, value] of Object.entries(fields)) {
    const input = dialog.locator(`input[placeholder="${placeholder}"], textarea[placeholder="${placeholder}"]`).first();
    await expect(input).toBeVisible({ timeout: 8000 });
    await input.fill(value);
  }
}

/** 点击弹窗的确定按钮并等待弹窗关闭 */
export async function submitDialog(page: Page) {
  const dialog = page.locator(".el-dialog:visible, .el-drawer:visible").last();
  await dialog.locator('button:has-text("确定"), button:has-text("确认"), button:has-text("保存")').last().click();
  await expect(page.locator(".el-dialog:visible, .el-drawer:visible")).toHaveCount(0, { timeout: 15000 });
}

/** 取消并关闭弹窗 */
export async function cancelDialog(page: Page) {
  const dialog = page.locator(".el-dialog:visible, .el-drawer:visible").last();
  await dialog.locator('button:has-text("取消"), button:has-text("关闭")').last().click();
  await expect(page.locator(".el-dialog:visible, .el-drawer:visible")).toHaveCount(0, { timeout: 10000 });
}

/** 确认 Element Plus 的 MessageBox（删除确认等） */
export async function confirmMessageBox(page: Page) {
  const box = page.locator(".el-message-box").last();
  await expect(box).toBeVisible({ timeout: 8000 });
  await box.locator('button:has-text("确定"), button:has-text("确认")').last().click();
  await expect(page.locator(".el-message-box")).toHaveCount(0, { timeout: 10000 });
}

/** 在搜索框中输入关键字并点击搜索 */
export async function search(page: Page, placeholder: string, keyword: string) {
  const input = page.locator(`input[placeholder="${placeholder}"]`).first();
  await expect(input).toBeVisible({ timeout: 8000 });
  await input.fill(keyword);
  await page.locator('button:has-text("搜索")').first().click();
  await waitTableReady(page);
}
