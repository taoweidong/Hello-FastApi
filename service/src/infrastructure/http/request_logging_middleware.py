"""请求日志中间件。

记录所有 HTTP 请求，并对非 GET 请求自动写入 SystemLog 表作为审计日志。
"""

import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import Request, Response
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import settings
from src.infrastructure.logging.logger import log_request, logger

# 不需要写入 SystemLog 审计表的路径前缀集合
# 这些路径仍会写入 access.log 文件，但不写数据库审计表
_SKIP_LOG_PATH_PREFIXES = frozenset(
    {
        "/api/system/login",  # 含密码明文，有独立的 login_logs 表
        "/api/system/register",  # 含密码明文
        "/api/system/logout",  # 无业务审计价值
        "/api/system/refresh-token",  # 高频(30min)、含敏感token
        "/api/system/get-async-routes",  # 高频路由加载
        "/api/system/list-all-role",  # 高频下拉列表
        "/api/system/list-role-ids",  # 高频角色查询
        "/api/system/role-menu",  # 高频权限查询
        "/api/system/role-menu-ids",  # 高频权限查询
    }
)


def _extract_user_agent_info(user_agent: str) -> tuple[str, str]:
    """从 User-Agent 字符串中粗略提取浏览器和操作系统信息。

    Returns:
        (browser, system) 元组
    """
    browser = "unknown"
    system = "unknown"

    if not user_agent:
        return browser, system

    ua_lower = user_agent.lower()
    if "windows" in ua_lower:
        system = "Windows"
    elif "mac os" in ua_lower:
        system = "Mac OS"
    elif "linux" in ua_lower:
        system = "Linux"
    elif "android" in ua_lower:
        system = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        system = "iOS"

    if "edg/" in ua_lower:
        browser = "Edge"
    elif "chrome/" in ua_lower:
        browser = "Chrome"
    elif "firefox/" in ua_lower:
        browser = "Firefox"
    elif "safari/" in ua_lower and "chrome/" not in ua_lower:
        browser = "Safari"

    return browser, system


def _try_decode_user_id(authorization: str | None) -> str | None:
    """尝试从 Authorization header 解码 JWT 获取用户 ID。

    解码失败时静默返回 None，不抛出异常。
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") == "access":
            return str(payload.get("sub", ""))
    except JWTError:
        pass
    return None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录所有 HTTP 请求的中间件。

    - 所有请求：打印日志 + 记录处理时间
    - 非 GET 请求：额外写入 SystemLog 表作为审计日志（排除 _SKIP_LOG_PATH_PREFIXES 中的路径）
    """

    @staticmethod
    def _should_skip_log(path: str) -> bool:
        """判断请求路径是否应跳过审计日志写入。

        使用前缀匹配：若 path 以 _SKIP_LOG_PATH_PREFIXES 中任一前缀开头则跳过。
        """
        return any(path.startswith(prefix) for prefix in _SKIP_LOG_PATH_PREFIXES)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # 记录请求开始
        logger.debug(f"请求开始: {request.method} {request.url.path} 来自 {client_ip}")

        # 读取请求体（仅非 GET 请求需要）
        body_str: str | None = None
        if request.method != "GET":
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body_str = body_bytes.decode("utf-8", errors="replace")
                    if len(body_str) > 4000:
                        body_str = body_str[:4000] + "...(truncated)"
            except Exception:
                body_str = None

        response: Response = await call_next(request)

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

        # 非 GET 请求写入 SystemLog 审计表（排除敏感/高频路径，后台异步执行，不阻塞响应）
        if request.method != "GET" and not self._should_skip_log(request.url.path):
            self._write_system_log_async(
                request=request, response=response, client_ip=client_ip, body=body_str, duration_ms=duration_ms
            )

        return response

    def _write_system_log_async(
        self, request: Request, response: Response, client_ip: str, body: str | None, duration_ms: float
    ) -> None:
        """将非 GET 请求写入 SystemLog 审计表（后台异步执行，不阻塞响应）。"""
        import asyncio

        user_agent = request.headers.get("user-agent", "")
        browser, system = _extract_user_agent_info(user_agent)
        creator_id = _try_decode_user_id(request.headers.get("authorization"))

        # 捕获写入日志所需的所有数据（不再依赖 request/response 对象）
        log_data = {
            "id": uuid.uuid4().hex,
            "module": self._extract_module(request.url.path),
            "path": request.url.path,
            "body": body,
            "method": request.method,
            "ipaddress": client_ip,
            "browser": browser,
            "system": system,
            "response_code": response.status_code,
            "response_result": None,
            "status_code": response.status_code,
            "creator_id": creator_id,
            "description": f"{request.method} {request.url.path} - {duration_ms:.0f}ms",
        }

        async def _write_log_background() -> None:
            """后台任务：写入审计日志。"""
            from src.infrastructure.database import get_async_session_factory
            from src.infrastructure.database.models import SystemLog

            try:
                log_entry = SystemLog(
                    **log_data, created_time=datetime.now(timezone.utc), updated_time=datetime.now(timezone.utc)
                )
                session_factory = get_async_session_factory()
                async with session_factory() as session:
                    session.add(log_entry)
                    await session.commit()
            except Exception:
                logger.warning(
                    f"后台写入 SystemLog 审计日志失败: {log_data['method']} {log_data['path']}", exc_info=True
                )

        # 后台执行，不阻塞响应
        asyncio.create_task(_write_log_background())

    @staticmethod
    def _extract_module(path: str) -> str:
        """从请求路径提取模块名称。

        例如: /api/system/user -> user, /api/system/role/create -> role
        """
        parts = path.strip("/").split("/")
        # 路径格式通常为 /api/system/{module}/...
        if len(parts) >= 3:
            return parts[2]
        return path
