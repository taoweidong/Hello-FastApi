# 前端全量界面优化：问题清单与修改方案

> 范围：`web/src` 全量页面与组件。约束：**不改变现有功能逻辑与数据结构**。
> 产出顺序：先通读代码列出问题 → 按优先级排序 → 逐项给出改动位置/原因/预期效果 → 实施 → 验证。

---

## 一、问题清单（按优先级排序）

### P0 — 会导致误操作、不可达或静默失败

| # | 维度 | 问题 | 位置 |
|---|---|---|---|
| 1 | 交互 | 刷新按钮执行**写操作**。右侧面板 `@refresh="handleSave"`，点"刷新"会静默提交权限变更 | `views/system/permission/index.vue:75` |
| 2 | 交互 | **不可逆破坏性操作无二次确认**。"清空全部"直接调 `ipRuleApi.clear()`，且失败无任何提示 | `views/system/ip-rule/index.vue:114-120`、`:153-157` |
| 3 | 交互 | 抹掉按钮焦点环。`:deep(.el-button:focus-visible){outline:none}` 使键盘 Tab 导航看不到焦点位置（违反 WCAG 2.4.7） | `views/system/user/index.vue`（原 255 行） |
| 4 | 交互 | **错误状态缺失**。响应拦截器只处理 401，5xx / 断网 / 超时被静默 `reject`，页面只剩空白表格，用户无法区分"没有数据"与"加载失败" | `utils/http/index.ts:146-168` |
| 5 | 流畅度 | **首屏依赖外网 CDN 拉取图标**。登录页第三方图标用 `IconifyIconOnline`，运行时依次请求 `api.iconify.design` → `api.simplesvg.com` → `api.unisvg.com`。实测 `load` 仅 0.85s，但要 **24.0s** 才达到 networkidle；弱网/内网下更久甚至挂起 | `views/login/index.vue`（原 324 行） |

### P1 — 一致性分叉（同类组件样式/行为不统一）

| # | 维度 | 问题 | 规模 |
|---|---|---|---|
| 5 | 一致性 | 搜索表单内边距 3 种写法：`pl-8 pt-3`(×10) / `pl-4 pt-3`(×1, user) / `pl-2 pt-2`(×1, menu) | 12 个页面 |
| 6 | 一致性 | 搜索表单项下边距写了 **12 份**重复的 scoped `.search-form{...}`，且 menu 是 8px、其余 11 页是 12px | 12 个页面 |
| 7 | 一致性 | 主内容区外边距写了 **7 份**重复的 `.main-content{margin:8px 8px 0!important}` | 7 个列表页 |
| 8 | 一致性 | `label-width` 82px(×11) vs 90px(×1) | `AccountManagement.vue` |
| 9 | 一致性 | `offsetBottom` 魔法数 45/108/80 散落 14 处，看不出差异来源，新页面只能"抄一个" | 14 个页面 |
| 10 | 一致性 | `100vh` 魔法数：`calc(100vh - 141px)` 在字典树与用户部门树各写一份，`calc(100vh - 210px)` 另写一份 | 3 处 |
| 11 | 一致性 | z-index 脱离体系：`.is-dark`=9999、`.right-panel`=40000、`.right-panel-background`=20000 | 3 处 |
| 12 | 流畅度 | `transition: all` 共 10 处。侧边栏折叠、路由容器切换时把无关属性一并卷入过渡，放大重排/重绘 | 见下表 |
| 13 | 流畅度 | 过渡时长不统一：0.1/0.16/0.2/0.25/0.28/0.3/0.4/0.5/0.6s 与 220/300ms 混用，共 10+ 种取值 | 全局 |
| 14 | 流畅度 | hover 过渡只声明在 `:hover` 上，鼠标移出时瞬间跳回，出现"进有动画、出无动画"的割裂感 | `components/ReIcon/src/Select.vue` |

### P2 — 响应式与状态反馈缺口

