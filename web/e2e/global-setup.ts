/**
 * 全局登录态准备
 *
 * 通过 UI 登录一次，把浏览器存储状态（cookie + localStorage）落盘，
 * 供所有业务模块用例复用，避免每个用例重复登录导致的耗时与不稳定。
 */
import { chromium, type FullConfig } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { ADMIN, loginViaUI } from "./helpers";

// 项目为 ESM（package.json type=module），__dirname 不可用，需从 import.meta.url 推导
const currentDir = dirname(fileURLToPath(import.meta.url));

/** 登录态落盘路径（Playwright 会按配置文件所在目录解析相对路径，此处用绝对路径更稳妥） */
export const STORAGE_STATE = resolve(currentDir, ".auth/admin.json");

async function globalSetup(config: FullConfig) {
  const baseURL =
    config.projects[0]?.use?.baseURL ?? "http://localhost:8848";
  mkdirSync(dirname(STORAGE_STATE), { recursive: true });

  const browser = await chromium.launch({ args: ["--no-proxy-server"] });
  const context = await browser.newContext({ baseURL });
  const page = await context.newPage();

  try {
    await loginViaUI(page, ADMIN.username, ADMIN.password);
    await page.context().storageState({ path: STORAGE_STATE });
    // 校验登录确实成功（首页已渲染侧边栏）
    await page.waitForSelector(".el-menu, .sidebar-container", {
      timeout: 15000
    });
  } finally {
    await browser.close();
  }
}

export default globalSetup;
