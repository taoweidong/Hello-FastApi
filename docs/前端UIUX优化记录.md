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

---

## 3. 验证结果

| 项 | 结果 |
|---|---|
| `pnpm typecheck`（vue-tsc） | 通过 |
| `pnpm lint`（eslint + prettier + stylelint） | 通过 |
| `pnpm build` | 成功 |
| E2E（Playwright，串行 51 用例） | 50/51；失败用例单独复跑通过 |

### E2E flaky 根因（重要，非代码回归）

三轮全量跑**失败用例均不同**（第 1 轮：login 空密码 + monitor 在线用户；第 2 轮基线 A/B：smoke-monitor 5/5 全过；第 3 轮：smoke post），且每个失败用例**单独复跑均通过**。

后端日志定位到根因：

```
WARNING  Redis 读取缓存失败: menu:all
INFO     POST /api/system/login | 200 | 3250.79ms   ← 单请求 3.2 秒
```

**Redis 服务在 E2E 启动初期未就绪**，后端全程走降级路径，且每次缓存操作都要等一次连接超时，导致单请求 3.2 秒级延迟。E2E 的 `waitForLoadState("networkidle")` 与 10 秒表格断言均为临界值，慢一点就超时——表现为随机用例失败。

处置：确认 Redis 健康后重启后端，失败用例单独复跑即通过。**与本次 UI 改动无关**（已用 `git stash` 做 A/B 对照验证）。

---

## 4. 刻意未做的部分（及原因）

| 项 | 原因 |
|---|---|
| 开启 tsconfig `strict` | 会一次性暴露数百错误，需独立批次三步走，不属于 UI/UX 范畴 |
| vendor 分包 / 删 9.7MB 僵尸资源 | 属构建优化批次（方案文档 F3），改动面大需单独验证 |
| 引入 vitest | 属测试基建批次（方案文档 F4） |
| 清理 admin123 默认填充 | 属安全批次（方案文档 F5），影响 E2E 登录流程，需配套改测试 |

以上均已记录在 `docs/最佳实践优化方案.md` 的对应批次中。
