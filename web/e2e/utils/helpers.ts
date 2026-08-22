import { request, type Locator, type Page } from "@playwright/test";

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
  { path: "/permission/page/index", anchor: ".card-header" }, // 页面描述 header
  { path: "/permission/button/index", anchor: ".flex" },
  { path: "/permission/button/perms", anchor: ".el-card" },
  { path: "/about/index", anchor: ".box-card" }, // about 卡片
  { path: "/guide/index", anchor: ".card-header" }, // 引导页 title
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

/** API 登录 admin，返回 accessToken（登录限流 100 次/分钟，全局仅少量调用） */
async function apiLogin(username: string, password: string): Promise<string> {
  // 显式 127.0.0.1：localhost 可能解析到 ::1 命中其他 8000 绑定（workbuddy http.server）
  const ctx = await request.newContext({ baseURL: "http://127.0.0.1:8000" });
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

/** API 兜底清理：登录拿 token → POST 列表 → DELETE 逐个（BaseApi 端点约定） */
export async function cleanupByApi(
  prefix: string,
  nameLike: string
): Promise<void> {
  const token = await apiLogin("admin", "admin123");
  const ctx = await request.newContext({
    baseURL: "http://127.0.0.1:8000",
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
        const hit = [row.name, row.username, row.label]
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
