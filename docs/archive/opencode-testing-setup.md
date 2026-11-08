# OpenCode 自动化测试集成指南

> 本文档说明如何在 OpenCode 中配置插件、MCP 和工具，以实现 Hello-FastApi 项目的**前后端联调测试**和**自动化 Web 测试**。

---

## 1. 当前已有能力

### ✅ 已安装的工具

| 工具 | 版本 | 位置 | 用途 |
|------|------|------|------|
| Playwright (Python) | 1.59.0 | 系统全局 `/usr/local/lib/python3.10/dist-packages/playwright/` | 驱动现有 `service/tests/ui_test.py` |
| agent-browser CLI | 0.25.3 | 系统全局（npm） | Rust 浏览器自动化 CLI |
| Playwright MCP Skill | - | `/root/.config/opencode/skills/playwright/` | MCP 驱动的浏览器自动化 |
| agent-browser Skill | - | `.opencode/skills/agent-browser/` + 全局 skill | 项目级浏览器自动化 |

### ✅ 已有测试资产

- **后端 pytest 测试**: 1828 个测试（单元 + 集成），覆盖率 93.48%
- **UI 测试脚本**: `service/tests/ui_test.py` — Playwright 全栈测试（登录、页面导航、API 端点验证）
- **前端 mock**: `vite-plugin-fake-server` 提供开发环境 mock 数据
- **Docker Compose**: `service/docker/docker-compose.yml` — FastAPI + PostgreSQL + Redis

### ⚠️ 当前缺失

| 缺失项 | 影响 |
|--------|------|
| OpenCode 中**未配置任何 MCP Server** (`mcpServers: {}`) | 无法直接通过 MCP 工具调用浏览器 |
| 前端 `package.json` **无 Playwright/Cypress 依赖** | 无法在前端侧运行 `npx playwright test` |
| **无 CI workflow** (`.github/` 不存在) | 无法在 CI 中自动执行全栈测试 |
| **无后端 Playwright 依赖** (仅系统全局安装) | 在 venv 中运行 `ui_test.py` 需系统级 playwright |

---

## 2. MCP Server 配置

### 2.1 Playwright MCP Server（核心推荐）

这是**最直接**的方式——通过 MCP 协议让 OpenCode AI 直接操控浏览器进行测试。

**安装**:
```bash
npm install -g @playwright/mcp
# 或项目级安装
cd /mnt/e/GitHub/Hello-FastApi
npm init -y  # 如果项目根没有 package.json
npm install @playwright/mcp
```

**配置到 `~/.config/opencode/opencode.json`**:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp", "--headless"],
      "env": {}
    }
  }
}
```

> 参数说明：`--headless` 无头模式；不加则以有头模式运行（可看浏览器窗口）。
> 也可以使用 `--port 31000` 指定端口。

**验证**:
重启 OpenCode 后，AI 将拥有 `browser_navigate`、`browser_click`、`browser_snapshot` 等 MCP 工具，可直接操作浏览器。

### 2.2 agent-browser MCP（备选）

agent-browser 也可以封装为 MCP Server，但它本身是 CLI 工具，通过 Bash 调用更直接。

```json
{
  "mcpServers": {
    "agent-browser": {
      "command": "agent-browser",
      "args": ["--json"],
      "env": {}
    }
  }
}
```

> 注意：agent-browser 0.25.3 的原生 MCP 支持可能有限。更推荐直接通过 Bash 工具调用 `agent-browser` CLI，或者使用 Playwright MCP。

---

## 3. 自动化联调测试方案

### 方案 A：通过 OpenCode Agent 编排（推荐）

在 OpenCode 中，利用 `task` + 后台 agent + bash 工具编排完整测试流程：

```
┌─────────────────────────────────────────┐
│        OpenCode Orchestrator            │
│  (Sisyphus / Plan Agent)                │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────┐    ┌──────────┐  │
│  │  Bash: Start BE  │    │ Bash:    │  │
│  │  uvicorn :8000   │───▶│ Start FE │  │
│  └──────────────────┘    │ Vite:8848│  │
│                          └──────────┘  │
│                                │        │
│                                ▼        │
│  ┌──────────────────────────────────┐   │
│  │  Playwright MCP / agent-browser  │   │
│  │  → 登录                          │   │
│  │  → 导航页面                      │   │
│  │  → 验证 UI 元素                  │   │
│  │  → API 请求验证                  │   │
│  └──────────────────────────────────┘   │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  pytest（单独后端测试）           │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

