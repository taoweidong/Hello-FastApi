# 限流方案

## 概述

本系统使用 [slowapi](https://slowapi.readthedocs.io/) 库实现请求限流功能，基于 [limits](https://limits.readthedocs.io/) 提供灵活的限流策略。

## 技术栈

- **slowapi**: FastAPI/Starlette 限流扩展库
- **limits**: 通用限流库，支持多种存储后端

## 集成配置

### 1. 安装依赖

```toml
# pyproject.toml
slowapi>=0.1.9
limits>=3.10.0
```

### 2. 限流器初始化

限流器在 `src/infrastructure/http/limiter.py` 中定义：

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_real_ip(request: Request) -> str:
    """获取真实客户端 IP，支持反向代理场景"""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)

limiter = Limiter(key_func=get_real_ip)
```

### 3. 应用集成

在 `src/main.py` 中配置：

```python
from slowapi.errors import RateLimitExceeded
from src.infrastructure.http.limiter import limiter, rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

### 4. 全局配置

在 `src/config/settings.py` 中配置默认限流参数：

```python
# 限流配置
RATE_LIMIT_TIMES: int = Field(default=100, ge=1)    # 默认每时间段允许的请求次数
RATE_LIMIT_SECONDS: int = Field(default=60, ge=1)   # 默认时间段（秒）
```

## 使用方式

### 1. 在路由中使用限流装饰器

```python
from fastapi import Request
from src.infrastructure.http.limiter import DEFAULT_LIMIT, limiter

class AuthRouter(Routable):
    @post("/login")
    @limiter.limit(DEFAULT_LIMIT)  # 使用默认配置
    async def login(self, request: Request, dto: LoginDTO) -> dict:
        ...

    @post("/register")
    @limiter.limit("10/minute")    # 自定义配置
    async def register(self, request: Request, dto: RegisterDTO) -> dict:
        ...
```

### 2. 装饰器参数格式

| 格式 | 说明 | 示例 |
|------|------|------|
| `数量/second` | 每秒限流 | `"5/second"` |
| `数量/minute` | 每分钟限流 | `"100/minute"` |
| `数量/hour` | 每小时限流 | `"1000/hour"` |
| `数量/day` | 每天限流 | `"10000/day"` |

### 3. 注意事项

- **装饰器顺序**: `@router.get()` 必须在 `@limiter.limit()` 之上
- **request 参数**: 限流装饰器需要函数包含 `request: Request` 参数
- **速率限制**: 登录接口默认 `100/分钟`，注册接口 `10/分钟`

## 响应格式

触发限流时返回 HTTP 429 状态码：

```json
{
    "detail": "Rate limit exceeded: 100 per 1 minute"
}
```

## 扩展配置

###Redis 存储后端（生产环境推荐）

如需使用 Redis 作为限流存储后端，可以修改 `limiter.py`：

```python
from limits import storage
from limits.strategies import MovingWindowRateLimiter

storage_uri = "redis://localhost:6379"
limiter = Limiter(
    key_func=get_real_ip,
    storage_uri=storage_uri,
    strategy=MovingWindowRateLimiter
)
```

### 自定义限流键

可基于用户 ID、API Key 等自定义限流键：

```python
def get_user_id(request: Request) -> str:
    """基于用户 ID 限流"""
    return request.state.user_id

@limiter.limit(DEFAULT_LIMIT, key_func=get_user_id)
async def api_endpoint(request: Request):
    ...
```