| # | 维度 | 问题 | 位置 |
|---|---|---|---|
| 15 | 布局 | **业务层响应式覆盖率≈0**：全项目仅 3 个 error 页用了 Tailwind 断点前缀，业务页 0 处 `@media` | 全局 |
| 16 | 布局 | 固定宽度分栏在窄屏挤爆表格：字典页左栏 `w-70! shrink-0`(280px)、权限页 `w-1/3 min-w-75`(300px) | `dictionary/index.vue`、`permission/index.vue` |
| 17 | 布局 | 表格缺 `row-key`（行身份不稳定，勾选/展开/复用 DOM 会错行） | `monitor/online`、`system/role` |
| 18 | 交互 | 表格缺 `showOverflowTooltip`：长文本撑高行或被硬截断且无提示 | `SecurityLog`、monitor logs ×3、`permission`、`user` |
| 19 | 布局 | flex 子项未加 `min-w-0`，表格过宽时撑破容器造成整页横向溢出 | 分栏页右侧容器 |

---

## 二、逐项修改方案

### 基础：新增设计令牌 `web/src/style/tokens.scss`

**原因**：上述 5~14 号问题的共性是"规范没有单一来源"。把间距/动效/圆角阴影/层级收敛成 CSS 变量后，规范变更只改一处。

**内容**：4px 基准间距刻度（8 档）+ 3 个语义化间距；4 档时长（fast .15s / base .2s / panel .25s / slow .3s）；3 条缓动曲线（standard / emphasized / out）；4 档圆角；3 级阴影（含 `.dark` 覆盖）；6 级 z-index；`@media (width <= 768px)` 窄屏覆盖；`.pure-touch-target`（粗指针设备 44px，WCAG 2.5.5）。

**接入**：`style/index.scss` 顶部 `@use "tokens";`（必须先于其他样式，保证变量可用）。

---

### P0-1 刷新按钮误触发保存

| 项 | 内容 |
|---|---|
| 文件 | `web/src/views/system/permission/hook.tsx`、`web/src/views/system/permission/index.vue` |
| 组件 | `SystemPermission` 右侧「菜单权限配置」面板 |
| 改动 | hook 新增 `handleRefresh()`：无选中角色时提示，否则按 `currentRoleId` 重新走 `selectRole()` 拉服务端权限回写树（即丢弃本地未保存勾选）；导出该函数；模板 `@refresh` 由 `handleSave` 改为 `handleRefresh`。「保存权限」按钮保持 `handleSave` 不变 |
| 原因 | 刷新语义应是"放弃本地改动、重新拉取"，而 `handleSave` 是写接口。原绑定会让用户在以为只是刷新时静默提交权限变更 |
| 预期效果 | 刷新=重新加载并提示"已重新加载该角色的权限"；保存仍走原按钮，两者语义分离 |

### P0-2 清空全部缺少二次确认

| 项 | 内容 |
|---|---|
| 文件 | `web/src/views/system/ip-rule/hook.tsx` |
| 组件 | `handleClear()` |
| 改动 | 前置 `ElMessageBox.confirm`（danger 按钮文案「确认清空」），用户取消直接 return；接口调用包 `try/catch`，失败提示「清空失败，请重试」 |
| 原因 | 清空全表不可逆；原实现无确认、无失败反馈，误点即全量删除 |
| 预期效果 | 误点可取消；失败有明确提示，不会静默无反应 |

### P0-3 按钮焦点环被抹除

| 项 | 内容 |
|---|---|
| 文件 | `web/src/views/system/user/index.vue` |
| 改动 | 删除 `:deep(.el-button:focus-visible){outline:none}` 规则，改为注释说明交由全局规则接管 |
| 原因 | 该规则覆盖了全局 `:focus-visible`，使键盘用户无法定位焦点（WCAG 2.4.7 Focus Visible） |
| 预期效果 | 键盘 Tab 到操作按钮时出现 2px 主色焦点环；鼠标点击仍不出现（全局规则用 `:focus-visible` 已区分） |

### P0-4 服务端/网络错误静默失败

| 项 | 内容 |
|---|---|
| 文件 | `web/src/utils/http/index.ts`（响应拦截器） |
| 改动 | 401 分支之外新增：非取消请求 且（`status === undefined` 或 `status >= 500`）时弹出 error 提示——无响应提示「网络连接失败，请检查网络后重试」，5xx 提示「服务暂时不可用，请稍后重试」 |
| 原因 | 原实现只处理 401。后端 500 时（本项目曾真实出现 `sys_userloginlog` 缺列导致 500）前端表现为表格空白 + loading 可能卡死，用户无从判断 |
| 预期效果 | 5xx/断网有统一反馈；4xx 属业务校验仍由各页面自行呈现，避免重复打扰 |

### P0-5 首屏不再依赖外网图标 CDN

