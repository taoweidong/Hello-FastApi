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
- **多项目并行开发的端口冲突（2026-10-25 实测）**：本机 `think-m2b` 占用 8848/8000 时，本项目改用
  `VITE_PORT=8899 VITE_BACKEND_PORT=8001 pnpm dev` + `PORT=8001` 起后端；E2E 侧
  `E2E_BASE_URL=http://localhost:8899 E2E_API_BASE_URL=http://127.0.0.1:8001`
  （`playwright.config.ts` 与 `e2e/utils/helpers.ts` 均已支持这两个环境变量）。
  **排查法**：`netstat -ano | grep LISTENING` 拿 PID，再 `Get-CimInstance Win32_Process` 看
  CommandLine 归属哪个项目；不要杀别的项目的进程。
- **登录凭据**：`admin` / `admin123`（`web/e2e/utils/auth.setup.ts`）。
- 前置：后端 `cd service && APP_ENV=development ./.venv/Scripts/python.exe -m scripts.cli runserver`；前端 `cd web && VITE_SKIP_CAPTCHA=true pnpm dev`。
- **跑前必查 Redis 是否真的连上**（2026-10-25 更正）：不要只看 `netstat :6379` LISTENING，要直接看后端启动日志是否打印 **`Redis 连接初始化完成`**。出现 `Redis 连接初始化失败，缓存功能将降级为直接查库` 时，每个缓存操作等一次 1s 连接超时，单请求可到 3.2s，E2E 的 `networkidle` 与 10s 表格断言均为临界值 → **随机用例假失败**（2026-10-21 实测三轮失败用例均不同、单独复跑全过）。
  - **真根因已定位并修复**：`service/src/config/settings.py` 里 `Settings(env_file=...)` 参数名写错，应为 `_env_file=`；写错时 pydantic-settings 静默丢弃，`.env.development` 从未加载，`REDIS_URL` 落到默认值 `redis://localhost:6379/0`，Windows 下 `localhost` 解析到 IPv6 `::1`，而本机 Redis（v3.2.100，`D:\Program Files\Redis\`）只监听 IPv4 → 异步连接必超时。**不是** RESP3/protocol 问题，项目早已正确配 `protocol=2`。
  - 排障顺序：`netstat` → 后端日志 → `redis-cli ping`（能通不代表异步能通）→ 用项目 venv 跑 `await get_redis().ping()` 复现。
- **E2E flaky 判定法**：全量跑失败用例每次不同 + 单独复跑通过 ⇒ 环境/配置问题，不是代码回归。用 `git stash push -- <改动文件>` 做 A/B 对照可确证。

## 前端依赖升级约定（2026-10-25 起）

以上游 `pure-admin/vue-pure-admin` master（本项目 fork 源头，同为 v7.0.0）为「已知良好」基线：
**同大版本内取最新；跨大版本只升上游已采用的；无上游参照的跨大版本一律不升**。
上游明确不升的：`typescript` 7（Go 编译器路线）、`@types/node` 26、`@iconify/vue` 5
（精确锁 4.2.0）、`vxe-table`（精确锁 4.6.25）、`intro.js` 8、`cssnano` 9。
核对方式：`curl -s https://raw.githubusercontent.com/pure-admin/vue-pure-admin/master/package.json`。

升级后必须复查的两类破坏：
1. **`defineComponent` 的 props 只写 `default` 不写 `type`** —— Vue 小版本升级会收紧 prop 推断，
   进而 `typeof` 收窄报 TS2345。修法：补 `type: [...] as PropType<any>`（参考 `ReIcon/src/iconifyIconOffline.ts`）。
2. **库的顶层便捷导出被删** —— 如 `@zxcvbn-ts/core` v4 只剩 `ZxcvbnFactory`，写法改为
   `new ZxcvbnFactory().check(pwd).score`（`views/system/user/utils/hook.tsx`）。

