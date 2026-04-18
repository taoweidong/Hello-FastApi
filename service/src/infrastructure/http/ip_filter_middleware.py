"""IP 黑白名单过滤中间件。"""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging.logger import logger


class IPFilterMiddleware(BaseHTTPMiddleware):
    """IP 黑白名单过滤中间件。

    从 app.state 动态读取 ip_blacklist / ip_whitelist 集合，
    无需重启服务即可生效。规则由 IPFilterCache 在启动时加载，
    并在规则变更时自动刷新。
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        blacklist: set[str] = getattr(request.app.state, "ip_blacklist", set())
        whitelist: set[str] = getattr(request.app.state, "ip_whitelist", set())

        # 如果配置了白名单，只允许白名单中的 IP 访问
        if whitelist and client_ip not in whitelist:
            logger.warning(f"IP {client_ip} 不在白名单中，访问被拒绝")
            return Response(content='{"detail": "访问被拒绝"}', status_code=403, media_type="application/json")

        # 检查黑名单
        if client_ip in blacklist:
            logger.warning(f"IP {client_ip} 在黑名单中，访问被拒绝")
            return Response(content='{"detail": "访问被拒绝"}', status_code=403, media_type="application/json")

        response: Response = await call_next(request)
        return response
