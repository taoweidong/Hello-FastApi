---
name: fix-token-expired-force-logout
overview: 在前端HTTP响应拦截器中增加401/403状态码处理，当token失效时强制调用logOut()跳转登录页，避免页面持续加载
todos:
  - id: add-401-handler
    content: 在响应拦截器中添加401状态码处理，强制登出并跳转登录页
    status: pending
---

## 用户需求

检查前端代码，修复token失效后页面停留在当前页面一直加载的问题。当后端返回401（token失效/无效）时，前端需要强制登出并跳转到登录页面。

## 核心问题

`web/src/utils/http/index.ts` 的响应拦截器缺少对HTTP 401状态码的处理。后端token失效时返回401，前端仅做`Promise.reject`，不会触发登出，导致API请求失败后页面持续loading，用户停留在当前页面无法操作。

## 修复目标

- 响应拦截器检测到401状态码时，强制调用`logOut()`登出并跳转登录页
- 提示用户"登录已过期，请重新登录"
- 防止多个401并发时重复登出
- 登录/刷新token请求白名单，避免死循环

## 技术栈

- 前端框架: Vue3 + TypeScript
- HTTP库: Axios
- 状态管理: Pinia
- UI组件: Element Plus (ElMessage)
- 国际化: vue-i18n

## 实现方案

### 问题分析

1. **后端行为**: 当token无效/过期时，后端抛出`UnauthorizedError`，异常处理器返回HTTP 401，body为`{"code": 401, "message": "无效或已过期的令牌"}`
2. **前端现状**: 响应拦截器error回调（143-149行）仅做`Promise.reject`，完全不处理401
3. **现有登出逻辑**: `useUserStoreHook().logOut()`（95-103行）已正确实现清除token、重置路由、跳转/login
4. **现有提示**: 国际化key `login.pureLoginExpired` = "登录已过期，请重新登录"已存在

### 修改方案

在`web/src/utils/http/index.ts`的响应拦截器错误处理中：

1. 添加静态标志位`isLoggingOut`防止多个401并发时重复登出
2. 检查error.response.status是否为401
3. 排除白名单URL（`/login`、`/refresh-token`），避免登出流程自身触发401处理
4. 对401错误：设置标志位 → 提示消息 → 调用`logOut()` → 重置标志位
5. 非401错误保持原有`Promise.reject`逻辑

### 关键设计决策

- **使用类静态标志位而非`isRefreshing`**: `isRefreshing`用于token刷新流程，语义不同；新增`isLoggingOut`专门控制登出去重
- **白名单排除**: 登录和刷新token请求本身不应触发401登出，否则会造成循环
- **消息提示**: 复用已有的`login.pureLoginExpired`国际化key，与请求拦截器中token刷新失败的提示保持一致

### 目录结构

```
web/src/utils/http/
├── index.ts          # [MODIFY] 响应拦截器添加401处理逻辑
└── types.d.ts        # 无需修改
```

### 修改文件详情

**`web/src/utils/http/index.ts`** — 响应拦截器401处理

- 新增`private static isLoggingOut = false`标志位，防止并发401重复登出
- 在`httpInterceptorsResponse`的error回调中，提取`error.response?.status`
- 当status为401且请求URL不在白名单中时：
- 若`isLoggingOut`为true则直接reject（防止重复）
- 设置`isLoggingOut = true`
- 调用`message()`显示"登录已过期，请重新登录"
- 调用`useUserStoreHook().logOut()`强制登出跳转登录页
- 在finally中重置`isLoggingOut = false`
- 非401错误保持原有reject逻辑不变