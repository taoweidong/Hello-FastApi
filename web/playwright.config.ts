import { defineConfig } from "@playwright/test";
import { STORAGE_STATE } from "./e2e/global-setup";

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