#### 实现步骤：

1. **启动后端**（后台 agent）：
```bash
cd /mnt/e/GitHub/Hello-FastApi/service
source .venv_linux/bin/activate
python -m scripts.cli runserver
```

2. **启动前端**（后台 agent）：
```bash
cd /mnt/e/GitHub/Hello-FastApi/web
pnpm dev
```

3. **等待服务就绪**（health check）：
```bash
curl -f http://localhost:8000/health
curl -f http://localhost:8848
```

4. **执行 Playwright 测试**（通过 MCP 或 Bash）：
```bash
# 运行已有 UI 测试
source .venv_linux/bin/activate
cd /mnt/e/GitHub/Hello-FastApi/service
python -m tests.ui_test
```

#### 在 OpenCode 中使用的命令模板：

```python
# 并行启动前后端
task(category="quick", run_in_background=true, prompt="cd service && source .venv_linux/bin/activate && python -m scripts.cli runserver", description="Start backend")
task(category="quick", run_in_background=true, prompt="cd web && pnpm dev", description="Start frontend")

# 等待就绪后执行 UI 测试
task(category="quick", prompt="cd service && source .venv_linux/bin/activate && python -m tests.ui_test", description="Run UI tests")
```

### 方案 B：Docker Compose 全栈测试

使用已有 Docker Compose 一键启动所有服务：

```bash
cd /mnt/e/GitHub/Hello-FastApi/service/docker
docker-compose up -d
docker-compose exec app python -m scripts.cli initall
```

然后通过 MCP 浏览器工具对 http://localhost:8848 进行测试。

---

## 4. 需要安装/配置的工具清单

### 4.1 必须配置

| # | 项目 | 说明 | 优先级 |
|---|------|------|--------|
| 1 | **Playwright MCP Server** 配置到 `opencode.json` | 让 AI 获得浏览器操控能力 | P0 |
| 2 | **frontend Playwright 依赖** | `cd web && pnpm add -D @playwright/test` | P1 |

### 4.2 强烈推荐

| # | 项目 | 说明 | 优先级 |
|---|------|------|--------|
| 3 | **Playwright browsers** 安装 | `cd web && npx playwright install chromium` | P1 |
| 4 | **`playwright.config.ts`** 在前端项目配置 | 定义 baseURL、viewport、reporters 等 | P1 |
| 5 | **测试脚本** 自动化启动前后端并运行 UI 测试 | 参考下方脚本示例 | P1 |

### 4.3 可选增强

| # | 项目 | 说明 | 优先级 |
|---|------|------|--------|
| 6 | **CI workflow** (GitHub Actions) | `.github/workflows/fullstack-test.yml` | P2 |
| 7 | **前端 e2e 测试用例** | Playwright test 文件覆盖所有页面 | P2 |
| 8 | **Docker 全栈测试环境** | 在 CI 中使用 docker-compose 启动 | P2 |

---

## 5. 前端 Playwright 配置参考

安装依赖：
```bash
cd /mnt/e/GitHub/Hello-FastApi/web
pnpm add -D @playwright/test
npx playwright install chromium
```

创建 `web/playwright.config.ts`：
```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  expect: { timeout: 5000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["html", { outputFolder: "playwright-report" }],
    ["list"],
  ],
  use: {
    baseURL: "http://localhost:8848",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium", viewport: { width: 1920, height: 1080 } },
    },
  ],
});
```

创建 `web/e2e/login.spec.ts` 示例：
```typescript
import { test, expect } from "@playwright/test";

test("登录成功 - 默认管理员账号", async ({ page }) => {
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  await page.getByPlaceholder(/用户|账号/).fill("admin");
  await page.getByPlaceholder("密码").fill("admin123");
  await page.getByRole("button", { name: /登录/ }).click();

  await expect(page).toHaveURL(/welcome|dashboard/, { timeout: 10000 });
});
```

