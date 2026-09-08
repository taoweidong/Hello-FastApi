import { defineConfig } from "@playwright/test";

/**
 * 登录态落盘路径。
 *
 * 与 e2e/global-setup.ts 保持一致；此处不直接 import 是为了避免配置文件
 * 加载时执行 global-setup 的模块顶层代码（ESM 环境下 __dirname 不可用）。
 */
const STORAGE_STATE = "e2e/.auth/admin.json";

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  timeout: 60000,
  expect: { timeout: 10000 },
  // 业务用例共享同一登录态且存在写操作，串行执行以避免数据竞争
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: 1,
  reporter: [
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["list"]
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8848",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    // 复用全局登录态，业务模块用例无需重复登录
    storageState: STORAGE_STATE,
    // 绕过系统代理，避免 localhost 请求被代理拦截
    launchOptions: { args: ["--no-proxy-server"] }
  },
  projects: [
    {
      name: "chromium",
      use: {
        browserName: "chromium",
        viewport: { width: 1920, height: 1080 }
      }
    }
  ]
});
