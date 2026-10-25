import { request, type Locator, type Page } from "@playwright/test";

/**
 * 后端 API 基地址。
 * 默认 127.0.0.1:8000（显式 IP：localhost 可能解析到 ::1 命中其他 8000 绑定）。
 * 可用 E2E_API_BASE_URL 覆盖——本机同时开发多个项目时，8000 常被别的服务占用，
 * 此时后端需换端口启动，否则这里会静默打到别的项目上（表现为 API 登录 404）。
 */
const API_BASE_URL = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8000";

/** 冒烟页面注册表：path → 页面关键锚点选择器（存在即可判渲染成功） */
export const SMOKE_PAGES: Array<{
  path: string;
  anchor: string;
  note?: string;
}> = [
  { path: "/welcome", anchor: ".sidebar-container" },
  { path: "/system/user", anchor: ".el-table" },
  { path: "/system/role", anchor: ".el-table" },
  { path: "/system/menu", anchor: ".el-table" },
  { path: "/system/dept", anchor: ".el-table" },
  { path: "/system/dictionary", anchor: ".el-tree" }, // 左侧字典树
  { path: "/system/ip-rule", anchor: ".el-table" },
  { path: "/system/config", anchor: ".el-table" },
  { path: "/system/notice", anchor: ".el-table" },
  { path: "/system/post", anchor: ".el-table" },
  { path: "/monitor/online-user", anchor: ".el-table" },
  { path: "/monitor/server", anchor: ".el-card" }, // CPU/内存/磁盘信息卡
  { path: "/monitor/cache", anchor: ".el-card" },
  { path: "/monitor/log/login", anchor: ".el-table" },
  { path: "/monitor/log/operation", anchor: ".el-table" },
  { path: "/account-settings", anchor: ".pure-account-settings" }, // 账号设置容器
  { path: "/empty", anchor: ".size-full" } // 空页占位
];

/** hash 导航并等待目标路由稳定（轮询断言，避免 networkidle） */
export async function gotoPage(page: Page, hashPath: string): Promise<void> {
  await page.goto(`/#${hashPath}`);
  await page.waitForURL(new RegExp(hashPath.replace(/\//g, "\\/") + "$"));
}

/** 收集页面 console.error / pageerror / 4xx 以上网络响应，冒烟结束统一断言 */
export function trackPageErrors(page: Page, errors: string[]): void {
  page.on("console", msg => {
    if (msg.type() === "error") errors.push(`console.error: ${msg.text()}`);
  });
  page.on("pageerror", err => errors.push(`pageerror: ${err.message}`));
  page.on("response", res => {
    if (res.url().includes("/api/system/") && res.status() >= 400) {
      errors.push(`HTTP ${res.status()}: ${res.url()}`);
    }
  });
}

/** 生成唯一测试数据名：e2e_<模块>_<毫秒时间戳>_<4位随机> */
export function makeUniqueName(module: string): string {
  const rand = Math.random().toString(36).slice(2, 6);
  return `e2e_${module}_${Date.now()}_${rand}`;
}

/** 按表单行 label 定位并填充输入框（新增/修改对话框通用） */
export async function fillFormItem(
  dialog: Locator,
  label: string,
  value: string
): Promise<void> {
  // hasText 子串匹配 label 文本；has: 谓词要求相对定位器，绝对定位器命中为 0，故弃用
  const item = dialog.locator(".el-form-item").filter({ hasText: label });
  await item.locator("input, textarea").first().fill(value);
}

/**
 * 确认 Element Plus 的 ElMessageBox（删除/强退等二次确认弹窗）。
 *
 * useCrudTable 的 handleDelete / handleBatchDelete 在模板 popconfirm 之外，
 * 还会再弹一层 ElMessageBox.confirm；只点 popconfirm 不会真正发起删除请求。
 * 该助手在 popconfirm 确认后调用，等待并点击 message-box 的「确定」。
 */
export async function confirmMessageBox(page: Page): Promise<void> {
  const box = page.locator(".el-message-box").last();
  await box.waitFor({ state: "visible", timeout: 8000 });
  await box.locator('button:has-text("确定"), button:has-text("确认")').last().click();
  await page.locator(".el-message-box").last().waitFor({ state: "hidden", timeout: 10000 }).catch(() => {});
}

/** API 登录 admin，返回 accessToken（登录限流 100 次/分钟，全局仅少量调用） */
async function apiLogin(username: string, password: string): Promise<string> {
  const ctx = await request.newContext({ baseURL: API_BASE_URL });
  try {
    const res = await ctx.post("/api/system/login", {
      data: { username, password }
    });
    const body = await res.json();
    if (res.status() >= 400 || !body?.data?.accessToken) {
      throw new Error(`API 登录失败: ${res.status()} ${body?.message ?? ""}`);
    }
    return body.data.accessToken as string;
  } finally {
    await ctx.dispose();
  }
}
export { apiLogin };

/**
 * 通用 API 请求助手（造数/清理用，避免测试依赖 UI 流程准备前置数据）。
 * 用法：apiFetch("POST", "/api/system/user/create", { token, body })
 */
export async function apiFetch(
  method: "GET" | "POST" | "PUT" | "DELETE",
  path: string,
  options: { token?: string; body?: unknown } = {}
): Promise<{ status: number; body: any }> {
  const ctx = await request.newContext({ baseURL: API_BASE_URL });
  try {
    const res = await ctx.fetch(path, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {})
      },
      data: options.body
    });
    let body: any = null;
    try {
      body = await res.json();
    } catch {
      body = null;
    }
    return { status: res.status(), body };
  } finally {
    await ctx.dispose();
  }
}

/** API 兜底清理：登录拿 token → POST 列表 → DELETE 逐个（BaseApi 端点约定） */
export async function cleanupByApi(
  prefix: string,
  nameLike: string
): Promise<void> {
  const token = await apiLogin("admin", "admin123");
  const ctx = await request.newContext({
    baseURL: API_BASE_URL,
    extraHTTPHeaders: { Authorization: `Bearer ${token}` }
  });
  try {
    // 字典列表返回数组（不分页），user/role 返回 { list } 分页结构，统一兼容
    for (let pageNum = 1; ; pageNum++) {
      const res = await ctx.post(`/api/system${prefix}`, {
        data: { pageNum, pageSize: 100 }
      });
      const body = await res.json();
      const payload = body?.data;
      const rows: Array<Record<string, any>> = Array.isArray(payload)
        ? payload
        : (payload?.list ?? []);
      for (const row of rows) {
        // 覆盖各模块的命名域：user/username、role/name、config/name、
        // notice/title、post/postName+postCode、menu/meta.title
        const hit = [
          row.name,
          row.username,
          row.label,
          row.title,
          row.postName,
          row.postCode,
          row.meta?.title
        ]
          .filter(Boolean)
          .some(v => String(v).includes(nameLike));
        if (hit && row.id) {
          await ctx.delete(`/api/system${prefix}/${row.id}`);
        }
      }
      const total = Array.isArray(payload)
        ? rows.length
        : Number(payload?.total ?? rows.length);
      if (pageNum * 100 >= total) break;
    }
  } finally {
    await ctx.dispose();
  }
}