### pnpm 12 配置已迁到 `web/pnpm-workspace.yaml`（`package.json` 的 `pnpm` 字段已删除）

pnpm 12 **不再读** `package.json` 的 `pnpm` 字段（`allowedDeprecatedVersions` / `onlyBuiltDependencies`
静默失效）。设置新家：`allowedDeprecatedVersions:`、`allowBuilds:`、`shellEmulator`、
`shamefullyHoist`、`enablePrePostScripts`、`strictPeerDependencies`、`minimumReleaseAge`。
`web/.npmrc` 已删除（四项设置并入 yaml）。
- **新增带原生构建脚本的依赖会让 `pnpm install` exit 1**（`ERR_PNPM_IGNORED_BUILDS`）：
  pnpm 自动往 `allowBuilds` 写占位 `xxx: set this to true or false`，必须显式改 `true/false`。
  当前需显式 `false`：`@tailwindcss/oxide`、`vue3-danmaku`、`node-pty`。
- **install 中断会打烂 node_modules**（`.pnpm` 清空 + 顶层符号链接悬空），后续 install 报
  `ERR_PNPM_PACKAGE_MANAGER_REMOVE_MODULES_DIR ... 拒绝访问`。修法
  `CODEBUDDY_SAFE_DELETE_ENABLED=0 pnpm install --force`；
  判据 `find node_modules -maxdepth 1 -type l ! -exec test -e {} \; -print | wc -l` 应为 0。

### Playwright 升级后必须补装浏览器

`node node_modules/@playwright/test/cli.js install chromium`。
漏装时全部用例报 `browserType.launch: Executable doesn't exist`（N failed / M did not run），
极易误判成代码回归。

## 样式与配置的两个静默失效陷阱（都真的踩过）

1. **全局 `.scss` 里不能写 `:deep()`**。
   `:deep()` 由 `@vitejs/plugin-vue` 在编译 SFC 的 `<style scoped>` 时重写，独立 `.scss`
   不经过该处理，产物保留字面量 `:deep(...)` → 无效选择器 → **整条规则被浏览器丢弃**，
   而且 `pnpm build` 照样成功，不报任何错。
   校验：`grep ':deep(' web/dist/static/css/index-*.css` 应为 0。

2. **pydantic-settings v2 的 `__init__` 参数是 `_env_file`（带下划线）**，不是 `env_file`。
   写错会被当成未知字段、在 `extra="ignore"` 下静默丢弃 → `.env.*` 全部不加载、全站跑默认值。
   判别：`Settings(_env_file=[...]).REDIS_URL` 与 `Settings(env_file=[...]).REDIS_URL` 对比。

## 全量验证基线（2026-10-25 抹库根因修复后）

| 项 | 结果 |
|---|---|
| E2E | 51/51 通过（串行 2.4m） |
| 后端 pytest | 2171 通过（493.68s；事件循环 session 化后较此前 595~605s 快约 2 分钟） |
| dev.db 稳定性 | 全量 pytest 前后 `sys_userloginlog.username` 列与 `alembic_version` 完全一致（见下节） |
| mypy | `alembic/env.py`、`tests/unit/test_alembic_cli.py` 均 0 错 |

## schema drift（版本戳超前、结构落后）—— 真根因已定位并根治（2026-10-25）

现象：某接口 500，日志 `table sys_xxx has no column named yyy`，但 `alembic current` 已显示 head。
**根因（决定性实验证实：pytest 前 True → 2171 passed → pytest 后 False）**：三缺陷叠加——
① `alembic/env.py` 用裸 `Settings()` 而非 `get_settings()`：项目没有 `.env` 文件，且 testing 的
DATABASE_URL 覆盖只在 `get_settings()` 里应用 → `APP_ENV=testing` 时 alembic 静默落到
模型默认值 `sql/dev.db`；② `tests/unit/test_alembic_cli.py` 子进程真实执行 alembic 且未隔离库
（pytest 的 `APP_ENV=testing` 被子进程继承）→ 每次全量 pytest 都对 dev.db 执行
`downgrade -1`（删列）+ `stamp head`（版本戳推回 head 不补 Schema）；③ `scripts/cli.py` 的
`initdb` 已委托 `run_migrate()`，同样受①影响。**已全部修复**（env.py 改 `get_settings()`；
CLI 测试 hermetic 化走 `tmp_path` + `DATABASE_URL`）。应用启动的 `create_all` 只建缺失表、
不加列，**不会自愈**。

