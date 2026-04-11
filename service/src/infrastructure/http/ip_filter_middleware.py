"""IP 黑白名单过滤中间件。"""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging.logger import logger


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
            logger.warning(f"IP {client_ip} 不在白名单中，访问被拒绝")
            return Response(content='{"detail": "访问被拒绝"}', status_code=403, media_type="application/json")

        # 检查黑名单
        if client_ip in self.blacklist:
            logger.warning(f"IP {client_ip} 在黑名单中，访问被拒绝")
            return Response(content='{"detail": "访问被拒绝"}', status_code=403, media_type="application/json")

        response: Response = await call_next(request)
        return response
