"""WebSocket 鉴权辅助。

复用与 HTTP 路径完全一致的 JWT 校验 + 黑名单逻辑，供 ws_router 使用。
"""

from __future__ import annotations

from typing import Any

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.domain_services import get_token_service
from src.domain.error_messages import ErrorMessages as EM
from src.domain.exceptions import UnauthorizedError


async def get_ws_user_id(token: str | None) -> str:
    """从 WebSocket 查询参数 token 中解析并校验用户 ID。

    校验步骤与 `get_current_user_id` 保持一致：
    1. decode JWT；2. 校验为 access 类型；3. 校验未进入黑名单；4. 提取 sub。
    """
    if not token:
        raise UnauthorizedError(EM.INVALID_OR_EXPIRED_TOKEN)

    token_service = get_token_service()
    payload: dict[str, Any] | None = token_service.decode_token(token)
    if payload is None:
        raise UnauthorizedError(EM.INVALID_OR_EXPIRED_TOKEN)
    if not token_service.verify_token_type(payload, "access"):
        raise UnauthorizedError(EM.INVALID_TOKEN_TYPE)

    cache_service = await get_cache_service()
    if await cache_service.is_token_blacklisted(token):
        raise UnauthorizedError(EM.TOKEN_REVOKED)

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError(EM.INVALID_TOKEN_PAYLOAD)
    return str(user_id)
