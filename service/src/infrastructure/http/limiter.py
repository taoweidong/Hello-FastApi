"""限流模块。

基于 limits.aio（limits>=3.6 提供的异步存储/异步策略）实现全局限流：
自写轻量纯 ASGI 中间件 ``RateLimitMiddleware``，替代 SlowAPIMiddleware。

替换 slowapi 的原因：
1. slowapi 底层使用同步 redis 客户端，每个请求都会在事件循环内做一次
   同步 Redis 往返，高并发下阻塞整个事件循环；
2. slowapi 的 @limiter.limit 装饰器与 classy_fastapi 的 partial 端点
   不兼容（此前靠 monkey-patch slowapi 三处内部函数绕过，本项目路由
   全部基于 Routable，从未使用过路由级装饰器）。

语义与原 SlowAPIMiddleware 对齐：
- 按「真实客户端 IP + 请求路径」分桶（slowapi 默认 key_style="url"）；
- 固定窗口，默认限额来自 settings.RATE_LIMIT_TIMES / RATE_LIMIT_SECONDS；
- 存储优先 Redis（多 worker 共享限流窗口），RATE_LIMIT_STORAGE=memory
  或未配置 REDIS_URL 时降级为进程内 memory 存储；
- 存储异常（如 Redis 抖动）时 fail-open 放行，不因限流组件故障阻断业务；
- 超限返回统一格式的 429 JSON（与原 rate_limit_exceeded_handler 一致）。
"""

import ipaddress
import time

from limits import parse
from limits.aio.strategies import FixedWindowRateLimiter
from limits.storage import storage_from_string
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from src.config.settings import settings
from src.infrastructure.logging.logger import logger


def get_real_ip(request: Request) -> str:
    """获取真实客户端 IP（作为限流 key）。

    仅当直连对端（request.client.host，不可伪造）位于可信代理列表时才采信
    X-Forwarded-For。直连部署（TRUSTED_PROXIES 为空，默认）下 XFF 可被任意
    伪造——盲信它等于给每个请求一个独立限流桶，全局限流形同虚设。

    本函数绝不抛异常：key_func 异常会触发限流 fail-open，
    因此所有可预见异常都在此收敛为可用的字符串 key。

    配置示例（nginx 反代在本机）：TRUSTED_PROXIES=127.0.0.1,::1,10.0.0.0/8
    """
    try:
        client_host = request.client.host if request.client else None
    except AttributeError:
        client_host = None
    if client_host and _is_trusted_proxy(client_host):
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    try:
        # 等价于原 slowapi.util.get_remote_address
        return request.client.host if request.client else "127.0.0.1"
    except Exception:
        # request.client 为 None 等极端场景：退化为固定 key（共享限流桶，安全侧）
        return "127.0.0.1"


def _is_trusted_proxy(client_host: str) -> bool:
    """判断直连对端是否为配置的可信反向代理。"""
    raw = getattr(settings, "TRUSTED_PROXIES", "") or ""
    try:
        client_ip = ipaddress.ip_address(client_host)
    except ValueError:
        return False
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if client_ip in ipaddress.ip_network(part, strict=False):
                return True
        except ValueError:
            logger.warning(f"忽略无效的 TRUSTED_PROXIES 条目: {part}")
    return False


def _get_storage_uri() -> str:
    """获取限流存储 URI（同步 scheme）。

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


def get_async_storage_uri(storage_uri: str | None = None) -> str:
    """获取限流存储 URI（limits.aio 异步 scheme）。

    复用 _get_storage_uri 的配置解析（RATE_LIMIT_STORAGE / REDIS_URL、
    未配置 Redis 时降级 memory），再转换为异步存储的 scheme 前缀
    （limits.aio 的存储注册名为 ``async+memory`` / ``async+redis`` 等）。
    """
    uri = storage_uri if storage_uri is not None else _get_storage_uri()
    if uri.startswith("unix://"):
        # unix socket 的异步 scheme 为 async+redis+unix
        return "async+redis+unix://" + uri[len("unix://") :]
    return f"async+{uri}"


def build_rate_limit_response(retry_after: int) -> JSONResponse:
    """构造统一格式的 429 限流响应（全局限流与登录限流共用）。"""
    return JSONResponse(
        status_code=429,
        content={"code": 429, "msg": "请求过于频繁，请稍后再试", "data": None, "retry_after": retry_after},
        headers={"Retry-After": str(retry_after)},
    )


class RateLimitMiddleware:
    """全局限流中间件（纯 ASGI 实现，异步存储不阻塞事件循环）。

    测试可通过 ``storage_uri`` 注入存储后端（如 ``memory://``）。
    """

    def __init__(self, app: ASGIApp, storage_uri: str | None = None) -> None:
        self.app = app
        # limits.aio 异步存储 + 异步策略：请求路径上不再有同步 Redis 往返。
        # implementation="redispy"：limits 的 async+redis 默认使用 coredis 客户端
        # （项目未安装），显式改用 redis-py 的 asyncio 客户端（项目已有 redis 依赖）
        self._storage = storage_from_string(get_async_storage_uri(storage_uri), implementation="redispy", protocol=2)
        self._strategy = FixedWindowRateLimiter(self._storage)
        self._item = parse(f"{settings.RATE_LIMIT_TIMES} per {settings.RATE_LIMIT_SECONDS} seconds")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # websocket 等非 HTTP 作用域不限流（与原 BaseHTTPMiddleware 行为一致）
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        identifier = get_real_ip(request)
        try:
            # 与原 SlowAPI 默认 key_style="url" 一致：按「IP + 请求路径」分桶
            if not await self._strategy.hit(self._item, identifier, scope["path"]):
                reset_at, _remaining = await self._strategy.get_window_stats(self._item, identifier, scope["path"])
                retry_after = max(1, int(reset_at - time.time()))
                logger.warning(f"全局限流触发: ip={identifier} path={scope['path']} retry_after={retry_after}s")
                await build_rate_limit_response(retry_after)(scope, receive, send)
                return
        except Exception:
            # 存储异常（如 Redis 抖动）时放行——fail-open，与登录限流语义一致，
            # 不因限流组件故障阻断业务；此处必须记日志保留排查线索。
            logger.exception("全局限流器内部错误，本次请求放行")
        await self.app(scope, receive, send)
