"""限流模块。

基于 slowapi 实现请求限流功能。
通过 SlowAPIMiddleware 全局中间件处理限流，
解决 @limiter.limit() 装饰器与 class-based 路由的兼容性问题。

补丁说明：
- 补丁 1：_get_route_name 无法处理 functools.partial（classy_fastapi 路由端点）
- 补丁 2：_check_request_limit 直接访问 __module__/__name__
- 补丁 3：_check_limits 对非 RateLimitExceeded 异常错误地调用 _rate_limit_exceeded_handler
"""

import functools
import logging
from collections.abc import Callable

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.config.settings import settings

_logger = logging.getLogger(__name__)


def _unwrap_partial(handler):
    """递归解包 functools.partial，返回原始函数。"""
    while isinstance(handler, functools.partial):
        handler = handler.func
    return handler


# ---------------------------------------------------------------------------
# 补丁 1：slowapi.middleware._get_route_name 无法处理 functools.partial
# ---------------------------------------------------------------------------
import slowapi.middleware as _slowapi_middleware  # noqa: E402

_original_get_route_name = _slowapi_middleware._get_route_name


def _patched_get_route_name(handler):
    return _original_get_route_name(_unwrap_partial(handler))


_slowapi_middleware._get_route_name = _patched_get_route_name


# ---------------------------------------------------------------------------
# 补丁 2：Limiter._check_request_limit 也直接访问 __module__/__name__
# ---------------------------------------------------------------------------
_original_check_request_limit = Limiter._check_request_limit


def _patched_check_request_limit(self, request, endpoint_func, in_middleware=True):
    unwrapped = _unwrap_partial(endpoint_func) if endpoint_func else endpoint_func
    return _original_check_request_limit(self, request, unwrapped, in_middleware)


Limiter._check_request_limit = _patched_check_request_limit


# ---------------------------------------------------------------------------
# 补丁 3：_check_limits 对非 RateLimitExceeded 异常错误地调用
#          _rate_limit_exceeded_handler（要求 exc.detail 属性），
#          导致 AttributeError: 'ValueError' object has no attribute 'detail'
# ---------------------------------------------------------------------------
_original_check_limits = _slowapi_middleware._check_limits


def _patched_check_limits(
    limiter: Limiter, request: Request, handler: Callable | None, app: Starlette
) -> tuple[Callable | None, bool, Exception | None]:
    if limiter._auto_check and not getattr(request.state, "_rate_limiting_complete", False):
        try:
            limiter._check_request_limit(request, handler, True)
        except RateLimitExceeded as e:
            # 正常限流异常，走标准处理流程
            exception_handler = app.exception_handlers.get(type(e), _rate_limit_exceeded_handler)
            return exception_handler, False, e
        except Exception as e:
            # 非限流异常（ValueError、AttributeError 等），
            # 不应交给 _rate_limit_exceeded_handler（它要求 exc.detail），
            # 而是记录日志后放行，避免中间件崩溃。
            _logger.exception("slowapi 内部错误，跳过限流检查: %s", e)
            return None, False, None

    return None, False, None


_slowapi_middleware._check_limits = _patched_check_limits


def get_real_ip(request: Request) -> str:
    """获取真实客户端 IP。

    优先从 X-Forwarded-For 获取真实IP，否则使用远程地址。
    适用于反向代理场景。
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


def _get_storage_uri() -> str:
    """获取限流存储 URI。

    优先使用 Redis 作为限流存储（支持分布式多 worker 限流）。
    如果 Redis 不可用或配置为 memory，则使用内存存储。
    """
    rate_limit_storage = getattr(settings, "RATE_LIMIT_STORAGE", "redis")
    if rate_limit_storage == "memory":
        return "memory://"

    redis_url = getattr(settings, "REDIS_URL", "")
    if redis_url:
        return redis_url

    return "memory://"


# 使用默认限额，SlowAPIMiddleware 会对所有未豁免的路由生效
_default_limit = f"{settings.RATE_LIMIT_TIMES} per {settings.RATE_LIMIT_SECONDS} seconds"

limiter = Limiter(
    key_func=get_real_ip, default_limits=[_default_limit], storage_uri=_get_storage_uri(), strategy="fixed-window"
)


def get_limiter() -> Limiter:
    """获取限流器实例。"""
    return limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """限流异常处理器。

    当请求触发限流时返回统一格式的 429 响应。
    """
    return JSONResponse(
        status_code=429,
        content={
            "code": 429,
            "msg": "请求过于频繁，请稍后再试",
            "data": None,
            "retry_after": int(str(exc).split(":")[-1].strip()) if ":" in str(exc) else 60,
        },
        headers={"Retry-After": "60"},
    )
