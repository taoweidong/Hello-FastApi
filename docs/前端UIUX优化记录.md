# 前端 UI/UX 全量优化记录

> 日期：2026-10-20 | 依据 skill：`ui-ux-pro-max`
> 范围：`web/` 布局、流畅度、交互反馈、可达性基线
> 原则：**只改全局层与体验层，不动业务逻辑与后端契约**

---

## 1. 优化前现状（实测基线）

| 维度 | 基线 | 问题 |
|---|---|---|
| 加载反馈 | 4 个 hook 用 `setTimeout(300~500ms)` 假延迟 | 数据已返回仍转圈 0.5s，纯浪费用户时间 |
| 提交防重 | ReDialog 已有 `sureBtnLoading` 机制，**全项目 0 处使用** | 表单可连点重复提交 |
| 焦点可及 | `reset.scss` 有 `div:focus { outline: none }` | 键盘导航完全无焦点环（高危可及性问题） |
| 减弱动效 | `prefers-reduced-motion` 0 处 | 前庭敏感用户无降级通道 |
| 动效时长 | 路由切换 `transition: all 0.5s` | 偏慢 + `all` 触发全属性重绘 |
| 空态 | 17 个表格页仅 1 处 empty slot，默认 `el-table__empty-block` 无留白 | 空数据呈现为死胡同 |
| 刷新按钮 | `onReFresh` 无防抖，连点发 N 次请求 | 请求风暴 |
| 表单语义 | 登录页输入框无 `autocomplete` | 浏览器/密码管理器无法正确填充 |
| 调试残留 | 3 处 `console.log("handleSelectionChange")` + 2 处分页日志 | 控制台噪音 |

---

## 2. 已落地改动

### 2.1 流畅度（直接可感知）

| 文件 | 改动 | 收益 |
|---|---|---|
| `views/system/user/utils/hook.tsx` | `setTimeout(500)` → `try/finally` 真实 loading，补分页回写 | 列表响应提速约 500ms |
| `views/system/dept/utils/hook.tsx` | 同上 | 同上 |
| `views/system/menu/utils/hook.tsx` | 同上 | 同上 |
| `views/system/dictionary/utils/hook.tsx` | `setTimeout(300)` → `try/finally`，双 loading 一并收口 | 树 + 表格同步收敛 |
| `style/transition.scss` | 路由切换 `all 0.5s` → `opacity/transform 0.25s` | 切换更快且只走合成层 |
| `style/element-plus.scss` | 表格空态 `min-height: 160px` + 次级文字色 | 空态不再是死胡同 |
| `components/RePureTableBar/src/bar.tsx` | 刷新按钮防抖（loading 期间拦截 + 定时器） + `onUnmounted` 清理 | 防请求风暴、防内存泄漏 |

### 2.2 交互反馈

| 文件 | 改动 |
|---|---|
| `composables/useDialogForm.ts` | 接入 `sureBtnLoading: true`，提交期间确认按钮 loading；失败分支 `closeLoading()`；验证失败滚动到首个错误字段 |
| `views/login/index.vue` | 账号/密码补 `autocomplete="username"` / `"current-password"` + `name`，支持浏览器凭据自动填充 |
| `composables/useDialogForm.ts` | 成功/失败/非 0 code 分支全部补 `closeLoading`，避免按钮永久转圈 |

### 2.3 可达性基线（全局一次生效）

| 文件 | 改动 | 对应准则 |
|---|---|---|
| `style/index.scss` | `:focus-visible` 全局焦点环（2px primary + 2px offset） | WCAG 2.4.7 Focus Visible |
| `style/index.scss` | `@media (prefers-reduced-motion: reduce)` 全局关闭动画/过渡 | WCAG 2.3.3 Animation from Interactions |
| `style/index.scss` | `html { scroll-behavior: smooth }` | 平滑锚点滚动 |
| `style/index.scss` | `.el-table__row` 限定 `background-color/color` 过渡 | 避免 `transition: all` 重绘放大 |
| `style/index.scss` | 弹窗/抽屉 body `content-visibility: auto` | 长内容首屏渲染优化 |
| `style/reset.scss` | `div:focus` → `div:focus:not(:focus-visible)` | 恢复键盘焦点，鼠标点击仍不显示 |

### 2.4 代码卫生

- 清理业务代码全部 `console.log` 残留（6 处，第三方 `iconfont.js` 不动）：
  - `handleSelectionChange` 3 处（dept / menu / dictionary）
  - user hook 的 `handleUpdate` / 分页回调 3 处
  - `welcome/components/table/columns.tsx` 分页回调
  - `account-settings` 的 Profile / Preferences 各 1 处
