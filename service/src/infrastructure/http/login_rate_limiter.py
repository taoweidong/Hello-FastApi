"""登录/注册接口专属限流中间件（防暴力破解）。

独立于 SlowAPI 中间件实现，原因有二：
1. slowapi 的 @limiter.limit 装饰器与 classy_fastapi 的方法绑定机制不兼容
   （调用时 IndexError: tuple index out of range），本项目路由全部基于 Routable；
2. 登录/注册是匿名可打点面，需要比全局默认值（100/min）严格得多的独立限额。

直接使用 slowapi 的底层库 `limits`（已是项目依赖）做固定窗口计数，
存储与全局限流共用同一 URI（Redis 多 worker 共享 / 降级 memory）。
"""

from __future__ import annotations

import time

from limits import parse
from limits.storage import storage_from_string
from limits.strategies import FixedWindowRateLimiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.config.settings import settings
from src.infrastructure.http.limiter import _get_storage_uri, get_real_ip
from src.infrastructure.logging.logger import logger

# 受保护的匿名认证端点（精确匹配，POST）
_PROTECTED_PATHS = frozenset({"/api/system/login", "/api/system/register"})


class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    """对 /login、/register 按 LOGIN_RATE_LIMIT 做按 IP 固定窗口限流。"""

    def __init__(self, app, storage_uri: str | None = None) -> None:
        super().__init__(app)
        # 与全局限流共享存储后端；测试可通过 storage_uri 注入 memory://
        self._storage = storage_from_string(storage_uri or _get_storage_uri(), protocol=2)
        self._strategy = FixedWindowRateLimiter(self._storage)
        self._item = parse(settings.LOGIN_RATE_LIMIT)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "POST" and request.url.path in _PROTECTED_PATHS:
            identifier = get_real_ip(request)
            try:
                if not self._strategy.hit(self._item, identifier):
                    # 重置时间即当前窗口结束点
                    reset_at, _remaining = self._strategy.get_window_stats(self._item, identifier)
                    retry_after = max(1, int(reset_at - time.time()))
                    logger.warning(
                        f"登录接口触发限流: ip={identifier} path={request.url.path} retry_after={retry_after}s"
                    )
                    return JSONResponse(
                        status_code=429,
                        content={
                            "code": 429,
                            "msg": "请求过于频繁，请稍后再试",
                            "data": None,
                            "retry_after": retry_after,
                        },
                        headers={"Retry-After": str(retry_after)},
                    )
            except Exception:
                # 存储异常（如 Redis 抖动）时放行——与全局限流的 fail-open 语义一致，
                # 不因限流组件故障阻断登录主功能；此处必须记日志保留排查线索。
                logger.exception("登录限流器内部错误，本次请求放行")
        return await call_next(request)
