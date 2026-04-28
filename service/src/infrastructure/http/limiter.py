"""限流模块。

基于 slowapi 实现请求限流功能。
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import Response

from src.config.settings import settings


def get_real_ip(request: Request) -> str:
    """获取真实客户端 IP。

    优先从 X-Forwarded-For 获取真实IP，否则使用远程地址。
    适用于反向代理场景。
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_real_ip)


def get_limiter() -> Limiter:
    """获取限流器实例。"""
    return limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """限流异常处理器。

    当请求触发限流时返回 429 响应。
    """
    return _rate_limit_exceeded_handler(request, exc)


def get_rate_limit_key() -> str:
    """获取默认限流配置。

    从 settings 读取限流配置，格式为 "次数/时间单位"。
    例如: "100/minute", "5/second"
    """
    return f"{settings.RATE_LIMIT_TIMES}/{settings.RATE_LIMIT_SECONDS}"


DEFAULT_LIMIT = get_rate_limit_key()
