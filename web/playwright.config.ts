import { defineConfig } from "@playwright/test";

/**
 * Playwright E2E 配置：四 project 拓扑
 * - setup：登录一次并持久化 storageState（供 smoke/crud 复用，规避后端登录限流 100 次/分钟）
 * - auth：登录流程用例（需未登录态，独立运行）
 * - smoke：全页面只读冒烟（无状态依赖，可全并行）
 * - crud：关键 CRUD（写操作，串行防数据竞争）
 *
 * 命名约定：`smoke*.spec.ts` 进 smoke project，`crud-*.spec.ts` 进 crud project，
 * `login.spec.ts` 进 auth project；不匹配任何 project 的文件不会被执行。
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  expect: { timeout: 10000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["html", { outputFolder: "playwright-report" }], ["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8848",
    browserName: "chromium",
    viewport: { width: 1920, height: 1080 },
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    // 绕过系统代理，避免 localhost 请求被代理拦截
    launchOptions: { args: ["--no-proxy-server"] }
  },
  projects: [
    // 登录一次并持久化 storageState，供 smoke/crud 复用（规避登录限流）
    {
      name: "setup",
      testMatch: /utils\/auth\.setup\.ts/
    },
    // 登录流程：必须处于未登录态，显式清空 storageState
    {
      name: "auth",
      testMatch: /login\.spec\.ts/,
      use: { storageState: { cookies: [], origins: [] } }
    },
    // 全页面只读冒烟：无状态依赖、可全并行
    {
      name: "smoke",
      testMatch: /smoke.*\.spec\.ts/,
      dependencies: ["setup"],
      use: { storageState: "test-results/.auth/admin.json" }
    },
    // 关键 CRUD：写操作，串行防数据竞争
    {
      name: "crud",
      testMatch: /crud-.*\.spec\.ts/,
      dependencies: ["setup"],
      use: { storageState: "test-results/.auth/admin.json" },
      fullyParallel: false,
      workers: 1
    }
  ]
});
