"""认证依赖项测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole
from src.domain.exceptions import ForbiddenError, UnauthorizedError


@pytest.mark.unit
class TestGetCurrentUserId:
    """get_current_user_id 函数测试。"""

    @patch("src.api.dependencies.auth.get_token_service")
    @patch("src.api.dependencies.auth.get_cache_service")
    async def test_valid_token_returns_user_id(self, mock_get_cache, mock_get_token):
        """有效令牌应返回用户ID。"""
        mock_token_svc = MagicMock()
        mock_token_svc.decode_token.return_value = {"sub": "user123", "type": "access"}
        mock_get_token.return_value = mock_token_svc

        mock_cache = AsyncMock()
        mock_cache.is_token_blacklisted.return_value = False
        mock_get_cache.return_value = mock_cache

        from src.api.dependencies.auth import get_current_user_id

        with patch("fastapi.security.HTTPBearer.__call__", return_value=MagicMock(credentials="token")):
            result = await get_current_user_id(
                credentials=MagicMock(credentials="valid_token"), token_service=mock_token_svc, cache_service=mock_cache
            )
            assert result == "user123"

    @patch("src.api.dependencies.auth.get_token_service")
    @patch("src.api.dependencies.auth.get_cache_service")
    async def test_invalid_token_raises_unauthorized(self, mock_get_cache, mock_get_token):
        """无效令牌应抛出 UnauthorizedError。"""
        mock_token_svc = MagicMock()
        mock_token_svc.decode_token.return_value = None
        mock_get_token.return_value = mock_token_svc

        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache

        from src.api.dependencies.auth import get_current_user_id

        with pytest.raises(UnauthorizedError, match="无效或已过期的令牌"):
            await get_current_user_id(
                credentials=MagicMock(credentials="invalid_token"),
                token_service=mock_token_svc,
                cache_service=mock_cache,
            )

    @patch("src.api.dependencies.auth.get_token_service")
    @patch("src.api.dependencies.auth.get_cache_service")
    async def test_wrong_token_type_raises_unauthorized(self, mock_get_cache, mock_get_token):
        """非 access 类型令牌应抛出 UnauthorizedError。"""
        mock_token_svc = MagicMock()
        mock_token_svc.decode_token.return_value = {"sub": "user123", "type": "refresh"}
        mock_get_token.return_value = mock_token_svc

        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache

        from src.api.dependencies.auth import get_current_user_id

        with pytest.raises(UnauthorizedError, match="无效的令牌类型"):
            await get_current_user_id(
                credentials=MagicMock(credentials="refresh_token"),
                token_service=mock_token_svc,
                cache_service=mock_cache,
            )

    @patch("src.api.dependencies.auth.get_token_service")
    @patch("src.api.dependencies.auth.get_cache_service")
    async def test_blacklisted_token_raises_unauthorized(self, mock_get_cache, mock_get_token):
        """黑名单中的令牌应抛出 UnauthorizedError。"""
        mock_token_svc = MagicMock()
        mock_token_svc.decode_token.return_value = {"sub": "user123", "type": "access"}
        mock_get_token.return_value = mock_token_svc

        mock_cache = AsyncMock()
        mock_cache.is_token_blacklisted.return_value = True
        mock_get_cache.return_value = mock_cache

        from src.api.dependencies.auth import get_current_user_id

        with pytest.raises(UnauthorizedError, match="令牌已失效"):
            await get_current_user_id(
                credentials=MagicMock(credentials="blacklisted_token"),
                token_service=mock_token_svc,
                cache_service=mock_cache,
            )

    @patch("src.api.dependencies.auth.get_token_service")
    @patch("src.api.dependencies.auth.get_cache_service")
    async def test_missing_sub_raises_unauthorized(self, mock_get_cache, mock_get_token):
        """缺少 sub 字段的令牌应抛出 UnauthorizedError。"""
        mock_token_svc = MagicMock()
        mock_token_svc.decode_token.return_value = {"type": "access"}
        mock_get_token.return_value = mock_token_svc

        mock_cache = AsyncMock()
        mock_cache.is_token_blacklisted.return_value = False
        mock_get_cache.return_value = mock_cache

        from src.api.dependencies.auth import get_current_user_id

        with pytest.raises(UnauthorizedError, match="无效的令牌负载"):
            await get_current_user_id(
                credentials=MagicMock(credentials="no_sub_token"),
                token_service=mock_token_svc,
                cache_service=mock_cache,
            )


@pytest.mark.unit
class TestGetCurrentActiveUser:
    """get_current_active_user 函数测试。"""

    async def test_cached_active_user_returns_info(self):
        """缓存中存在活跃用户应直接返回。"""
        mock_user_service = AsyncMock()
        mock_user_service.get_user_info_with_cache.return_value = UserEntity(
            id="1", username="test", password="", is_active=1, email="test@example.com", is_superuser=UserRole.USER
        )

        from src.api.dependencies.auth import get_current_active_user

        result = await get_current_active_user(user_id="1", user_service=mock_user_service)
        assert result.id == "1"
        mock_user_service.get_user_info_with_cache.assert_called_once_with("1")

    async def test_cached_inactive_user_raises(self):
        """缓存中用户被禁用应抛出 UnauthorizedError。"""
        mock_user_service = AsyncMock()
        mock_user_service.get_user_info_with_cache.side_effect = UnauthorizedError("用户账号已被禁用")

        from src.api.dependencies.auth import get_current_active_user

        with pytest.raises(UnauthorizedError, match="用户账号已被禁用"):
            await get_current_active_user(user_id="1", user_service=mock_user_service)

    async def test_cache_miss_user_found_returns_info(self):
        """缓存未命中且数据库中存在用户应返回用户信息。"""
        mock_user_service = AsyncMock()
        mock_user_service.get_user_info_with_cache.return_value = UserEntity(
            id="1", username="test", password="", is_active=1, email="test@example.com", is_superuser=UserRole.USER
        )

        from src.api.dependencies.auth import get_current_active_user

        result = await get_current_active_user(user_id="1", user_service=mock_user_service)
        assert result.id == "1"
        assert result.username == "test"

    async def test_cache_miss_user_not_found_raises(self):
        """缓存未命中且数据库中不存在用户应抛出 UnauthorizedError。"""
        mock_user_service = AsyncMock()
        mock_user_service.get_user_info_with_cache.side_effect = UnauthorizedError("用户不存在")

        from src.api.dependencies.auth import get_current_active_user

        with pytest.raises(UnauthorizedError, match="用户不存在"):
            await get_current_active_user(user_id="nonexistent", user_service=mock_user_service)


@pytest.mark.unit
class TestRequirePermission:
    """require_permission 依赖工厂测试。"""

    async def test_superuser_bypasses_check(self):
        """超级用户应绕过权限检查。"""
        mock_user_service = AsyncMock()
        mock_user_service.check_permission_cached_or_db.return_value = UserEntity(
            id="1", username="", password="", is_superuser=UserRole.SUPERUSER
        )

        from src.api.dependencies.auth import require_permission

        checker = require_permission("system:read")
        result = await checker(
            current_user=UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER),
            user_service=mock_user_service,
        )
        assert result.is_superuser == UserRole.SUPERUSER

    async def test_cache_hit_has_permission(self):
        """缓存命中且拥有权限应返回用户。"""
        mock_user_service = AsyncMock()
        mock_user_service.check_permission_cached_or_db.return_value = UserEntity(
            id="1", username="", password="", is_superuser=UserRole.USER
        )

        from src.api.dependencies.auth import require_permission

        checker = require_permission("system:read")
        result = await checker(
            current_user=UserEntity(id="1", username="user", password="", is_superuser=UserRole.USER),
            user_service=mock_user_service,
        )
        assert result.id == "1"

    async def test_cache_hit_no_permission_raises(self):
        """缓存命中但无权限应抛出 ForbiddenError。"""
        mock_user_service = AsyncMock()
        mock_user_service.check_permission_cached_or_db.side_effect = ForbiddenError("权限 'system:read' 是必需的")

        from src.api.dependencies.auth import require_permission

        checker = require_permission("system:read")
        with pytest.raises(ForbiddenError, match="权限 'system:read' 是必需的"):
            await checker(
                current_user=UserEntity(id="1", username="user", password="", is_superuser=UserRole.USER),
                user_service=mock_user_service,
            )


@pytest.mark.unit
class TestRequireMenuPermission:
    """require_menu_permission 依赖工厂测试。"""

    async def test_superuser_bypasses_check(self):
        """超级用户应绕过API权限检查。"""
        mock_user_service = AsyncMock()
        mock_user_service.check_api_permission_cached_or_db.return_value = UserEntity(
            id="1", username="", password="", is_superuser=UserRole.SUPERUSER
        )

        from src.api.dependencies.auth import require_menu_permission

        checker = require_menu_permission("/api/test", "GET")
        result = await checker(
            current_user=UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER),
            user_service=mock_user_service,
        )
        assert result.is_superuser == UserRole.SUPERUSER

    async def test_cache_hit_has_permission(self):
        """缓存命中且拥有API权限应返回用户。"""
        mock_user_service = AsyncMock()
        mock_user_service.check_api_permission_cached_or_db.return_value = UserEntity(
            id="1", username="", password="", is_superuser=UserRole.USER
        )

        from src.api.dependencies.auth import require_menu_permission

        checker = require_menu_permission("/api/test", "GET")
        result = await checker(
            current_user=UserEntity(id="1", username="user", password="", is_superuser=UserRole.USER),
            user_service=mock_user_service,
        )
        assert result.id == "1"

    async def test_cache_hit_no_permission_raises(self):
        """缓存命中但无API权限应抛出 ForbiddenError。"""
        mock_user_service = AsyncMock()
        mock_user_service.check_api_permission_cached_or_db.side_effect = ForbiddenError(
            "API权限 'GET /api/test' 是必需的"
        )

        from src.api.dependencies.auth import require_menu_permission

        checker = require_menu_permission("/api/test", "GET")
        with pytest.raises(ForbiddenError, match="API权限 'GET /api/test' 是必需的"):
            await checker(
                current_user=UserEntity(id="1", username="user", password="", is_superuser=UserRole.USER),
                user_service=mock_user_service,
            )


@pytest.mark.unit
class TestRequireSuperuser:
    """require_superuser 依赖工厂测试。"""

    async def test_superuser_passes(self):
        """超级用户应通过检查。"""
        from src.api.dependencies.auth import require_superuser

        checker = require_superuser()
        result = await checker(
            current_user=UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER)
        )
        assert result.is_superuser == UserRole.SUPERUSER

    async def test_non_superuser_raises(self):
        """非超级用户应抛出 ForbiddenError。"""
        from src.api.dependencies.auth import require_superuser

        checker = require_superuser()
        with pytest.raises(ForbiddenError, match="需要超级用户权限"):
            await checker(current_user=UserEntity(id="1", username="user", password="", is_superuser=UserRole.USER))