若再遇到 drift（如换旧备份），SOP：
1. 备份 `service/sql/dev.db`；
2. `alembic stamp <出错迁移的 down_revision>` → `alembic upgrade head`（迁移本身幂等，回退版本戳后才会真正跑）；
3. **全表结构核对**，防止还有别的 drift：
   ```python
   from sqlmodel import SQLModel; import src.infrastructure.database.models  # 注册全部模型
   # 逐表比对 SQLModel.metadata.tables[t].columns 与 PRAGMA table_info(t)
   ```
已知触发点：`sys_userloginlog.username`（迁移 `c4d5e6f7a8b9_add_login_log_username`，down_revision `a3b5c7d9e1f2`）。
注意 `service/sql/dev.db` **不受 git 跟踪**（`service/.gitignore` 忽略 `sql/*.db`），换机/换备份会复发。
详细分析见 `docs/pytest误伤开发库问题修复.md`。

## 后端两个测试期缺陷（2026-10-25 修复，均已验证）

1. **pytest-asyncio 1.3.0 默认每测试新建事件循环 → Windows 随机假失败**。
   `ProactorEventLoop._make_self_pipe()` 用 `socket.socketpair()`（TCP loopback）实现，
   约 2000 个用例累计耗尽系统缓冲区，随机用例在 fixture setup 阶段报
   `OSError: [WinError 10055]`（三次跑报错位置都不同、单独复跑全过、句柄数恒定 ⇒ 非泄漏）。
   修法：`pyproject.toml` 的 `[tool.pytest.ini_options]` 加
   `asyncio_default_fixture_loop_scope = "session"` 与 `asyncio_default_test_loop_scope = "session"`
   （与本就会话级的 `test_engine`/`test_app` 对齐）。**不要再定义 `event_loop` fixture**——
   pytest-asyncio 1.0+ 已移除覆写支持，写了也是死代码（`tests/conftest.py` 已删并留注释）。
2. **TTL 截断 bug（`int` 向零取整）**：`cache_service._remaining_seconds()` 用 `int(delta)`，
   `now + 86400s` 再算剩余值得 86399，黑名单/在线会话比配置少 1 秒。改 `math.ceil`。
   此前靠 Windows 计时器粒度偶尔同 tick 而侥幸通过——**潜伏缺陷**。

## 配置解析的两个优先级陷阱（2026-10-25 新增，都真的踩过）

1. **裸 `Settings()` 是 footgun**。全仓库只有 `src/config/settings.py` 内部可以裸构造；
   任何需要按 APP_ENV 解析配置的调用方（alembic env、脚本、工具）一律走 `get_settings()`。
   裸构造器只认 `.env`（项目没有该文件）且绕过 `_ENV_OVERRIDES`，`APP_ENV=testing` 下会静默
   落到模型默认值 `sql/dev.db`。
   判别：`APP_ENV=testing python -c "from src.config.settings import Settings, get_settings;
   print(Settings().DATABASE_URL, get_settings().DATABASE_URL)"`，两者必须一致。
2. **pydantic-settings 优先级：构造参数 > 环境变量 > dotenv > 模型默认值**。
   `_ENV_OVERRIDES` 是构造参数，永远盖得住环境变量——想用 `DATABASE_URL` 环境变量改库地址，
   必须选对应环境覆盖字典为空的 APP_ENV（如测试里临时库用 `development`）。

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
