# 限流方案

> 最后更新：2026-11-07（与 commit `2a2f0f4`/`a5397e5` 后的实际实现对齐）

## 概述

本系统使用 [slowapi](https://slowapi.readthedocs.io/) 库实现请求限流功能，基于 [limits](https://limits.readthedocs.io/) 提供灵活的限流策略，分两层：

1. **全局限流**（SlowAPI 中间件）：所有路由默认 `RATE_LIMIT_TIMES` 次 / `RATE_LIMIT_SECONDS` 秒；
2. **登录/注册专属限流**（`LoginRateLimitMiddleware`）：独立更严格的 `LOGIN_RATE_LIMIT`，防暴力破解。

> ⚠️ **不要给 classy_fastapi 路由加 `@limiter.limit()` 装饰器**：slowapi 装饰器与
> Routable 的方法绑定机制不兼容，运行时会抛 `IndexError: tuple index out of range`
> 直接打挂接口（曾由单测网住，见 commit `2a2f0f4` 的回退记录）。
> 本项目限流一律通过中间件实现。

## 技术栈

- **slowapi**: FastAPI/Starlette 限流扩展库（含三处上游补丁，见 `limiter.py` 模块注释）
- **limits**: 通用限流库（登录专属限流直接使用其 `FixedWindowRateLimiter`）

## 集成配置

### 1. 限流器初始化

限流器在 `src/infrastructure/http/limiter.py` 中定义：

```python
_default_limit = f"{settings.RATE_LIMIT_TIMES} per {settings.RATE_LIMIT_SECONDS} seconds"

limiter = Limiter(
    key_func=get_real_ip,
    default_limits=[_default_limit],
    storage_uri=_get_storage_uri(),          # Redis（默认）或 memory
    storage_options={"protocol": 2},         # Redis 6.0 以下需 RESP2
    strategy="fixed-window",
)
```

### 2. 客户端 IP 识别（可信代理）

```python
def get_real_ip(request: Request) -> str:
    """仅当直连对端位于 TRUSTED_PROXIES 时才采信 X-Forwarded-For。"""
```

- 直连部署（`TRUSTED_PROXIES` 为空，默认）：**忽略 X-Forwarded-For**——
  盲信可伪造的 XFF 等于给每个请求独立限流桶，全局限流形同虚设；
- 反向代理部署：在 `.env` 配置 `TRUSTED_PROXIES=127.0.0.1,::1,10.0.0.0/8`。
- 该函数绝不抛异常（key_func 异常会导致限流 fail-open）。

### 3. 应用集成

在 `src/main.py` 中（注意中间件顺序：LoginRateLimit → SlowAPI → IPFilter → RequestLogging）：

```python
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(LoginRateLimitMiddleware)   # 登录/注册专属限流
```

## 配置项（`src/config/settings.py`）

```python
RATE_LIMIT_TIMES: int = Field(default=100, ge=1)    # 全局：每时间段允许的请求次数
RATE_LIMIT_SECONDS: int = Field(default=60, ge=1)   # 全局：时间段（秒）
RATE_LIMIT_STORAGE: str = "redis"                   # redis 或 memory
LOGIN_RATE_LIMIT: str = "20/minute"                 # 登录/注册专属（testing 环境放宽）
TRUSTED_PROXIES: str = ""                           # 可信反向代理 IP/CIDR，逗号分隔
```

各环境实际值见 `.env.development`（全局 1000/60s，登录 100/min）、
`.env.production`（全局 100/60s，登录 20/min）、`.env.testing`（放宽，避免用例触发限流）。

## 登录/注册专属限流（`LoginRateLimitMiddleware`）

`src/infrastructure/http/login_rate_limiter.py`，基于 `limits` 库的固定窗口计数：

- 保护路径：`POST /api/system/login`、`POST /api/system/register`（精确匹配）；
- 限额按 IP（复用 `get_real_ip`，同样受 TRUSTED_PROXIES 约束）；
- 存储与全局限流共用（Redis 多 worker 共享 / 降级 memory）；
- 触发后返回 429 + `Retry-After` 头（与 body 的 `retry_after` 一致）；
- 存储异常时**放行并记录日志**（fail-open，与全局限流语义一致——限流组件故障不阻断登录主功能）。

## 响应格式

触发限流时返回 HTTP 429，统一响应体（`Retry-After` 头数值一致）：

```json
{
    "code": 429,
    "msg": "请求过于频繁，请稍后再试",
    "data": null,
    "retry_after": 57
}
```

## 注意事项

- **限流键**：全局与登录限流均使用 `get_real_ip`；新增自定义键时必须同样
  遵守可信代理语义，且不得抛异常；
- **fail-open 语义**：Redis/存储故障时限流放行（记录日志）——这是有意取舍，
  限流组件故障不应阻断正常业务；
- **多 worker**：生产 `--workers 4`，限流计数在 Redis 中共享；memory 存储
  仅适用于单进程（测试）；
- **不要使用装饰器**：见顶部警告；如需为特定路由定制限额，扩展
  `LoginRateLimitMiddleware` 的保护路径模式或在中间件内增加分组规则。
