"""请求日志中间件。

记录所有 HTTP 请求，并对非 GET 请求自动写入 SystemLog 表作为审计日志。
请求体落库前必须经过敏感字段脱敏（password/token 等），防止明文密码进入审计表。
"""

import json
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from fastapi import Request, Response
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from src.application.utils.user_agent import extract_user_agent_info
from src.config.settings import settings
from src.infrastructure.common.sanitizer import DataSanitizer
from src.infrastructure.http.audit_log_queue import get_audit_log_queue
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


@lru_cache(maxsize=2048)
def _decode_token_payload(token: str) -> dict[str, Any]:
    """JWT 二次解码结果缓存（token→payload）。

    中间件对每个非 GET 请求会解码一次 JWT（路由依赖链已解码过一次，属二次开销）。
    Token 一次性/短生命周期特性强，LRU 上限 2048 不会长期膨胀；
    解码失败（JWTError）不进缓存（lru_cache 不缓存异常），失败路径行为不变。
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def _try_decode_user_id(authorization: str | None) -> str | None:
    """尝试从 Authorization header 解码 JWT 获取用户 ID。

    解码结果经模块级有界 LRU 缓存；解码失败时静默返回 None，不抛出异常。
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        payload = _decode_token_payload(token)
        if payload.get("type") == "access":
            return str(payload.get("sub", ""))
    except JWTError:
        pass
    return None


def sanitize_body_for_audit(body_str: str | None) -> str | None:
    """对请求体做敏感字段脱敏后再落审计表。

    JSON 请求体按 key 脱敏（password/token/secret 等字段值替换为 ********）；
    非 JSON 文本退化为正则脱敏（覆盖 password=xxx 等形态）；
    二进制/乱码内容（如 multipart 上传）在 decode 阶段已替换为乱码字符，
    正则脱敏对其无副作用。

    这层脱敏不可省略：/user/create、/user/change-password、/user/{id}/reset-password
    等路径的请求体都携带明文密码，直接落库等于把密码写进审计表。
    """
    if body_str is None:
        return None
    try:
        data: Any = json.loads(body_str)
    except (json.JSONDecodeError, ValueError):
        return DataSanitizer.sanitize_string(body_str)
    if isinstance(data, dict):
        return json.dumps(DataSanitizer.sanitize_dict(data), ensure_ascii=False)
    if isinstance(data, list):
        return json.dumps(DataSanitizer.sanitize_list(data), ensure_ascii=False)
    return body_str


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
                request=request,
                response=response,
                client_ip=client_ip,
                body=sanitize_body_for_audit(body_str),
                duration_ms=duration_ms,
            )

        return response

    def _write_system_log_async(
        self, request: Request, response: Response, client_ip: str, body: str | None, duration_ms: float
    ) -> None:
        """将非 GET 请求写入 SystemLog 审计表（后台异步执行，不阻塞响应）。

        两条路径：
        - worker 已启动（lifespan 正常拉起）：入队攒批落库（见 audit_log_queue），
          消除每请求独立会话与逐条 INSERT 的写放大；
        - worker 未启动（测试 empty_lifespan / 降级）：退化为历史行为——
          后台任务独立会话直写，保证"请求返回后日志立即可查"的既有语义。
        """
        import asyncio

        user_agent = request.headers.get("user-agent", "")
        browser, system = extract_user_agent_info(user_agent)
        creator_id = _try_decode_user_id(request.headers.get("authorization"))

        # 捕获写入日志所需的所有数据（不再依赖 request/response 对象）
        log_data: dict[str, Any] = {
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
            # 时间戳在捕获时生成：入队攒批后落库时间会晚于请求完成时间
            "created_time": datetime.now(timezone.utc),
            "updated_time": datetime.now(timezone.utc),
        }

        # worker 未启动时走历史兜底路径（后台任务独立会话直写）
        if not get_audit_log_queue().running:
            asyncio.create_task(_write_log_background(log_data))
            return
        # worker 已启动：入队攒批落库（队列满时由 enqueue 内部丢弃并告警）
        get_audit_log_queue().enqueue(log_data)

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


async def _write_log_background(log_data: dict[str, Any]) -> None:
    """兜底路径：worker 未启动时以独立会话直写一条审计日志（历史行为）。

    保持与批量队列一致的语义：写入失败仅告警，不影响响应。
    """
    from src.infrastructure.database import get_async_session_factory
    from src.infrastructure.database.models import SystemLog

    try:
        log_entry = SystemLog(**log_data)
        session_factory = get_async_session_factory()
        async with session_factory() as session:
            session.add(log_entry)
            await session.commit()
    except Exception:
        logger.warning(f"后台写入 SystemLog 审计日志失败: {log_data['method']} {log_data['path']}", exc_info=True)
