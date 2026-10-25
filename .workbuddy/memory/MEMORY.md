# Hello-FastApi 项目长期约定

## E2E（Playwright）运行方式 —— 必须遵守

- **必须串行**：`--workers=1`。默认并发会在 Windows 触发 `WebSocket ERR_NO_BUFFER_SPACE`（Vite HMR 连接耗尽），导致 smoke/crud 出现**假失败**（单独跑却通过）。
- **必须禁用 safe-delete**（`CODEBUDDY_SAFE_DELETE_ENABLED=0`）。两类场景会被 WorkBuddy safe-delete 批量守卫（阈值 50）拦截并导致失败：
  - Playwright 启动清理 `web/test-results`（>50 文件）→ 进程中止、**0 用例执行**；
  - `vite build` 用 rimraf 清理 `web/dist`（恰好 50 个 .gz.br）→ build exit=1。
  因此 E2E 与 build 都要带该环境变量。
- 命令：
  ```bash
  cd web && CODEBUDDY_SAFE_DELETE_ENABLED=0 node node_modules/@playwright/test/cli.js test --workers=1 --reporter=list
  ```
  单跑某个 spec：`... test --workers=1 --project=crud crud-dept.spec.ts`
- **端口**：Playwright `baseURL` 默认 `http://localhost:8848`；vite 默认起 8848，若端口被占用会漂移到 8849，此时 E2E 全部失败（注意排查旧进程）。后端固定 8000。
- **登录凭据**：`admin` / `admin123`（`web/e2e/utils/auth.setup.ts`）。
- 前置：后端 `cd service && APP_ENV=development ./.venv/Scripts/python.exe -m scripts.cli runserver`；前端 `cd web && VITE_SKIP_CAPTCHA=true pnpm dev`。
- **跑前必查 Redis 是否真的连上**（2026-10-25 更正）：不要只看 `netstat :6379` LISTENING，要直接看后端启动日志是否打印 **`Redis 连接初始化完成`**。出现 `Redis 连接初始化失败，缓存功能将降级为直接查库` 时，每个缓存操作等一次 1s 连接超时，单请求可到 3.2s，E2E 的 `networkidle` 与 10s 表格断言均为临界值 → **随机用例假失败**（2026-10-21 实测三轮失败用例均不同、单独复跑全过）。
  - **真根因已定位并修复**：`service/src/config/settings.py` 里 `Settings(env_file=...)` 参数名写错，应为 `_env_file=`；写错时 pydantic-settings 静默丢弃，`.env.development` 从未加载，`REDIS_URL` 落到默认值 `redis://localhost:6379/0`，Windows 下 `localhost` 解析到 IPv6 `::1`，而本机 Redis（v3.2.100，`D:\Program Files\Redis\`）只监听 IPv4 → 异步连接必超时。**不是** RESP3/protocol 问题，项目早已正确配 `protocol=2`。
  - 排障顺序：`netstat` → 后端日志 → `redis-cli ping`（能通不代表异步能通）→ 用项目 venv 跑 `await get_redis().ping()` 复现。
- **E2E flaky 判定法**：全量跑失败用例每次不同 + 单独复跑通过 ⇒ 环境/配置问题，不是代码回归。用 `git stash push -- <改动文件>` 做 A/B 对照可确证。

## 样式与配置的两个静默失效陷阱（都真的踩过）

1. **全局 `.scss` 里不能写 `:deep()`**。
   `:deep()` 由 `@vitejs/plugin-vue` 在编译 SFC 的 `<style scoped>` 时重写，独立 `.scss`
   不经过该处理，产物保留字面量 `:deep(...)` → 无效选择器 → **整条规则被浏览器丢弃**，
   而且 `pnpm build` 照样成功，不报任何错。
   校验：`grep ':deep(' web/dist/static/css/index-*.css` 应为 0。

2. **pydantic-settings v2 的 `__init__` 参数是 `_env_file`（带下划线）**，不是 `env_file`。
   写错会被当成未知字段、在 `extra="ignore"` 下静默丢弃 → `.env.*` 全部不加载、全站跑默认值。
   判别：`Settings(_env_file=[...]).REDIS_URL` 与 `Settings(env_file=[...]).REDIS_URL` 对比。

## 全量验证基线（2026-09-09）

| 项 | 结果 |
|---|---|
| E2E | 51/51 通过（串行 9.9m） |
| 后端 pytest | 2166 通过（2002 unit + 164 integration） |
| vue-tsc / eslint / build | 0 错误 / 0 错误 / 成功 |

## Git 推送认证

- 全局 gitconfig 已配 HTTP(S) 代理（`127.0.0.1:31180/31181`）但**未配 `credential.helper`**，HTTPS 推送会报 `could not read Username for 'https://github.com'`（非交互模式无法提示）。
- 解决：`git config credential.helper manager`（复用 Windows 凭据管理器，其中已存 GitHub 凭据）。无 SSH 密钥、无 `gh` CLI，不要走 SSH 方案。

## 架构与数据要点

- **表名前缀**：后端表均带 `sys_` 前缀（如 `sys_departments`、`sys_users`），写 SQL/查库时**不要**用无前缀名。
- `sys_departments.code` 为 `NOT NULL` + `UNIQUE`；部门表单无「编码」输入项，提交时由 hook 生成唯一编码，避免空串冲突后端 500。
- vue-router 为 **hash 模式**（`createWebHashHistory`），E2E 导航必须 `/#/path`。
- `/account-settings` 属 `remaining.ts` 全屏路由，**不渲染** `.app-main` 布局，也没有表格；通用页面断言不可假设「必有表格」。
- 测试残留数据会让 E2E 反复失败：CRUD 用例用 `makeUniqueName` 命名 + `afterAll` 调 `cleanupByApi` 兜底清理；失败时不会清理，必要时手动清 `service/sql/dev.db`。

## 文档路径勘误

- 后端 Swagger 实际在 `http://localhost:8000/docs`（**不是** `/api/docs`，后者 404）。`CODEBUDDY.md`（根与 service 下）里写的 `/api/docs` 已过时。
- `service/CODEBUDDY.md` 描述「仓储层用 FastCRUD」已过时，实际已迁移到自研 `GenericRepository`（`infrastructure/repositories/base.py`），`mypy.ini` 里的 `[mypy-fastcrud.*]` 也是死配置。