---

## 6. OpenCode Skill 使用建议

| Skill | 用途 | 触发场景 |
|-------|------|----------|
| `Agent Browser` (项目 skill) | 通过 `agent-browser` CLI 进行浏览器操作 | 单次导航、截图、表单填写 |
| `Playwright (Automation + MCP + Scraper)` (用户 skill) | MCP 驱动的浏览器自动化，或 Playwright 测试脚本编写 | 复杂交互、多步骤测试、页面数据提取 |

**选择建议**：
- **快速验证**（看一眼页面）→ `agent-browser open + snapshot`
- **编写测试脚本** → Playwright MCP 或直接 `@playwright/test`
- **已有脚本运行** → Bash 直接 `python -m tests.ui_test` 或 `npx playwright test`

---

## 7. 完整设置步骤

### 一次性设置

```bash
# 1. 安装 Playwright MCP（全局）
npm install -g @playwright/mcp

# 2. 安装前端 Playwright 依赖
cd /mnt/e/GitHub/Hello-FastApi/web
pnpm add -D @playwright/test
npx playwright install chromium

# 3. 配置 MCP Server 到 opencode.json
# 编辑 ~/.config/opencode/opencode.json，在顶级添加：
# "mcpServers": {
#   "playwright": {
#     "command": "npx",
#     "args": ["@playwright/mcp", "--headless"]
#   }
# }

# 4. 验证
npx playwright --version    # 应 ≥1.59
agent-browser --version     # 应 ≥0.25
```

### 验证安装

```bash
# 重启 OpenCode 后，AI 应能调用以下工具：
# - browser_navigate("http://localhost:8848")
# - browser_snapshot()
# - browser_click() 等 MCP 工具

# 或通过 Bash 直接运行：
cd /mnt/e/GitHub/Hello-FastApi/service
source .venv_linux/bin/activate
python -m tests.ui_test
```

---

## 8. 架构图

```
┌────────────────────────────────────────────────────────────┐
│                   OpenCode Agent                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ task()   │  │ Bash     │  │ MCP      │  │ Skill    │  │
│  │ 编排     │  │ CLI      │  │ Browser  │  │ Playwright│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├──────────┼──────────────┼──────────────┼───────────────────┤
│          ▼              ▼              ▼                   │
│  ┌──────────────┐ ┌──────────┐ ┌────────────────┐        │
│  │ pytest       │ │ uvicorn  │ │ Playwright MCP │        │
│  │ (后端单元/   │ │ (后端服务)│ │ (浏览器操控)   │        │
│  │  集成测试)   │ │ :8000    │ │                │        │
│  └──────────────┘ └──────────┘ └────────────────┘        │
│                          │              │                  │
│                          ▼              ▼                  │
│                    ┌──────────┐  ┌────────────────┐        │
│                    │ Vite Dev │  │ Chromium       │        │
│                    │ (前端)   │  │ Headless Browser│       │
│                    │ :8848    │  │                │        │
│                    └──────────┘  └────────────────┘        │
└────────────────────────────────────────────────────────────┘
```

---

## 9. 常见问题

### Q: Playwright MCP 连接失败？
确保 `@playwright/mcp` 已全局安装，且端口未被占用。尝试：
```bash
npx @playwright/mcp --headless --port 31000
```
然后在 `opencode.json` 中配置对应端口。

### Q: 运行 `python -m tests.ui_test` 报错 "ModuleNotFoundError: playwright"？
Playwright 安装在系统全局，但 venv 中不可见。在 venv 中安装：
```bash
source .venv_linux/bin/activate
uv pip install playwright
playwright install chromium
```

### Q: 前端 Playwright 测试连不上后端？
确保后端先启动（`:8000`），Vite proxy 会自动将 `/api` 请求转发到后端。

### Q: agent-browser 和 Playwright MCP 哪个更好？
- **agent-browser**: 轻量、快速、适合单次操作（导航、截图、简单点击）
- **Playwright MCP**: 功能完整、支持复杂交互（多标签、多步表单、网络拦截）、适合编写测试脚本

建议两者都安装，按需使用。
