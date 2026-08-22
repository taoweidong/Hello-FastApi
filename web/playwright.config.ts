import { defineConfig } from "@playwright/test";

/**
 * Playwright E2E 配置：三 project 拓扑
 * - setup：登录一次并持久化 storageState（供 smoke/crud 复用，规避后端登录限流 100 次/分钟）
 * - smoke：全页面只读冒烟（无状态依赖，可全并行）
 * - crud：用户/角色/字典关键 CRUD（写操作，串行防数据竞争）
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  expect: { timeout: 5000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["html", { outputFolder: "playwright-report" }], ["list"]],
  use: {
    baseURL: "http://localhost:8848",
    browserName: "chromium",
    viewport: { width: 1920, height: 1080 },
    trace: "on-first-retry",
    screenshot: "only-on-failure"
  },
  projects: [
    // 登录一次并持久化 storageState，供 smoke/crud 复用（规避登录限流）
    {
      name: "setup",
      testMatch: /utils\/auth\.setup\.ts/
    },
    // 全页面只读冒烟：无状态依赖、可全并行
    {
      name: "smoke",
      testMatch: /smoke\.spec\.ts/,
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
