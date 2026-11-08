# 缓存体系

> Redis 缓存的分层设计：按消费方拆分的窄端口、降级语义、分组清单与清理。
> 操作入口见[监控中心操作指导](../guide/monitoring.md)。

[← 返回文档导航](../README.md)

---

## 1. 结构总览

```
domain/services/                  窄端口（消费方各自声明所需能力）
├── cache_port.py                 TokenRevocationPort / UserCachePort / MenuCachePort / DictCachePort
│                                 （CachePort = 四者聚合，仅供组合根与 CacheService 使用）
├── cache_admin_port.py           CacheAdminPort（分组清单与清理，管理员运维面）
├── online_session_port.py        OnlineSessionStore（在线会话：Redis + 内存镜像双写）
infrastructure/cache/
├── cache_service.py              CacheService：实现上述全部端口（单例）
├── online_session_store.py       RedisOnlineSessionStore
└── ttl.py                        remaining_seconds（ceil 语义，防 TTL 截断）
```

原则：**服务只 import 自己用到的窄端口**（如 `AuthorizationService` 只依赖
`UserCachePort`），组合根 `get_cache_service` 统一提供 `CacheService` 实例。

## 2. 键空间与 TTL

| 键模式 | 用途 | TTL | 失效时机 |
|---|---|---|---|
| `user:info:{uid}` | 当前用户实体（轻量） | 300s | 用户/角色变更主动失效 |
| `user:perms:{uid}` | 权限条目列表 | 300s | 角色/用户变更批量失效 |
| `menu:all` | 全量菜单（登录/路由加速） | 600s | 菜单增删改失效 |
| `dict:{name}` | 字典项 | 3600s | 字典变更失效 |
| `token:blacklist:{hash}` | 已吊销令牌（SHA-256 前 32 位） | 令牌剩余有效期 | 自然过期 |
| `ip:rules` | IP 黑白名单快照 | 无 TTL | 规则变更刷新 |
| `online:user:{hash}` | 在线会话（OnlineSessionStore） | = access 剩余有效期 | 登出/强退/过期 |

## 3. 降级语义（统一约定）

- Redis 未配置/不可用时：读返回 None、写返回 False、清单返回 None，
  调用方回源数据库或跳过缓存，**不抛异常不阻断业务**；
- 令牌黑名单是唯一"fail-open"特例：Redis 故障期间已拉黑令牌放行
  （注释明确标注的取舍）；
- 在线会话双写内存镜像：Redis 挂掉时本进程仍可查询/强退。

## 4. 管理操作（CacheAdminPort）

`GET /cache-groups`、`POST /cache-clear`、`POST /cache-clear-all`（均需管理员/对应权限）：

- 分组清单：SCAN 统计各前缀键数量；
- 分组清理：SCAN+DELETE（非 FLUSHDB）；令牌黑名单组**拒绝清理**（安全红线）；
- 全量清理：逐个可清理组求和，跳过黑名单与限流计数键。

实现细节与安全考量见 `cache_service.py` 类内注释与
[监控中心操作指导](../guide/monitoring.md#2-缓存监控monitorcache)。

## 5. 二次开发：新增一类缓存

1. 在 `CacheService` 增加 key 前缀常量 + get/set/invalidate 三件套
   （复用 `_get_json/_set_json/_delete_keys`，自动获得降级语义）；
2. 若属新消费方：在 `cache_port.py` 增加窄端口 ABC，服务依赖该窄端口；
3. 若希望出现在缓存监控页：在 `_CACHE_GROUPS` 注册分组（决定是否可清理）；
4. 单测：`tests/unit/infrastructure/cache/`（mock redis，参照 test_cache_admin.py）。
