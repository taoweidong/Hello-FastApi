# 前端开发指南

> 基于 vue-pure-admin v7 脚手架二次开发的约定与推荐路径。
> 核心原则：**新页面一律走 BaseApi + composables 体系**，不手写分页/搜索/对话框逻辑。

[← 返回文档导航](../README.md)

---

## 1. 目录与分层

```
src/api/base.ts          BaseApi<TList, TDetail, TPayload> 泛型基类
src/api/system/<m>.ts    模块 API（继承 BaseApi，声明类型）
src/composables/         useCrudTable / useDialogForm / useSwitchStatus / useDict
src/views/system/<m>/    页面：index.vue + utils/hook.tsx（或直接组合式）
src/utils/http/          axios：令牌附加、401 无感刷新、5xx/断网全局提示
```

## 2. 新增一个 API 模块

```ts
// src/api/system/gadget.ts
import { BaseApi } from "../base";
import type { Payload } from "../base";

export type Gadget = { id: string; name: string; isActive: number };

class GadgetApi extends BaseApi<Gadget, Gadget, Payload> {
  constructor() { super("/gadget"); }   // 对应后端路由前缀 /api/system/gadget
}
export const gadgetApi = new GadgetApi();
```

类型从后端 ResponseDTO 对齐（camelCase）；字段变更必须同步两端（AGENTS.md 协作规范第 5 条）。

## 3. 新增一个列表页（组合式写法）

参照 `views/system/config`（最精简样板）：

```ts
const crud = useCrudTable({ api: gadgetApi, searchForm: form, displayField: "name", entityName: "设备" });
// 得到 loading/dataList/pagination/onSearch/handleDelete/handleBatchDelete/分页事件
```

- 分页参数由 composable 自动携带（**勿在页面自拼 pageNum/pageSize**——历史上三页漏传致翻页失效）；
- 搜索表单空字符串会被 `pruneEmpty` 剔除；
- 删除/批量删除的"用户取消"与"请求失败"已区分处理。

## 4. 新增/编辑对话框

用 `useDialogForm` + `addDialog`（ReDialog 体系），表单组件放 `views/system/<m>/form.vue`；
提交按钮自带防重复；失败统一 message + 首错误字段定位。

## 5. 状态开关

```ts
const { switchLoadMap, onChange, createSwitchRenderer } = useSwitchStatus({
  api: gadgetApi as any, displayField: "name", entityName: "设备"
});
// 列定义：{ label: "状态", cellRenderer: createSwitchRenderer() }
```

自带确认弹窗、失败回滚、行级 loading。

## 6. 按钮权限

- 页面按钮：`v-auth="'gadget:add'"`（权限码来自菜单树 PERMISSION 节点，见[RBAC](../features/rbac.md)）；
- 后端接口必须有对应 `require_permission` 依赖——前端显隐只是体验，后端校验才是安全边界。

## 7. 动态路由与菜单

前端路由由后端下发（`/get-async-routes`），**不需要**在 `src/router/` 手写业务路由；
新页面上线步骤：后端菜单管理新增页面节点（component=`system/gadget/index`）→
角色勾选 → 用户重新登录。

## 8. 工具与约定

| 场景 | 用法 |
|---|---|
| 消息提示 | `import { message } from "@/utils/message"`（统一包装，勿直接用 ElMessage） |
| 字典下拉 | `useDict("dictName")`（模块级缓存；字典变更后需刷新页面） |
| 时间格式化 | `dayjs(x).format("YYYY-MM-DD HH:mm:ss")` |
| WebSocket 订阅 | `realtime.on("<type>", cb)` / 组件卸载 `realtime.off` |
| 树形数据 | `handleTree`（`@/utils/tree`） |

## 9. 测试

- 组件级单测：`src/**/__tests__/*.spec.ts`（vitest + happy-dom），参照
  `composables/__tests__/useCrudTable.spec.ts`；
- 页面交互：`e2e/crud-<m>.spec.ts`（Playwright，凭 storageState 登录，参照 crud-config）；
- 提交前：`pnpm lint && pnpm typecheck && pnpm test:unit`。