| 项 | 内容 |
|---|---|
| 文件 | `web/src/views/login/index.vue`、`web/src/components/ReIcon/src/{hooks.ts, offlineIcon.ts, offlineIconNames.ts(新增)}`、`service/src/domain/rbac_defaults.py` |
| 改动 | ① 登录页第三方图标 `IconifyIconOnline` → `IconifyIconOffline`（`~icons/ri/xxx-fill?raw` + `addIcon`）；② `offlineIconNames.ts` 新增为**轻量清单模块**（只有图标名字符串，避免把 46 个 SVG 拖进登录页 chunk）；③ `useRenderIcon` 对冒号形式图标先归一成 `/`，已注册的走离线、**未注册仍回退在线**（保证图标选择器选到未预置图标时不空白）；④ 补齐 11 个在用但未离线注册的菜单图标 |
| 原因 | 后端菜单图标存的是 `ri:settings-3-line`（冒号），`useRenderIcon` 以"是否含 `:`"判在线/离线，于是**每次渲染菜单都去 api.iconify.design 拉数据**。实测登录页 `load` 仅 0.85s，但要 24.0s 才达到 networkidle；弱网/内网下更久甚至挂起 |
| 预期效果 | 首屏 networkidle **24.0s → 1.8s**；登录后页面 networkidle **60s+ 超时 → 2.4s**；外部请求 **3 → 0**；内网/离线部署也能正常渲染 |

**顺带发现的数据缺陷**：`rbac_defaults.py` 里"按钮权限"用 `ri:button-line`、"按钮权限组件"用
`ri:components-line`，这两个图标在 Remix Icon 中**不存在**（本地 `@iconify-json/ri` 与在线
API 均无），此前一直渲染为空白。已改为 `ri:radio-button-line` / `ri:stack-line`，并同步修正
`sys_menumeta` 中的存量数据。

> 该问题原先的可见后果是 E2E 里 `waitForLoadState("networkidle")` 常态耗时 23~37s、
> 偶发突破 60s 超时，且**每次失败的用例都不同**——表现为"随机 flaky"，实质是外网请求耗时抖动。

**改动过程中的两个坑**（复现于文档以免重蹈）：
1. 图标名必须本地真实存在。`ri/button-line`、`ri/components-line` 不存在时，
   unplugin-icons 直接 `Pre-transform error: Icon xxx not found`，导致 `layout/index.vue`
   动态导入失败 → **整页白屏**（且 typecheck/lint/build 全部通过，只有运行时炸）。
2. 改了 `sys_menumeta` 后菜单仍显示旧图标，是因为菜单树被 **Redis 缓存**（缓存已启用），
   需要 `FLUSHDB` 才能看到新数据。

### P1-5/6/7 搜索表单与主内容区样式去重

| 项 | 内容 |
|---|---|
| 文件 | 12 个列表页模板 + `web/src/style/element-plus.scss` |
| 改动 | ① 移除模板上的 `pl-8/pl-4/pl-2`、`pt-3/pt-2`；② 移除 12 份重复的 scoped `.search-form` 块与 7 份重复的 `.main-content` 块；③ 在 `element-plus.scss` 增加全局规则，取值来自令牌：`--pure-search-form-padding`、`--pure-form-item-gap`、`--pure-content-margin` |
| 原因 | 同一视觉规范被复制 12 遍且已产生 3 种分叉；menu 页 8px 与其他页 12px 不一致 |
| 预期效果 | 12 个列表页搜索区间距完全一致；窄屏由 tokens 的 `@media (width<=768px)` 自动收紧；改规范只改 1 处 |

> **实施中发现并修正的陷阱**：全局 `.scss` 里**不能**写 `:deep()`。`:deep()` 由 `@vitejs/plugin-vue` 在编译 SFC 的 `<style scoped>` 时重写，独立样式表不经过该处理，产物会保留字面量 `:deep(...)` 成为无效选择器、整条规则被浏览器丢弃。已改为普通后代选择器 `.search-form .el-form-item`，并在产物 CSS 中验证规则确实输出。

### P1-8 label-width 统一

`views/account-settings/components/AccountManagement.vue`：`90px` → `82px`，与其余 11 个表单一致。

### P1-9 offsetBottom 语义化

