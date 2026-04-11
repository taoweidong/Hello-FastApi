"""请求日志中间件。"""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging.logger import log_request, logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录所有 HTTP 请求的中间件。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # 记录请求开始
        logger.debug(f"请求开始: {request.method} {request.url.path} 来自 {client_ip}")

        response: Response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time
        duration_ms = process_time * 1000

        # 记录请求完成
        log_request(method=request.method, path=request.url.path, status_code=response.status_code, duration_ms=duration_ms, client_ip=client_ip)

        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        return response