- 顺手修掉两个**潜在运行时错误**：dept / menu 的 `handleSelectionChange` 引用了未定义变量 `selectedNum`，选中表格行时会抛 `ReferenceError` → 改为 `selectedRows` ref 暂存
- `handleUpdate`（user 页下拉菜单占位回调，实际入口是 `handleUpload`）改为带注释的空实现
- 未使用参数统一加 `_` 前缀，满足 `no-unused-vars` 规则

> 注：`welcome/components/table/columns.tsx` 的 `delay(300)` 是演示页 mock 加载动画（无真实请求），与本次清理的"假延迟"性质不同，保留。

### 2.5 防御性加固（全量测试中发现）

| 文件 | 改动 |
|---|---|
| `views/monitor/logs/login/hook.tsx` | `onSearch` 改 `try/finally`，接口异常时不再卡死 loading |
| `views/monitor/logs/operation/hook.tsx` | 同上 |
| `views/monitor/logs/system/hook.tsx` | 同上 |
| `views/monitor/online/hook.tsx` | 同上 |

> 触发原因：后端 `login-logs` 接口 500（dev.db schema drift）时，这 4 个 hook 的按钮会永久转圈。属「后端故障被放大成前端假死」，与本次 UI 优化同属"流畅度"范畴。

---

## 3. 验证结果

全量测试（2026-10-21，Redis 就绪、dev.db schema 修复后）：

| 项 | 结果 |
|---|---|
| 后端 pytest（unit + integration） | **2171 passed**（237.93s，基线 2166 +5） |
| `pnpm typecheck`（vue-tsc） | 通过 |
| `pnpm lint`（eslint + prettier + stylelint） | 通过 |
| `pnpm build` | 成功（57s） |
| E2E（Playwright，串行） | **51/51 通过**（10.7m） |

### 全量测试中挖出并修复的两个真实缺陷

**缺陷 1：后端 `sys_userloginlog` 表缺 `username` 列 → 登录日志接口 500**

- 现象：E2E「登录日志按状态筛选」连续两次失败，搜索按钮永久卡在 `disabled` + `is-loading`。
- 根因（本地复现拿堆栈）：
  ```
  sqlalchemy.exc.OperationalError: no such column: sys_userloginlog.username
  ```
  dev.db 的 `alembic_version` **已被打到 head（`c4d5e6f7a8b9`）但该迁移的 DDL 从未真正执行**——「版本戳超前、结构落后」。而 lifespan 走 `init_db()`（`create_all`），**只建缺失的表、不会给已存在表加列**，所以模型新增的 `username` 列一直没落到 dev.db。这正是方案文档 **B5（高危）** 的实证。
- 为什么测试没发现：pytest 用 `.env.testing` 独立库，每用例 `create_all/drop_all`，schema 永远最新；只有走 dev.db 的 E2E 会暴露。
- 修复（本地数据修复，非代码改动）：
  ```bash
  cp sql/dev.db sql/dev.db.bak-<ts>        # 先备份
  alembic downgrade a3b5c7d9e1f2           # 回退版本戳（迁移本身幂等）
  alembic upgrade head                     # 重新执行，补齐 username 列
  ```
- 根治建议（属方案文档 B5 批次，未在本次自动实施）：lifespan 改 `alembic upgrade head`，消除「版本戳与结构不一致」的空间。

**缺陷 2：前端 4 个 monitor hook 的 `onSearch` 无 `try/finally`，后端一报错 UI 永久转圈**

- 现象：接口 500 时 axios 走 reject，`await` 之后的 `loading.value = false` 被跳过 → 搜索按钮永久 disabled。这是「后端故障被放大成前端假死」的典型链路。
- 修复：`monitor/logs/{login,operation,system}/hook.tsx`、`monitor/online/hook.tsx` 的 `onSearch` 统一改 `try/finally`，与第 2.1 节已修的 4 个 hook 保持一致。
- 顺带修掉一个自己引入的回归：清理 `console.log` 时把 `Profile.vue` 的 else 分支写成 `return false`，导致回调返回 `Promise<boolean>`，与 Element Plus 的 `FormValidateCallback`（`void | Promise<void>`）不兼容，typecheck 报 TS2345。已改回无返回值。

---

## 4. 刻意未做的部分（及原因）

| 项 | 原因 |
|---|---|
| 开启 tsconfig `strict` | 会一次性暴露数百错误，需独立批次三步走，不属于 UI/UX 范畴 |
| vendor 分包 / 删 9.7MB 僵尸资源 | 属构建优化批次（方案文档 F3），改动面大需单独验证 |
| 引入 vitest | 属测试基建批次（方案文档 F4） |
| 清理 admin123 默认填充 | 属安全批次（方案文档 F5），影响 E2E 登录流程，需配套改测试 |

以上均已记录在 `docs/最佳实践优化方案.md` 的对应批次中。