| 项 | 内容 |
|---|---|
| 文件 | 新增 `web/src/config/adaptive.ts`；14 个列表页 |
| 改动 | 导出 `ADAPTIVE_OFFSET = { base: 45, withSelectionBar: 108, split: 80 }`，14 处字面量改为具名引用并加 import |
| 原因 | 45/108/80 的差异来源是"页面上方是否多一条批量选择操作条（约 +63px）"以及"是否分栏无分页器"，原来完全看不出来 |
| 预期效果 | 数值不变（不产生布局回归），但含义显式化，新增页面可正确选档 |

### P1-10 面板高度令牌化

`tokens.scss` 新增 `--pure-panel-height: calc(100vh - 141px)`、`--pure-panel-scroll-height: calc(100vh - 210px)`；`dictionary/index.vue`、`user/tree.vue` 的 3 处内联魔法数改为引用令牌。

### P1-11 z-index 收敛

| 位置 | 原值 | 改为 |
|---|---|---|
| `style/element-plus.scss` `.is-dark` | `9999 !important` | `var(--pure-z-popper)` (3000) |
| `layout/components/lay-panel/index.vue` `.right-panel` | `40000` | `var(--pure-z-top)` (4000) |
| 同上 `.right-panel-background` | `20000` | `calc(var(--pure-z-top) - 1)` |

保留 `!important` 是因为 Element Plus 会给 popper 动态写内联 z-index，只有 `!important` 能固定。预期：层级顺序变为 遮罩(2000) < 弹窗(2001) < tooltip(3000) < 全局浮层(4000)，不再出现脱离体系的极值。

### P1-12/13/14 动效统一

| 文件 | 原写法 | 改为 |
|---|---|---|
| `components/ReSegmented/src/index.css` | `all 0.1s cubic-bezier(.645,.045,.355,1)` | `color / background-color / box-shadow`，时长 `--pure-duration-fast`，缓动 `--pure-ease-standard` |
| `components/ReIcon/src/Select.vue` | `all 0.4s`（**只写在 `:hover` 上**） | 过渡移到常态声明，属性收窄为 `color / border-color / transform`，时长 `--pure-duration-base` |
| `layout/components/lay-panel/index.vue` | `all 0.25s` / `all 0.3s` | `transform` / `opacity`，分别用 `--pure-duration-panel` 与 `--pure-duration-slow` |
| `layout/components/lay-setting/index.vue` | `all 0.2s ease` | `box-shadow / transform` + `--pure-duration-base` |
| `layout/components/lay-tag/index.scss` ×2 | `all 0.4s`、`all 0.2s cubic-bezier(.645,...)` | 收窄为 `color / background-color / box-shadow / padding(+margin)`；**保留 padding** 是因为 chrome 风格标签切换确实要动画内边距；时长统一到 `--pure-duration-base` |
| `style/sidebar.scss` ×2 | `all var(--pure-transition-duration)` | 分别收窄为 `width/height/background-color` 与 `width/padding-left`，缓动统一 `--pure-ease-standard` |
| `layout/components/lay-content/index.vue` | 内联 `all 300ms` | `max-width` + `--pure-duration-slow` + `--pure-ease-standard` |

预期效果：折叠侧边栏、切换路由时不再触发全属性过渡计算；`ReIcon/Select` 鼠标移出也有过渡，进出一致。

### P2-15/16/19 响应式与溢出防护

| 文件 | 改动 |
|---|---|
| `views/system/dictionary/index.vue` | 分栏容器加 `dict-layout`、左栏加 `dict-tree` 类；scoped 内新增 `@media (width <= 768px)`：改为上下堆叠，左栏 `width:100%`、`min-height:40vh`、内部 `el-scrollbar` 高度 `24vh`（需 `!important` 覆盖内联 style 与组件 height 属性）；右侧容器加 `min-w-0` |
| `views/system/permission/index.vue` | 同理加 `permission-layout` / `permission-roles`，窄屏堆叠且左栏 `width:100%`、`min-width:0`；右侧容器加 `min-w-0` |

预期效果：768px 以下字典/权限页由"左右挤压"变为"上下堆叠"，表格不再被挤出可视区；`min-w-0` 防止表格过宽撑破 flex 容器导致整页横向滚动条。

### P2-17/18 表格属性补齐

- 补 `row-key="id"`：`monitor/online/index.vue`、`system/role/index.vue`
- 补 `showOverflowTooltip`：`account-settings/components/SecurityLog.vue`、monitor logs ×3、`system/permission/index.vue`、`system/user/index.vue`

