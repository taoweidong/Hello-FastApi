# OpenCode + Playwright MCP 实现 Hello-FastApi（Vue3 + FastAPI）全栈项目联调与 Web 自动化测试实战指南

> **作者**: AI 技术实践团队  
> **日期**: 2026-05-23  
> **标签**: OpenCode, Playwright MCP, Vue3, FastAPI, Element Plus, Pure Admin, Web 自动化测试, E2E 测试, AI 驱动测试, DDD 架构

---

## 目录

- [1. 前言](#1-前言)
- [2. 项目概览](#2-项目概览)
- [3. 环境准备与安装](#3-环境准备与安装)
  - [3.1 环境要求](#31-环境要求)
  - [3.2 克隆项目](#32-克隆项目)
  - [3.3 后端启动（service）](#33-后端启动service)
  - [3.4 前端启动（web）](#34-前端启动web)
  - [3.5 OpenCode IDE 安装与配置](#35-opencode-ide-安装与配置)
  - [3.6 Playwright MCP Server 配置](#36-playwright-mcp-server-配置)
- [4. 项目架构详解](#4-项目架构详解)
  - [4.1 后端 DDD 四层架构](#41-后端ddd四层架构)
  - [4.2 前端 Pure Admin 架构](#42-前端-pure-admin-架构)
- [5. Playwright MCP 核心能力详解](#5-playwright-mcp-核心能力详解)
  - [5.1 浏览器控制工具](#51-浏览器控制工具)
  - [5.2 页面交互工具](#52-页面交互工具)
  - [5.3 数据提取与断言工具](#53-数据提取与断言工具)
  - [5.4 代码生成（Codegen）能力](#54-代码生成codegen能力)
  - [5.5 HTTP API 测试工具](#55-http-api-测试工具)
- [6. Hello-FastApi 联调实战](#6-hello-fastapi-联调实战)
  - [6.1 场景一：JWT 登录与 RBAC 权限验证](#61-场景一jwt-登录与-rbac-权限验证)
  - [6.2 场景二：用户管理 CRUD 操作测试](#62-场景二用户管理-crud-操作测试)
  - [6.3 场景三：菜单管理与动态路由测试](#63-场景三菜单管理与动态路由测试)
  - [6.4 场景四：操作日志与系统监控](#64-场景四操作日志与系统监控)
  - [6.5 场景五：前端异常捕获与修复](#65-场景五前端异常捕获与修复)
  - [6.6 场景六：响应式布局与多设备适配](#66-场景六响应式布局与多设备适配)
- [7. 常见问题与修复方案](#7-常见问题与修复方案)
  - [7.1 MCP Server 连接失败](#71-mcp-server-连接失败)
  - [7.2 Element Plus 组件定位超时](#72-element-plus-组件定位超时)
  - [7.3 JWT Token 失效与刷新](#73-jwt-token-失效与刷新)
  - [7.4 跨域与 Cookie 问题](#74-跨域与-cookie-问题)
  - [7.5 测试环境隔离与数据清理](#75-测试环境隔离与数据清理)
- [8. CI/CD 集成（Jenkins + GitHub Actions）](#8-cicd-集成jenkins--github-actions)
- [9. 最佳实践总结](#9-最佳实践总结)
- [10. 结语](#10-结语)

---

## 1. 前言

在现代全栈开发中，**Vue 3 + FastAPI** 已成为构建高性能 Web 应用的热门组合。然而，前后端联调、端到端（E2E）测试以及 UI 回归测试往往耗费大量人力。随着 **MCP（Model Context Protocol）** 协议的兴起，AI 驱动的自动化测试工具正在改变这一现状。

**Hello-FastApi** 是一个基于 **Vue3 + FastAPI** 的全栈中后台管理系统，前端基于 **Pure Admin**（Vue3 + TypeScript + Element Plus + Vite），后端采用 **FastAPI + SQLModel + DDD 四层架构**，实现了完整的 JWT 双令牌认证、RBAC 权限控制、菜单管理、用户管理、操作日志等中后台核心功能。该项目已在 GitHub 开源：https://github.com/taoweidong/Hello-FastApi

**OpenCode** 是一款开源 AI 编码代理，原生支持 MCP 协议扩展。通过集成 **Playwright MCP Server**，开发者可以用自然语言描述测试需求，由 AI 自动完成浏览器操作、断言验证、截图对比，甚至自动生成可复用的测试脚本。本文将手把手指导你如何在 OpenCode 中配置 Playwright MCP，实现对 Hello-FastApi 项目的全栈联调与自动化测试。

---

## 2. 项目概览

### 2.1 技术栈

| 层级 | 技术 | 版本建议 | 作用 |
|------|------|----------|------|
| **IDE** | OpenCode | 最新版 | AI 编码代理，提供 MCP 集成能力 |
| **测试引擎** | Playwright MCP | `@latest` | 浏览器自动化与 API 测试 |
| **前端框架** | Vue 3 + TypeScript + Element Plus + Vite | 3.4+ | 构建中后台管理界面 |
| **后端框架** | FastAPI + SQLModel + DDD | 0.110+ | 提供 RESTful API |
| **数据库** | SQLite (开发) / PostgreSQL (生产) | - | 数据持久化 |
| **缓存** | Redis | - | 会话缓存、限流计数 |
| **认证** | JWT 双令牌 + RBAC | - | 权限控制与身份认证 |
| **测试** | pytest + Playwright | - | 单元测试 + E2E 测试 |

### 2.2 项目结构

```
Hello-FastApi/
├── service/                    # 后端服务（FastAPI + DDD 架构）
│   ├── src/                    # 源代码（DDD 四层）
│   │   ├── api/                # API 层（路由、DTO、依赖注入）
│   │   ├── application/        # 应用层（用例、服务编排）
│   │   ├── domain/             # 领域层（实体、值对象、领域服务）
│   │   └── infrastructure/     # 基础设施层（数据库、缓存、外部服务）
│   ├── tests/                  # 测试代码（1828 tests，覆盖率 93.48%）
│   ├── docker/                 # Docker 配置
│   ├── scripts/                # CLI 管理脚本（initdb、seedrbac 等）
│   └── alembic/                # 数据库迁移
├── web/                        # 前端项目（Vue3 + Pure Admin）
│   ├── src/
│   │   ├── views/              # 页面视图
│   │   ├── components/         # 公共组件
│   │   ├── store/              # Pinia 状态管理
│   │   ├── api/                # Axios 请求封装
│   │   └── router/             # 动态路由
│   └── vite.config.ts
├── docs/                       # 项目文档
├── .opencode/                  # OpenCode 配置（含 code-gen、git-release 技能）
└── README.md
```

### 2.3 服务端口

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:8848 | 管理后台 |
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 默认账号 | admin / admin123 | 超级管理员 |

---

## 3. 环境准备与安装

### 3.1 环境要求

- **Python >= 3.10**
- **Node.js >= 20.19** 或 >= 22.13
- **pnpm >= 9**
- **uv**（Python 包管理器，推荐）

### 3.2 克隆项目

```bash
git clone https://github.com/taoweidong/Hello-FastApi.git
cd Hello-FastApi
```

### 3.3 后端启动（service）

```bash
cd service

# 创建虚拟环境（使用 uv）
uv venv --python 3.10
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖并初始化
uv pip install -e ".[dev]"

# 初始化数据库、种子数据、RBAC 权限
python -m scripts.cli initall

# 启动服务
python -m scripts.cli runserver
```

**CLI 管理命令说明：**

| 命令 | 说明 |
|------|------|
| `python -m scripts.cli initdb` | 初始化数据库表结构 |
| `python -m scripts.cli seedrbac` | 种子 RBAC 权限数据 |
| `python -m scripts.cli createsuperuser` | 创建超级管理员 |
| `python -m scripts.cli runserver` | 启动开发服务器 |

### 3.4 前端启动（web）

```bash
cd web
pnpm install
pnpm dev
```

前端服务将在 http://localhost:8848 启动。

### 3.5 OpenCode IDE 安装与配置

Hello-FastApi 项目已内置 `.opencode` 目录，包含 code-gen、git-release 等技能配置。你可以直接使用项目级配置，或全局安装 OpenCode：

```bash
# macOS / Linux
curl -fsSL https://opencode.ai/install | bash

# 验证安装
opencode --version
```

配置 LLM 提供商（以 Anthropic Claude 为例）：

```bash
opencode auth login
# 选择 Anthropic → 输入 API Key
```

启动 OpenCode：

```bash
opencode
```

### 3.6 Playwright MCP Server 配置

在 Hello-FastApi 项目根目录创建或更新 `opencode.json`：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp@latest"],
      "enabled": true,
      "environment": {
        "PLAYWRIGHT_BROWSERS_PATH": "0"
      }
    }
  },
  "tools": {
    "playwright": true
  }
}
```

**配置说明：**
- `type`: `"local"` 表示本地启动 MCP Server
- `command`: 使用 `npx -y` 自动安装并运行最新版 Playwright MCP
- `enabled`: 启用该 MCP Server
- `environment`: 可选环境变量，控制浏览器下载路径

配置完成后，重启 OpenCode 使配置生效。在对话中输入以下指令验证：

```
使用 Playwright MCP 打开 http://localhost:8848 并截图
```

---

## 4. 项目架构详解

### 4.1 后端 DDD 四层架构

Hello-FastApi 后端采用 **领域驱动设计（DDD）** 四层架构，确保业务逻辑清晰、可测试、可维护：

```
service/src/
├── api/                        # API 层（接口适配器）
│   ├── v1/
│   │   ├── auth.py             # 认证接口（登录、刷新令牌、登出）
│   │   ├── users.py            # 用户管理接口
│   │   ├── roles.py            # 角色管理接口
│   │   ├── menus.py            # 菜单管理接口
│   │   └── logs.py             # 操作日志接口
│   └── dependencies.py         # FastAPI 依赖注入（JWT 验证、权限检查）
├── application/                # 应用层（用例编排）
│   ├── services/
│   │   ├── auth_service.py     # 认证服务（登录、令牌管理）
│   │   ├── user_service.py     # 用户服务（CRUD、分页）
│   │   └── menu_service.py     # 菜单服务（树形结构、动态路由）
│   └── dto/                    # 数据传输对象
├── domain/                     # 领域层（核心业务）
│   ├── entities/
│   │   ├── user.py             # 用户实体
│   │   ├── role.py             # 角色实体
│   │   └── menu.py             # 菜单实体
│   ├── repositories/           # 仓库接口（依赖倒置）
│   └── services/               # 领域服务
└── infrastructure/             # 基础设施层
    ├── database/
    │   ├── models.py           # SQLModel 数据模型
    │   └── repositories/       # 仓库实现
    ├── cache/
    │   └── redis_client.py     # Redis 缓存客户端
    └── security/
        └── jwt_handler.py      # JWT 令牌处理
```

**关键设计特点：**
- **依赖倒置原则（DIP）**：领域层不依赖基础设施层，通过接口抽象
- **JWT 双令牌**：Access Token（短期）+ Refresh Token（长期），支持自动刷新
- **RBAC 权限控制**：用户 → 角色 → 权限 → 菜单，四级权限模型
- **Alembic 迁移**：数据库版本管理，支持回滚
- **限流中间件**：基于 Redis 的全局 SlowAPI 限流

### 4.2 前端 Pure Admin 架构

前端基于 **Pure Admin** 框架，采用 Vue3 + TypeScript + Element Plus：

```
web/src/
├── views/
│   ├── login/                  # 登录页
│   ├── system/
│   │   ├── user/index.vue      # 用户管理
│   │   ├── role/index.vue      # 角色管理
│   │   ├── menu/index.vue      # 菜单管理
│   │   └── log/index.vue       # 操作日志
│   └── error/                  # 错误页
├── components/
│   ├── RePureTable/            # 表格封装
│   ├── ReDialog/               # 对话框封装
│   └── ReIcon/                 # 图标组件
├── store/
│   ├── modules/
│   │   ├── user.ts             # 用户状态（JWT、用户信息）
│   │   ├── permission.ts       # 权限状态（路由、按钮权限）
│   │   └── app.ts              # 应用状态（主题、布局）
├── api/
│   ├── auth.ts                 # 认证 API
│   ├── user.ts                 # 用户 API
│   └── system.ts               # 系统管理 API
└── router/
    ├── index.ts                # 路由入口
    └── modules/                # 动态路由模块
```

**关键设计特点：**
- **动态路由**：根据后端返回的菜单数据动态生成路由
- **按钮级权限**：通过 `v-permission` 指令控制按钮显示
- **Axios 封装**：统一请求拦截（添加 Token）、响应拦截（处理 401/403）
- **Element Plus 组件库**：表格、表单、对话框、树形控件等

---

## 5. Playwright MCP 核心能力详解

Playwright MCP Server 提供了一套完整的工具集，让 AI 能够像人类一样操作浏览器并执行断言。

### 5.1 浏览器控制工具

| 工具名 | 功能描述 |
|--------|----------|
| `playwright_navigate` | 导航到指定 URL |
| `playwright_resize` | 调整浏览器视口大小，支持 143+ 设备预设 |
| `playwright_close` | 关闭浏览器并释放资源 |
| `playwright_custom_user_agent` | 设置自定义 User-Agent |

**示例指令（在 OpenCode 中使用）：**

```
使用 Playwright 打开 http://localhost:8848，
并将浏览器窗口调整为 Desktop（1920x1080）尺寸，
截图保存到 tests/screenshots/login-desktop.png
```

### 5.2 页面交互工具

| 工具名 | 功能描述 |
|--------|----------|
| `playwright_click` | 点击页面元素 |
| `playwright_fill` | 在输入框中填写文本 |
| `playwright_select` | 选择下拉框选项 |
| `playwright_hover` | 悬停在元素上 |
| `playwright_upload_file` | 上传文件 |
| `playwright_evaluate` | 在浏览器控制台执行 JavaScript |

**示例指令：**

```
打开登录页面 http://localhost:8848，
在用户名输入框填写 "admin"，
在密码输入框填写 "admin123"，
点击登录按钮
```

### 5.3 数据提取与断言工具

| 工具名 | 功能描述 |
|--------|----------|
| `playwright_get_visible_text` | 获取页面可见文本 |
| `playwright_get_visible_html` | 获取页面 HTML 内容 |
| `playwright_screenshot` | 截图（支持全页/元素截图） |
| `playwright_console_logs` | 捕获浏览器控制台日志 |

**示例指令：**

```
登录后截图保存到 tests/screenshots/dashboard.png，
检查页面是否包含 "系统管理" 菜单，
并检查控制台是否有错误日志
```

### 5.4 代码生成（Codegen）能力

这是 Playwright MCP 最强大的功能之一。通过 `start_codegen_session` 和 `end_codegen_session`，AI 可以录制你的手动操作并自动生成可复用的 Playwright 测试脚本。

**工作流程：**

```
1. 用户: "开始录制 Hello-FastApi 登录测试流程"
   → AI 调用 start_codegen_session

2. 用户手动操作浏览器（或 AI 自动执行）
   → 每一步操作被记录

3. 用户: "结束录制并生成测试脚本"
   → AI 调用 end_codegen_session
   → 生成 tests/e2e/login.spec.ts
```

**生成的测试脚本示例：**

```typescript
import { test, expect } from '@playwright/test';

test('Hello-FastApi 管理员登录流程', async ({ page }) => {
  await page.goto('http://localhost:8848');

  // 等待登录页加载
  await page.waitForSelector('input[placeholder="用户名"]', { timeout: 10000 });

  // 填写登录表单
  await page.fill('input[placeholder="用户名"]', 'admin');
  await page.fill('input[placeholder="密码"]', 'admin123');

  // 点击登录
  await page.click('button:has-text("登录")');

  // 验证登录成功 - 等待 Dashboard 加载
  await page.waitForSelector('.sidebar-container', { timeout: 15000 });
  await expect(page.locator('.sidebar-container')).toBeVisible();

  // 验证菜单包含系统管理
  await expect(page.locator('text=系统管理')).toBeVisible();
});
```

### 5.5 HTTP API 测试工具

Playwright MCP 不仅支持 UI 测试，还内置了 HTTP 请求工具，可直接测试后端 API：

| 工具名 | 功能描述 |
|--------|----------|
| `playwright_get` | 执行 HTTP GET 请求 |
| `playwright_post` | 执行 HTTP POST 请求 |
| `playwright_put` | 执行 HTTP PUT 请求 |
| `playwright_delete` | 执行 HTTP DELETE 请求 |
| `playwright_expect_response` | 开始等待特定 HTTP 响应 |
| `playwright_assert_response` | 断言等待的响应内容 |

**示例指令（API + UI 联动测试）：**

```
先调用 POST http://localhost:8000/api/v1/auth/login 接口，
请求体 {"username":"admin","password":"admin123"}，
验证返回的 access_token 字段存在且不为空，
然后打开前端页面 http://localhost:8848 验证登录状态
```

---

## 6. Hello-FastApi 联调实战

### 6.1 场景一：JWT 登录与 RBAC 权限验证

**测试目标**：验证用户从前端输入账号密码 → 调用后端 `/api/v1/auth/login` → 获取 JWT 双令牌 → 前端存储 Token → 访问受保护页面 → RBAC 权限控制的完整链路。

**OpenCode 指令：**

```
请使用 Playwright MCP 完成 Hello-FastApi 的登录与权限验证测试：

1. 导航到 http://localhost:8848
2. 截图记录登录页初始状态
3. 在用户名输入框填写 "admin"
4. 在密码输入框填写 "admin123"
5. 点击登录按钮
6. 等待页面跳转，验证是否进入 Dashboard（检查 .sidebar-container 是否存在）
7. 验证左侧菜单是否包含 "系统管理"、"用户管理"、"角色管理"
8. 点击 "用户管理" 菜单，验证页面是否加载用户列表表格
9. 检查浏览器 LocalStorage 中是否存储了 access_token 和 refresh_token
10. 截图保存登录成功后的 Dashboard 页面
11. 检查浏览器控制台是否有报错
12. 关闭浏览器
```

**AI 执行流程解析：**

```
用户指令
    ↓
OpenCode 解析意图
    ↓
调用 playwright_navigate → 打开 http://localhost:8848
    ↓
调用 playwright_screenshot → 保存初始截图
    ↓
调用 playwright_fill → 填写用户名 "admin"
    ↓
调用 playwright_fill → 填写密码 "admin123"
    ↓
调用 playwright_click → 点击登录按钮
    ↓
调用 playwright_get_visible_text → 验证页面文本包含 "系统管理"
    ↓
调用 playwright_click → 点击 "用户管理" 菜单
    ↓
调用 playwright_get_visible_html → 验证表格存在
    ↓
调用 playwright_evaluate → 检查 LocalStorage Token
    ↓
调用 playwright_screenshot → 保存 Dashboard 截图
    ↓
调用 playwright_console_logs → 捕获控制台日志
    ↓
调用 playwright_close → 关闭浏览器
    ↓
返回测试报告给用户
```

**预期输出报告：**

```
✅ 测试通过：JWT 登录与 RBAC 权限验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 页面导航: http://localhost:8848
📸 初始截图: tests/screenshots/login-init.png
📝 表单填写: username=admin, password=admin123
🖱️  点击登录按钮
⏳ 等待 Dashboard 加载（最大 15s）
✅ 断言通过: .sidebar-container 可见
✅ 断言通过: 菜单包含 "系统管理"
✅ 断言通过: 菜单包含 "用户管理"
✅ 断言通过: 菜单包含 "角色管理"
🖱️  点击 "用户管理" 菜单
✅ 断言通过: 用户列表表格已加载
🔐 Token 验证: access_token 存在 (长度: 847)
🔐 Token 验证: refresh_token 存在 (长度: 847)
📸 成功截图: tests/screenshots/dashboard-admin.png
📋 控制台日志: 0 errors, 0 warnings
🔒 浏览器已关闭
```

### 6.2 场景二：用户管理 CRUD 操作测试

**测试目标**：验证前端用户管理页面能够正确调用后端 API 完成增删改查操作。

**后端 API 接口：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/users` | 获取用户列表（分页） |
| POST | `/api/v1/users` | 创建用户 |
| PUT | `/api/v1/users/{id}` | 更新用户 |
| DELETE | `/api/v1/users/{id}` | 删除用户 |

**OpenCode 测试指令：**

```
请使用 Playwright MCP 测试 Hello-FastApi 用户管理页面的完整 CRUD 流程：

前置条件：
1. 先调用 POST http://localhost:8000/api/v1/auth/login
   获取管理员 Token（admin / admin123）

测试步骤：
2. 导航到 http://localhost:8848
3. 使用获取的 Token 完成登录（或直接填写表单登录）
4. 点击 "系统管理" → "用户管理"
5. 验证用户表格已加载，至少显示 admin 用户
6. 点击 "新增" 按钮
7. 在弹出的对话框中填写：
   - 用户名: testuser001
   - 昵称: 测试用户
   - 邮箱: test001@example.com
   - 手机号: 13800138001
   - 密码: Test@123456
   - 角色: 普通用户
8. 点击 "确定" 保存
9. 验证表格中出现新用户 "testuser001"
10. 点击该用户的 "编辑" 按钮
11. 修改昵称为 "测试用户已修改"
12. 点击 "确定"
13. 验证昵称已更新
14. 点击该用户的 "删除" 按钮
15. 在确认对话框中点击 "确定"
16. 验证 "testuser001" 已从表格中消失
17. 同时调用 GET http://localhost:8000/api/v1/users?page=1&size=10
    使用 Bearer Token 验证后端数据一致性
18. 截图保存测试结果
```

**Element Plus 组件定位技巧：**

```typescript
// 针对 Element Plus 的 el-dialog、el-form、el-table 组件
// 使用更精确的选择器

// 点击新增按钮（Element Plus 按钮）
await page.click('button:has-text("新增")');

// 等待对话框出现（el-dialog）
await page.waitForSelector('.el-dialog', { timeout: 5000 });

// 填写表单（el-input）
await page.fill('.el-dialog input[placeholder="用户名"]', 'testuser001');
await page.fill('.el-dialog input[placeholder="昵称"]', '测试用户');

// 选择角色（el-select）
await page.click('.el-dialog .el-select');
await page.click('.el-select-dropdown__item:has-text("普通用户")');

// 点击确定（el-button type="primary"）
await page.click('.el-dialog .el-button--primary:has-text("确定")');

// 等待表格刷新（el-table）
await page.waitForSelector('.el-table__body tr:has-text("testuser001")');
```

### 6.3 场景三：菜单管理与动态路由测试

**测试目标**：验证菜单的增删改查能够正确影响前端动态路由。

**OpenCode 测试指令：**

```
请测试 Hello-FastApi 的菜单管理功能：

1. 以 admin 身份登录 http://localhost:8848
2. 点击 "系统管理" → "菜单管理"
3. 验证菜单树形结构已加载（包含 "系统管理"、"用户管理" 等）
4. 点击 "新增" 按钮，添加一个测试菜单：
   - 菜单名称: 测试菜单
   - 路由路径: /test-page
   - 组件路径: views/test/index.vue
   - 图标: el-icon-star
   - 排序: 999
   - 父菜单: 顶级菜单
5. 点击 "确定"
6. 验证菜单树中出现 "测试菜单"
7. 刷新页面（F5）
8. 验证左侧导航栏出现 "测试菜单"
9. 点击 "测试菜单"
10. 验证页面导航到 /test-page（可能显示 404，这是正常的，因为组件不存在）
11. 删除 "测试菜单"
12. 刷新页面，验证菜单已消失
13. 截图记录每个关键步骤
```

### 6.4 场景四：操作日志与系统监控

**测试目标**：验证操作日志是否正确记录用户的 CRUD 操作。

**OpenCode 测试指令：**

```
请测试 Hello-FastApi 的操作日志功能：

1. 以 admin 身份登录
2. 执行以下操作（每个操作间隔 2 秒）：
   a. 进入用户管理，新增一个用户 "logtest01"
   b. 编辑该用户，修改昵称为 "logtest01-modified"
   c. 删除该用户
3. 点击 "系统监控" → "操作日志"
4. 验证操作日志表格中至少包含 3 条记录：
   - 新增用户 logtest01
   - 编辑用户 logtest01
   - 删除用户 logtest01
5. 验证每条记录包含：操作人、操作时间、操作类型、请求路径、IP 地址
6. 截图保存操作日志页面
```

### 6.5 场景五：前端异常捕获与修复

**测试目标**：主动发现前端运行时错误并定位修复。

**OpenCode 指令：**

```
打开 http://localhost:8848，执行以下操作：
1. 在页面加载完成后，检查浏览器控制台日志
2. 登录后依次访问以下页面：
   - 用户管理
   - 角色管理
   - 菜单管理
   - 操作日志
3. 每个页面停留 3 秒，检查控制台日志
4. 如果存在任何 error 级别的日志，截图并记录错误信息
5. 分析错误原因，如果是代码问题，请定位到具体文件并修复
6. 修复后重新验证
```

**常见前端异常及修复方案：**

| 异常类型 | 错误示例 | 修复方案 |
|----------|----------|----------|
| **未定义变量** | `ReferenceError: xxx is not defined` | 检查变量声明，添加默认值或可选链操作符 |
| **API 404** | `Failed to load resource: 404` | 检查后端接口路径是否正确，确保后端服务已启动 |
| **Vue 渲染错误** | `Cannot read properties of undefined` | 使用 `v-if` 做数据存在性判断，或添加 `?.` 可选链 |
| **网络超时** | `TimeoutError` | 增加 Axios 超时配置，添加 loading 和重试机制 |
| **Element Plus 样式异常** | `el-table` 列错位 | 检查 `doLayout` 调用时机，确保数据加载后刷新表格 |

**修复示例**（处理 API 返回空数据导致的渲染错误）：

```vue
<!-- 修复前 -->
<el-table :data="userList">
  <el-table-column prop="name" label="姓名">
    <template #default="{ row }">
      {{ row.name.toUpperCase() }}  <!-- 可能报错 -->
    </template>
  </el-table-column>
</el-table>

<!-- 修复后 -->
<el-table :data="userList" v-loading="loading">
  <el-table-column prop="name" label="姓名">
    <template #default="{ row }">
      {{ row.name?.toUpperCase() || '-' }}
    </template>
  </el-table-column>
</el-table>
```

### 6.6 场景六：响应式布局与多设备适配

**测试目标**：验证中后台页面在不同设备尺寸下的显示效果。

**OpenCode 指令：**

```
请测试 Hello-FastApi 登录页和管理页在以下设备上的显示效果：
1. Desktop（1920x1080）
2. iPad Pro（1024x1366）
3. iPhone 13（390x844）

对每个尺寸：
- 调整浏览器视口
- 截图保存到 tests/screenshots/responsive/
- 检查登录表单是否正常显示，按钮是否可点击
- 检查侧边栏菜单是否正常显示（移动端应自动折叠）
- 记录任何布局错乱问题
```

Playwright MCP 的 `playwright_resize` 工具支持 143+ 种设备预设，AI 会自动匹配正确的视口尺寸和 User-Agent。

---

## 7. 常见问题与修复方案

### 7.1 MCP Server 连接失败

**现象**：OpenCode 提示 "无法连接到 Playwright MCP Server"

**排查步骤：**

```bash
# 1. 检查 Node.js 版本（需 >= 18）
node --version

# 2. 手动测试 MCP Server 是否可启动
cd Hello-FastApi
npx -y @playwright/mcp@latest --help

# 3. 检查 Playwright 浏览器是否已安装
npx playwright install chromium

# 4. 查看 OpenCode 日志
# macOS/Linux: ~/.config/opencode/logs/
# Windows: %APPDATA%\opencode\logs\
```

**修复方案：**

```json
// opencode.json 中添加超时配置
{
  "mcp": {
    "playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp@latest"],
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

### 7.2 Element Plus 组件定位超时

**现象**：AI 提示 "Timeout waiting for element"，特别是在 el-dialog、el-table 等组件上。

**原因分析：**
1. Element Plus 组件有动画过渡效果，需要等待动画完成
2. 表格数据是异步加载的，需要等待数据返回
3. 对话框有打开动画，元素可能在动画结束后才完全可见

**修复方案：**

```
在指令中明确要求 AI 等待动画和加载完成：

"打开用户管理页面后等待 3 秒，确保 Element Plus 表格渲染完成"
"点击新增按钮后等待对话框动画结束（约 500ms）再操作表单"
"提交表单后等待表格刷新完成（检查 loading 状态消失）"
```

或在 Vue 组件中添加测试友好的标识：

```vue
<el-table 
  v-loading="loading" 
  element-loading-text="加载中..."
  data-testid="users-table"
>
  ...
</el-table>

<el-dialog 
  v-model="dialogVisible" 
  data-testid="user-form-dialog"
>
  ...
</el-dialog>
```

### 7.3 JWT Token 失效与刷新

**现象**：测试过程中突然跳转到登录页，提示 Token 已过期。

**原因分析：**
Hello-FastApi 使用 JWT 双令牌机制：
- **Access Token**：有效期较短（默认 15 分钟）
- **Refresh Token**：有效期较长（默认 7 天）

当 Access Token 过期时，前端会自动使用 Refresh Token 换取新的 Access Token。如果测试时间过长，可能触发 Token 刷新逻辑。

**修复方案：**

```typescript
// 在 Playwright 测试中处理 Token 刷新
// 可以通过拦截请求来验证刷新逻辑

await page.route('**/api/v1/auth/refresh', async (route) => {
  const response = await route.fetch();
  const json = await response.json();

  // 验证返回了新的 access_token
  expect(json.access_token).toBeDefined();
  expect(json.access_token.length).toBeGreaterThan(0);

  await route.fulfill({ response });
});
```

### 7.4 跨域与 Cookie 问题

**现象**：前端调用后端 API 返回 CORS 错误，或登录状态无法保持。

**修复方案：**

Hello-FastApi 后端已配置 CORS，但在测试环境中可能需要调整：

```python
# service/src/main.py 或配置文件中
# 确保测试前端地址在允许列表中

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8848",
        "http://127.0.0.1:8848",
        "http://localhost:4173",  # Vite preview 端口
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"]
)
```

### 7.5 测试环境隔离与数据清理

**现象**：测试数据污染开发数据库，导致后续测试失败。

**最佳实践：**

```python
# 使用 pytest fixture 提供测试隔离
# service/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from src.main import app

@pytest.fixture(scope="function")
def test_db():
    # 使用内存数据库或独立测试数据库
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

@pytest.fixture
def client(test_db):
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

在 Playwright 测试中使用独立的测试数据：

```typescript
// tests/e2e/setup.ts
export const testUsers = {
  admin: { username: 'admin', password: 'admin123' },
  testUser: { username: 'testuser001', password: 'Test@123456' },
};

// 每个测试后清理数据
export async function cleanupTestData(page: Page) {
  // 调用后端 API 删除测试创建的数据
  // 或重置数据库到初始状态
}
```

---

## 8. CI/CD 集成（Jenkins + GitHub Actions）

Hello-FastApi 项目已内置 Jenkins CI/CD Pipeline，我们可以扩展添加 E2E 测试阶段。

### 8.1 Jenkins Pipeline 扩展

```groovy
// Jenkinsfile 追加 E2E 测试阶段

pipeline {
    agent any

    stages {
        stage('Backend Unit Tests') {
            steps {
                dir('service') {
                    sh 'python -m pytest tests/ -v --cov=src --cov-report=xml'
                }
            }
        }

        stage('Frontend Build') {
            steps {
                dir('web') {
                    sh 'pnpm install'
                    sh 'pnpm build'
                }
            }
        }

        stage('E2E Tests') {
            steps {
                // 启动后端服务
                dir('service') {
                    sh 'python -m scripts.cli initall'
                    sh 'python -m scripts.cli runserver &'
                    sh 'sleep 5'
                }

                // 启动前端服务
                dir('web') {
                    sh 'pnpm dev &'
                    sh 'sleep 5'
                }

                // 安装 Playwright 并运行测试
                sh 'npx playwright install --with-deps'
                sh 'npx playwright test --reporter=html'
            }
            post {
                always {
                    // 归档测试报告
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'playwright-report',
                        reportFiles: 'index.html',
                        reportName: 'Playwright E2E Report'
                    ])

                    // 归档截图
                    archiveArtifacts artifacts: 'tests/screenshots/**/*.png', allowEmptyArchive: true
                }
            }
        }
    }
}
```

### 8.2 GitHub Actions 工作流

```yaml
# .github/workflows/e2e-test.yml
name: Hello-FastApi E2E Tests

on: 
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  e2e-test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v3
        with:
          version: 9

      - name: Install Backend Dependencies
        run: |
          cd service
          pip install uv
          uv venv --python 3.11
          source .venv/bin/activate
          uv pip install -e ".[dev]"

      - name: Initialize Database
        run: |
          cd service
          source .venv/bin/activate
          python -m scripts.cli initall

      - name: Start Backend Server
        run: |
          cd service
          source .venv/bin/activate
          python -m scripts.cli runserver &
          sleep 5

      - name: Install Frontend Dependencies
        run: |
          cd web
          pnpm install

      - name: Start Frontend Server
        run: |
          cd web
          pnpm dev &
          sleep 5

      - name: Install Playwright
        run: |
          cd web
          pnpm add -D @playwright/test
          npx playwright install --with-deps

      - name: Run E2E Tests
        run: |
          cd web
          npx playwright test
        env:
          TEST_BASE_URL: http://localhost:8848
          API_BASE_URL: http://localhost:8000

      - name: Upload Test Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: |
            web/playwright-report/
            web/test-results/
            web/tests/screenshots/
```

---

## 9. 最佳实践总结

### 9.1 元素定位策略

在 Element Plus + Vue 项目中，优先使用以下定位策略：

```vue
<!-- ✅ 推荐：使用 data-testid -->
<el-button data-testid="add-user-btn" type="primary">新增</el-button>
<el-input data-testid="username-input" v-model="form.username" />
<el-table data-testid="users-table" :data="userList">

<!-- ✅ 次选：使用语义化文本 -->
<el-button>确定</el-button>  <!-- 可通过 :has-text("确定") 定位 -->

<!-- ❌ 避免：依赖 Element Plus 内部类名 -->
<!-- 如 .el-button--primary、.el-input__inner 等可能随版本变化 -->
```

### 9.2 测试数据管理

```typescript
// tests/fixtures/test-data.ts
export const testUsers = {
  admin: { username: 'admin', password: 'admin123' },
  operator: { username: 'operator', password: 'Operator@123' },
  newUser: { 
    username: 'testuser001', 
    nickname: '测试用户',
    email: 'test001@example.com',
    phone: '13800138001',
    password: 'Test@123456'
  }
};

export const testMenus = {
  testMenu: {
    name: '测试菜单',
    path: '/test-page',
    component: 'views/test/index.vue',
    icon: 'el-icon-star',
    sort: 999
  }
};
```

### 9.3 截图与报告

在关键步骤截图，便于问题定位：

```
"登录前截图保存到 tests/screenshots/before-login.png"
"登录后截图保存到 tests/screenshots/after-login.png"
"用户管理页面截图保存到 tests/screenshots/user-management.png"
"如果测试失败，截图保存到 tests/screenshots/failure-{timestamp}.png"
```

### 9.4 自然语言指令优化

向 OpenCode 下达指令时，遵循以下原则：

1. **明确 URL**：直接给出完整地址，避免让 AI 点击导航
2. **指定选择器**：使用 `data-testid` 或语义化选择器
3. **分步验证**：每完成一个操作就验证结果
4. **错误处理**：要求 AI 在失败时截图并记录日志
5. **等待策略**：明确等待时间和条件（如等待 loading 消失、对话框动画结束）

### 9.5 与现有测试体系融合

Hello-FastApi 后端已有 1828 个单元测试（覆盖率 93.48%），E2E 测试应与之互补：

| 测试类型 | 覆盖范围 | 执行频率 | 工具 |
|----------|----------|----------|------|
| **单元测试** | 后端业务逻辑、领域模型 | 每次提交 | pytest |
| **集成测试** | API 接口、数据库交互 | 每次提交 | pytest + TestClient |
| **E2E 测试** | 完整用户流程、UI 交互 | 每日/每次发布 | Playwright MCP |
| **视觉回归** | UI 样式一致性 | 每次发布 | Playwright Screenshot |

---

## 10. 结语

通过 OpenCode + Playwright MCP 的组合，我们在 Hello-FastApi（Vue3 + FastAPI）项目上实现了：

- ✅ **零代码启动**：用自然语言描述测试需求，AI 自动执行
- ✅ **全链路覆盖**：从 UI 操作到 API 验证的端到端测试
- ✅ **智能代码生成**：录制操作自动生成可复用的 Playwright 脚本
- ✅ **异常自动修复**：捕获前端错误并定位修复
- ✅ **多设备适配**：一键验证响应式布局
- ✅ **与现有体系融合**：与后端 1828 个单元测试、Jenkins CI/CD 无缝集成

这套方案不仅大幅降低了自动化测试的门槛，更让测试用例的维护成本降至最低。随着 MCP 生态的不断完善，AI 驱动的全栈联调与测试将成为开发流程的标配。

---

## 参考资源

- [Hello-FastApi GitHub 仓库](https://github.com/taoweidong/Hello-FastApi)
- [OpenCode 官方文档 - MCP 服务器配置](https://opencode.ai/docs/zh-cn/mcp-servers/)
- [Playwright MCP GitHub 仓库](https://github.com/microsoft/playwright-mcp)
- [OpenCode Browser MCP Plugin](https://github.com/michaljach/opencode-browser)
- [Playwright 官方文档](https://playwright.dev/)
- [Vue 3 官方文档](https://vuejs.org/)
- [Element Plus 官方文档](https://element-plus.org/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pure Admin 文档](https://yiming_chang.gitee.io/pure-admin-doc/)

---

> 💡 **提示**：本文档中的代码示例可直接复制使用。建议在实际项目中根据业务需求调整选择器和断言逻辑。Hello-FastApi 项目持续更新中，建议关注 GitHub 仓库获取最新版本。

> 🚀 **快速开始**：克隆项目 → 启动前后端服务 → 配置 OpenCode Playwright MCP → 复制本文指令开始测试！
