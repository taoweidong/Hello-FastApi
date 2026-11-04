"""WebSocket 鉴权（ws_auth）单元测试。

覆盖黑名单、过期/伪造令牌、类型错误、缺 sub 等分支。
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.api.dependencies.ws_auth import get_ws_user_id
from src.config.settings import get_settings
from src.domain.exceptions import UnauthorizedError
from src.domain.services.token_service import TokenService


@pytest.fixture
def token_service() -> TokenService:
    s = get_settings()
    return TokenService(
        secret_key=s.JWT_SECRET_KEY,
        algorithm=s.JWT_ALGORITHM,
        access_expire_minutes=s.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_days=s.REFRESH_TOKEN_EXPIRE_DAYS,
    )


@pytest.fixture
def not_blacklisted():
    """黑名单查询返回 False（未拉黑）。"""
    with patch("src.api.dependencies.ws_auth.get_cache_service", new=AsyncMock(return_value=AsyncMock())) as mock:
        mock.return_value.is_token_blacklisted = AsyncMock(return_value=False)
        yield mock.return_value


@pytest.mark.unit
class TestGetWsUserId:
    async def test_valid_token_returns_user_id(self, token_service, not_blacklisted):
        token = token_service.create_access_token({"sub": "user-42"})
        assert await get_ws_user_id(token) == "user-42"

    async def test_missing_token_rejected(self, not_blacklisted):
        with pytest.raises(UnauthorizedError):
            await get_ws_user_id(None)

    async def test_empty_token_rejected(self, not_blacklisted):
        with pytest.raises(UnauthorizedError):
            await get_ws_user_id("")

    async def test_garbage_token_rejected(self, not_blacklisted):
        with pytest.raises(UnauthorizedError):
            await get_ws_user_id("not.a.valid.jwt")

    async def test_expired_token_rejected(self, token_service, not_blacklisted):
        from datetime import timedelta

        token = token_service.create_access_token({"sub": "u1"}, expires_delta=timedelta(seconds=-10))
        with pytest.raises(UnauthorizedError):
            await get_ws_user_id(token)

    async def test_refresh_type_token_rejected(self, token_service, not_blacklisted):
        """refresh 类型的令牌不得用于 WS 连接。"""
        token = token_service.create_refresh_token({"sub": "u1"})
        with pytest.raises(UnauthorizedError):
            await get_ws_user_id(token)

    async def test_blacklisted_token_rejected(self, token_service, not_blacklisted):
        """已登出（拉黑）的令牌不得建立 WS 连接。"""
        not_blacklisted.is_token_blacklisted = AsyncMock(return_value=True)
        token = token_service.create_access_token({"sub": "u1"})
        with pytest.raises(UnauthorizedError):
            await get_ws_user_id(token)

    async def test_token_without_sub_rejected(self, token_service, not_blacklisted):
        token = token_service.create_access_token({})
        with pytest.raises(UnauthorizedError):
            await get_ws_user_id(token)
