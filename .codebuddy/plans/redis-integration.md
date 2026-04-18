---
name: redis-integration
overview: 集成 Redis 到后端服务，启用 Token 黑名单（logout 安全）、权限缓存（减少 DB 查询）、应用生命周期管理，提升后端效率
todos:
  - id: cache-service
    content: 创建 CacheService 封装 Token 黑名单和权限缓存的 Redis 操作
    status: pending
  - id: lifecycle-redis
    content: 在应用生命周期中初始化和关闭 Redis 连接
    status: pending
    dependencies:
      - cache-service
  - id: token-blacklist
    content: 实现 logout Token 黑名单机制（auth_service + auth_router + auth 依赖）
    status: pending
    dependencies:
      - cache-service
  - id: perm-cache
    content: 实现用户权限 Redis 缓存（get_current_active_user + require_permission）
    status: pending
    dependencies:
      - cache-service
  - id: env-config
    content: 更新 .env 配置文件 REDIS_URL 为 127.0.0.1
    status: pending
---

## 用户需求

服务端集成 Redis（127.0.0.1:6379，无认证），提升后端效率。

## 产品概述

在现有 FastAPI 后端中激活已搭建但未使用的 Redis 基础设施，实现 Token 黑名单和权限缓存两大核心功能，解决当前 logout 后 Token 仍有效、每次请求均查库验证权限的性能瓶颈。

## 核心功能

- **应用生命周期集成 Redis**：启动时初始化 Redis 连接，关闭时释放连接
- **Token 黑名单**：logout 时将 access_token 写入 Redis 黑名单（TTL=Token 剩余过期时间），请求鉴权时先查黑名单
- **用户权限缓存**：将用户角色与权限查询结果缓存到 Redis（TTL=5分钟），减少高频数据库查询
- **配置对齐**：REDIS_URL 改为 `redis://127.0.0.1:6379/0`

## 技术栈

- 后端框架：FastAPI + async/await
- 缓存：redis.asyncio（redis>=5.0.0，已安装）
- 架构模式：DDD 分层 + 依赖注入（遵循现有项目约定）

## 实现方案

### 核心策略

在已有的 `RedisManager` 基础上，新增 `CacheService` 封装黑名单与权限缓存的 Redis 操作，通过 FastAPI `Depends()` 注入到鉴权链路和 AuthService 中。遵循现有 DDD 分层：CacheService 属于基础设施层，AuthService 通过注入使用。

### 关键技术决策

1. **Token 黑名单 Key 设计**：使用 `token:blacklist:{sha256(token)[:32]}` 作为 Key，避免存储完整 Token 字符串。TTL = Token 的 `exp` - 当前时间（剩余过期秒数），Token 过期后黑名单记录自动清除。
2. **权限缓存 Key 设计**：使用 `user:perms:{user_id}` 作为 Key，Value 为 JSON 序列化的用户角色+权限列表，TTL=300s（5分钟），通过 TTL 自然过期保证最终一致性。
3. **不修改 Token 结构**：不添加 `jti` 字段，避免使现有已颁发 Token 失效，使用 Token 哈希作为标识即可。
4. **降级策略**：Redis 连接失败时降级为直接查库，不阻塞正常请求（日志告警）。

### 性能与可靠性

- 权限缓存将每次请求 2-3 次 DB 查询降为 0 次（缓存命中时），TTL 内 QPS 提升
- Token 黑名单检查为 O(1) Redis GET 操作，无性能瓶颈
- Redis 连接异常时自动降级到 DB 查询，保证服务可用性

## 目录结构

```
service/
├── src/
│   ├── infrastructure/
│   │   ├── cache/
│   │   │   ├── __init__.py           # [MODIFY] 导出新增的 CacheService 工厂函数
│   │   │   ├── redis_manager.py      # [不修改] 已有的 RedisManager 单例
│   │   │   └── cache_service.py      # [NEW] 缓存服务，封装黑名单和权限缓存的 Redis 操作
│   │   └── lifecycle/
│   │       └── lifespan.py           # [MODIFY] 启动时初始化 Redis，关闭时释放连接
│   ├── api/
│   │   └── dependencies/
│   │       ├── __init__.py           # [MODIFY] 导出 get_cache_service
│   │       ├── auth.py               # [MODIFY] get_current_user_id 添加黑名单检查；get_current_active_user 和 require_permission 添加权限缓存
│   │       └── auth_service.py       # [MODIFY] AuthService 工厂注入 CacheService
│   ├── application/
│   │   └── services/
│   │       └── auth_service.py       # [MODIFY] 添加 logout 方法，接收 token 写入黑名单
│   ├── api/v1/
│   │   └── auth_router.py            # [MODIFY] logout 接口提取 token 并调用 service.logout()
│   └── config/
│       └── settings.py               # [不修改] REDIS_URL 默认值已满足
├── .env.development                  # [MODIFY] REDIS_URL 改为 redis://127.0.0.1:6379/0
└── .env.production                   # [MODIFY] 确认 REDIS_URL 配置
```

## 实现要点

- `CacheService` 所有方法需 try/except 包裹 Redis 操作，失败时 log.warning 并降级返回安全默认值（黑名单检查返回 False、权限缓存返回 None）
- `auth_router.py` 的 logout 需从 `Authorization` header 中提取原始 token 字符串传入 service
- 权限缓存在用户角色/权限变更时暂不主动失效，依赖 TTL 自然过期，简化实现
- 代码注释遵循项目约定：全部使用中文

## Agent Extensions

### Skill

- **python-code-quality**: 确保新增 CacheService 及修改的鉴权代码符合 OOP 设计、类型注解完整、遵循 SOLID 原则
- **async-python-patterns**: 确保 Redis 异步操作正确使用 async/await，避免阻塞事件循环