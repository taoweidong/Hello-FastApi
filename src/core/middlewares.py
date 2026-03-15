"""FastAPI 应用程序的中间件。"""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logger import log_request, logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录所有 HTTP 请求的中间件。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # 记录请求开始
        logger.debug(f"请求开始: {request.method} {request.url.path} 来自 {client_ip}")

        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time
        duration_ms = process_time * 1000

        # 记录请求完成
        log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
        )

        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        return response


class IPFilterMiddleware(BaseHTTPMiddleware):
    """IP 黑白名单过滤中间件。"""

    def __init__(self, app: Callable, blacklist: set[str] | None = None, whitelist: set[str] | None = None):
        super().__init__(app)
        self.blacklist = blacklist or set()
        self.whitelist = whitelist or set()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        # 如果配置了白名单，只允许白名单中的 IP 访问
        if self.whitelist and client_ip not in self.whitelist:
            logger.warning(f"IP {client_ip} not in whitelist, access denied")
            return Response(
                content='{"detail": "Access denied"}',
                status_code=403,
                media_type="application/json",
            )

        # 检查黑名单
        if client_ip in self.blacklist:
            logger.warning(f"IP {client_ip} is blacklisted, access denied")
            return Response(
                content='{"detail": "Access denied"}',
                status_code=403,
                media_type="application/json",
            )

        return await call_next(request)
