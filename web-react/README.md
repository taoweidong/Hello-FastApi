# web-react — React 管理端（探索版）

> 与 Vue 版（`web/`）**共用同一套 FastAPI 后端与 API 契约**（`/api/system/*`），零后端改动。
> 首期落地：登录、令牌无感刷新、动态菜单/权限、用户管理完整 CRUD（作为 React 版参考实现）。

---

## 一、框架选型对比（2026-11，探索结论）

候选均为开源、高星标、高更新频率、可用于生产的管理端方案：

| 方案 | 生态规模 | 说明 | 结论 |
|---|---|---|---|
| **Ant Design 5 + @ant-design/pro-components**（本工程采用） | antd 为 React 生态最大的企业级组件库；ProComponents 是 Ant Design Pro 的官方组件层（ProLayout/ProTable），国内生产案例极多 | 组件全（表格/表单/布局/树/上传），中文文档完善；ProTable 自带查询表单与分页模型，与本后端"POST 分页列表"契约契合 | ✅ 采用 |
| Ant Design Pro（UmiJS Max 全家桶） | 同上生态 | 约定优先的元框架（非 Vite），路由/构建/插件全托管——对"同一后端契约的自定义封装（{code,message,data}、401 刷新）"侵入较大 | ❌ 只取其组件层（pro-components），不用 Umi |
| Refine | 近年快速增长的管理端框架 | dataProvider 抽象统一 CRUD；与本后端自定义契约（POST 列表 + 包裹响应）需要自定义 provider，且 UI 层仍需 antd | 备选，未采用（多一层抽象收益有限） |
| react-admin（marmelab） | 老牌管理端框架 | 默认 Material-UI 风格，与团队 antd 经验不符 | 未采用 |
| Next.js / Remix | 顶级热度 | SSR/全栈框架，与"内网管理端 + 独立 FastAPI"场景不匹配 | 未采用 |

基础栈：**Vite 6 + React 18.3 + TypeScript（strict）+ React Router 6 + TanStack Query 5 + Zustand 5 + Axios**。
（React 18 而非 19：antd v5 对 React 19 需要 patch 包，生产保守选择 18。）

## 二、运行

```bash
cd web-react
pnpm install
pnpm dev        # http://localhost:5173（/api 代理到 127.0.0.1:8000，同 Vue 版）
pnpm build      # 生产构建（tsc --noEmit + vite build）
pnpm typecheck
```

> pnpm v12 构建脚本审批：若报 `ERR_PNPM_IGNORED_BUILDS`，执行
> `pnpm install --dangerously-allow-all-builds` 一次即可（或全局配置 esbuild 允许构建）。

登录账号与 Vue 版相同（`admin` / `admin123`），后端先启动。

## 三、已实现范围

| 功能 | 说明 | 对应 Vue 版 |
|---|---|---|
| 登录 / 登出 | 令牌持久化（localStorage）、401 无感刷新（单飞 + 请求队列）、登出吊销 | `store/modules/user.ts` |
| 动态菜单 | `/get-async-routes` 下发菜单树 → ProLayout 侧边栏（图标关键词映射 antd 图标） | `layout/` |
| 权限码 | 登录响应 `permissions` 数组 + `hasAuth(code)` 控制按钮显隐；后端二次校验 | `v-auth` 指令 |
| 用户管理 | ProTable 分页/搜索、新增/编辑（部门 TreeSelect/岗位/角色分配）、状态开关、删除/批量删除 | `views/system/user` |
| 服务器状态 | 首页复用 `/server-info`（CPU/内存/磁盘/系统信息） | `monitor/server` |

未迁移页面（菜单可见，点击显示"建设中"占位）：角色/菜单/部门/字典/公告/监控等——
迁移模式与用户管理页一致，按需推进。

## 四、二次开发模式

新增一个 CRUD 页面（React 版）：

1. `src/api/<m>.ts`：类型对齐后端 DTO（camelCase）+ 请求函数（`request` 已解包 `{code,message,data}` 并统一错误提示）；
2. `src/pages/...`：ProTable `request` 属性映射后端分页；表单用 antd Form/Modal；
3. 权限：`hasAuth(permissions, '<m>:add')` 控制按钮，后端 `require_permission` 校验；
4. 菜单：后端菜单管理页配置 path（React 按 path 渲染），无需改前端路由代码。

## 五、与 Vue 版（web/）的关系

- **后端唯一**：同一套 FastAPI 服务、同一数据库、同一菜单/权限种子；
- **契约唯一**：`{code,message,data}` 封装、POST 分页、camelCase DTO 两端一致；
- Vue 版仍是功能完整的主前端；React 版为框架探索与渐进迁移载体，
  未迁移页面在 React 端显示占位，不影响双端并行运行。
