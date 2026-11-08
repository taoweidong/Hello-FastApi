# 设计架构

> 后端 DDD 四层 + 前端工程分层。二次开发前必读：依赖方向、事务约定、
> 组合根规则是本仓库的三条硬约束。

[← 返回文档导航](../README.md)

---

## 1. 后端：DDD 四层（`service/src/`）

```
api/            43 文件  路由层：Routable 路由 + dependencies 组合根 + 统一响应
application/    34 文件  用例层：Service（事务边界）+ DTO + mapper/utils
domain/         36 文件  领域层：实体 / 仓储接口(ABC) / 服务端口(ABC) / 领域服务
infrastructure/ 58 文件  基础设施：SQLModel 仓储实现 / Redis / HTTP 中间件 / 日志
config/          3 文件  多环境 Settings
```

### 1.1 依赖方向（硬约束，CI 可验证）

- `domain` 不 import application/infrastructure/api —— **零违规**（当前实测）；
- `application` 不 import infrastructure —— 依赖倒置经端口实现；
- `api/dependencies/` 是**唯一的组合根**：只有这里允许实例化仓储与端口适配器。

### 1.2 端口-适配器（按消费方拆窄端口）

| 端口 | 消费方 | 实现 |
|---|---|---|
| `TokenRevocationPort` / `UserCachePort` / `MenuCachePort` / `DictCachePort` | 各自的服务 | `CacheService` |
| `CacheAdminPort` | MonitorService（缓存清单/清理） | `CacheService` |
| `OnlineSessionStore` | MonitorService / 登录登记 | `RedisOnlineSessionStore` |
| `RealtimePort` | NoticeService（WS 广播） | `WSManagerRealtimeAdapter` |
| `IPFilterPort` / `LoggingPort` | IP 规则服务 | 适配器 |

新增外部依赖（MQ、对象存储…）照此模式：domain 定义 ABC → infrastructure 实现 → dependencies 工厂注入。

### 1.3 事务约定（Unit of Work，见 `base.py` 模块注释）

- **请求级单事务**：`get_db` yield 后统一 commit / 异常统一 rollback；
- 同请求内**所有仓储共享同一 AsyncSession**——由组合根工厂统一 `Depends(get_db)`
  保证（c24e493 后由 `get_repositories(db) -> RepoBundle` 收敛）；
- **禁止**在服务工厂自建 AsyncSession；
- 观测类副作用（登录审计日志）是唯一例外：独立短会话立即提交（回滚不吞审计）。

### 1.4 请求生命周期

```
Request → LoginRateLimit(仅login/register) → SlowAPI 全局限流 → IPFilter → RequestLogging
        → Router(classy-fastapi) → 依赖链: JWT→黑名单→当前用户→权限码
        → Service（应用层，事务边界）→ Repository（共享 session）→ commit
异常   → AppError 体系（exceptions.py）→ 统一 JSON 响应（生产隐藏内部细节）
```

## 2. 前端分层（`web/src/`）

```
api/base.ts           BaseApi 泛型基类（list/retrieve/listTree/create/partialUpdate/destroy/batchDelete/updateStatus）
api/system/*          每模块一个 BaseApi 子类（userApi/roleApi/...）
composables/          useCrudTable（分页/搜索/删除）/ useDialogForm（对话框）/ useSwitchStatus（开关）/ useDict
store/modules/        Pinia：user（令牌/登出）等
router/               动态路由：登录后由 /get-async-routes 下发，component 映射 views/
utils/http/           axios 封装：401 无感刷新（isRefreshing 队列）、4xx/5xx 分级提示
utils/websocket/      RealtimeClient 单例（幂等 start/退避重连/心跳/事件总线）
views/                页面按后端模块 1:1 镜像（system/* monitor/* account-settings）
```

新页面的推荐路径：优先组合 `BaseApi + useCrudTable + useDialogForm`，
参照已迁移的 config / post / notice 页面（而非手写 hook 的旧页面）。

## 3. 技术栈版本（2026-11）

| 端 | 关键依赖 |
|---|---|
| 后端 | FastAPI 0.115+ / SQLModel 0.0.22 / classy-fastapi / redis(asyncio) / slowapi+limits / loguru / Alembic |
| 前端 | Vue 3.5 / Vite 8(Rolldown) / TS 6 / Element Plus / Pinia / vue-pure-admin v7 脚手架 / Tailwind 4 / vitest + playwright |

## 4. 深入资料

- 领域设计图与时序图：`service/docs/design/`
- 后端开发规范（代码风格/Ruff/命名）：`service/docs/guide/development.md`
- 历史评估与优化决策：`docs/archive/`