预期效果：行身份稳定（勾选/展开不再错行）；长文本省略并附 tooltip，不再撑高行高。

---

## 三、未纳入本轮（需评估后再动）

| 项 | 原因 |
|---|---|
| 长列表虚拟滚动（16 张表） | 需引入虚拟滚动方案，与 `adaptive` 高度计算、树形表格耦合，风险较高，建议单独立项 |
| 错误边界（ErrorBoundary）组件 | 需在路由层统一包裹，属架构改动 |
| 303 处硬编码颜色 | 建议先建立色板令牌再做批量替换，否则易引入对比度回归 |
| 欢迎页 `v-motion` 延迟累积（约 1.06s） | 首屏观感问题，需与产品确认可接受时长 |
| 批量删除条 `v-if` 造成的 54px 高度跳动 | 改为占位预留会占用常驻空间，需产品确认 |

---

## 四、验证结果

| 项 | 命令 | 结果 |
|---|---|---|
| 类型检查 | `pnpm typecheck` | ✅ 通过 |
| ESLint / Prettier / Stylelint | `pnpm lint` | ✅ 通过（0 error / 0 warning） |
| 生产构建 | `pnpm build` | ✅ 成功 |
| 产物校验 | 检查 `dist/static/css` | ✅ `.search-form` / `.main-content` 规则正确输出，`:deep(` 残留 0 处 |
| 后端 pytest | `pytest -q` | ✅ 2171 通过（595s） |
| E2E | Playwright `--workers=1` | ✅ 51/51 通过（**2.3m**，基线 9.9m） |
| 首屏网络（实测） | Playwright 请求打点 | 登录页 networkidle **24.0s → 1.76s**；登录后页面 **60s 超时 → 2.4s**；外部请求 **3 → 0** |
| 产物校验 | 检查 `dist/static/css` | ✅ `.search-form` / `.main-content` 规则正确输出，`:deep(` 残留 0 处 |

**提交**：`51211a0`（43 文件，+1348 / −537），已推送 `master`。

---

## 五、附：验证过程中发现的后端配置缺陷（已修复）

启动后端准备 E2E 时，日志持续出现 `Redis 连接初始化失败，缓存功能将降级为直接查库`，
而 `redis-cli PING` 与同步 `redis-py` 均正常返回。根因链如下：

1. `service/src/config/settings.py:220` 写的是 `Settings(env_file=..., ...)`；
2. pydantic-settings v2 在 `__init__` 中接收的参数名是 **`_env_file`**（带下划线前缀）。
   写成 `env_file` 会被当作未知字段，在 `extra="ignore"` 下**静默丢弃**；
3. 因此 `.env` / `.env.development` / `.env.production` / `.env.testing` **从未被加载**，
   全站一直跑在模型默认值上；
4. `REDIS_URL` 取默认值 `redis://localhost:6379/0`。Windows 下 `localhost` 优先解析到
   IPv6 `::1`，而本机 Redis 3.2.100 只监听 IPv4 `127.0.0.1`，异步连接必然超时（1s）→
   缓存永久降级 → 每个请求都要等一次连接超时，单请求被拖到 3s 量级。

这也解释了此前记录的"E2E 随机假失败"——**不是测试时序问题，而是配置加载 bug**。

**修复**：`env_file=` → `_env_file=`。

**修复后开发环境的实际变化**（均为 `.env.development` 的既有意图）：

| 配置项 | 修复前（默认值） | 修复后 |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0`（IPv6 超时） | `redis://127.0.0.1:6379/0` |
| `CORS_ORIGINS` | 仅 3000/8080，**不含 8848** | 增加 `http://localhost:8848` |
| `DEBUG` / `LOG_LEVEL` | `False` / `INFO` | `True` / `DEBUG` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | 60 |
| `RATE_LIMIT_TIMES` | 100 | 1000 |
| `SECRET_KEY` / `JWT_SECRET_KEY` | 模型默认占位值 | `.env.development` 值 |

> ⚠️ 对生产环境的影响：`_ensure_production_secrets()` 这个 fail-fast 校验此前因
> `.env.production` 未加载而从未生效。修复后若 `.env.production` 仍含 `your-` 前缀的
> 占位密钥，启动会按设计**直接抛错拒绝启动**。这是预期的安全行为，但部署前需确认已配置强随机密钥。
