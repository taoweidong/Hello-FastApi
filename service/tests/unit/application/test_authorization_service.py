"""AuthorizationService（授权服务）单元测试。

自 test_user_service.py 拆出：权限校验与当前用户解析属授权领域，
与用户 CRUD 按变更轴分离。
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.application.services.authorization_service import AuthorizationService
from src.domain.entities.menu import MenuEntity
from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole, UserStatus
from src.domain.exceptions import ForbiddenError, UnauthorizedError


@pytest.mark.unit
class TestAuthorizationServiceGetUserInfoWithCache:
    """AuthorizationService.get_user_info_with_cache 测试类 — 覆盖所有缓存路径。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def authz_cached(self, mock_user_repo, mock_role_repo, mock_cache):
        return AuthorizationService(user_repo=mock_user_repo, role_repo=mock_role_repo, cache_service=mock_cache)

    @pytest.fixture
    def authz_no_cache(self, mock_user_repo, mock_role_repo):
        return AuthorizationService(user_repo=mock_user_repo, role_repo=mock_role_repo, cache_service=None)

    @pytest.mark.asyncio
    async def test_cache_hit_active(self, authz_cached, mock_cache, mock_user_repo):
        """L243-255：缓存命中 + 活跃用户 → 从缓存返回。"""
        cached_info = {
            "id": "u1",
            "username": "cached_user",
            "email": "cached@test.com",
            "is_superuser": UserRole.USER,
            "is_active": UserStatus.ACTIVE,
        }
        mock_cache.get_user_info = AsyncMock(return_value=cached_info)

        with patch.object(authz_cached, "cache_service", mock_cache):
            result = await authz_cached.get_user_info_with_cache("u1")

        assert result.username == "cached_user"
        assert result.is_active == UserStatus.ACTIVE
        mock_user_repo.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_hit_inactive(self, authz_cached, mock_cache):
        """L246-247：缓存命中 + 不活跃 → 抛 UnauthorizedError。"""
        cached_info = {
            "id": "u1",
            "username": "disabled_user",
            "email": "",
            "is_superuser": UserRole.USER,
            "is_active": 0,
        }
        mock_cache.get_user_info = AsyncMock(return_value=cached_info)

        with patch.object(authz_cached, "cache_service", mock_cache), pytest.raises(UnauthorizedError) as exc_info:
            await authz_cached.get_user_info_with_cache("u1")
        assert "禁用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_miss_db_hit_active(self, authz_cached, mock_cache, mock_user_repo):
        """L257-272：缓存未命中 + DB命中 + 活跃 → 写缓存并返回。"""
        mock_cache.get_user_info = AsyncMock(return_value=None)
        test_user = UserEntity.create_new(
            username="db_user", hashed_password="hashed", email="db@test.com", is_active=1
        )
        test_user.id = "u1"
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

        with (
            patch.object(authz_cached, "cache_service", mock_cache),
            patch.object(authz_cached, "user_repo", mock_user_repo),
        ):
            result = await authz_cached.get_user_info_with_cache("u1")

        assert result.username == "db_user"
        assert result.is_active == 1
        mock_cache.set_user_info.assert_called_once()
        call_args = mock_cache.set_user_info.call_args[0]
        assert call_args[0] == "u1"
        assert call_args[1]["username"] == "db_user"

    @pytest.mark.asyncio
    async def test_cache_miss_db_miss(self, authz_cached, mock_cache, mock_user_repo):
        """L258-259：缓存未命中 + DB未命中 → 抛 UnauthorizedError。"""
        mock_cache.get_user_info = AsyncMock(return_value=None)
        mock_user_repo.get_by_id = AsyncMock(return_value=None)

        with (
            patch.object(authz_cached, "cache_service", mock_cache),
            patch.object(authz_cached, "user_repo", mock_user_repo),
            pytest.raises(UnauthorizedError) as exc_info,
        ):
            await authz_cached.get_user_info_with_cache("u1")
        assert "不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_miss_db_hit_inactive(self, authz_cached, mock_cache, mock_user_repo):
        """L260-261：缓存未命中 + DB命中 + 不活跃 → 抛 UnauthorizedError。"""
        mock_cache.get_user_info = AsyncMock(return_value=None)
        test_user = UserEntity.create_new(username="disabled_user", hashed_password="hashed", is_active=0)
        test_user.id = "u1"
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

        with (
            patch.object(authz_cached, "cache_service", mock_cache),
            patch.object(authz_cached, "user_repo", mock_user_repo),
            pytest.raises(UnauthorizedError) as exc_info,
        ):
            await authz_cached.get_user_info_with_cache("u1")
        assert "禁用" in str(exc_info.value)
        mock_cache.set_user_info.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_cache_skip_cache_db_hit(self, authz_no_cache, mock_user_repo):
        """L243/L270：无 cache_service → 跳过缓存，直接查 DB。"""
        test_user = UserEntity.create_new(username="nocache_user", hashed_password="hashed", is_active=1)
        test_user.id = "u1"
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

        with patch.object(authz_no_cache, "user_repo", mock_user_repo):
            result = await authz_no_cache.get_user_info_with_cache("u1")

        assert result.username == "nocache_user"


@pytest.mark.unit
class TestAuthorizationServiceCheckPermissionCachedOrDb:
    """AuthorizationService.check_permission_cached_or_db 测试类 — 覆盖所有路径。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def authz_cached(self, mock_user_repo, mock_role_repo, mock_cache):
        return AuthorizationService(user_repo=mock_user_repo, role_repo=mock_role_repo, cache_service=mock_cache)

    @pytest.fixture
    def authz_no_cache(self, mock_user_repo, mock_role_repo):
        return AuthorizationService(user_repo=mock_user_repo, role_repo=mock_role_repo, cache_service=None)

    @pytest.mark.asyncio
    async def test_superuser_fastpath(self, authz_cached, mock_cache):
        """L281-284：超级用户快捷路径 → 返回 SUPERUSER 实体。"""
        result = await authz_cached.check_permission_cached_or_db("u1", UserRole.SUPERUSER, "some:permission")
        assert result.is_superuser == UserRole.SUPERUSER
        assert result.id == "u1"

    @pytest.mark.asyncio
    async def test_cache_hit_permission_found(self, authz_cached, mock_cache):
        """L286-293：缓存命中 + 权限存在 → 返回 USER 实体。"""
        mock_cache.get_user_permissions = AsyncMock(
            return_value=[{"type": "permission", "name": "user:add"}, {"type": "permission", "name": "user:delete"}]
        )

        with patch.object(authz_cached, "cache_service", mock_cache):
            result = await authz_cached.check_permission_cached_or_db("u1", UserRole.USER, "user:add")

        assert result.is_superuser == UserRole.USER

    @pytest.mark.asyncio
    async def test_cache_hit_permission_not_found(self, authz_cached, mock_cache):
        """L294：缓存命中 + 权限不存在 → 抛 ForbiddenError。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=[{"type": "permission", "name": "user:view"}])

        with patch.object(authz_cached, "cache_service", mock_cache), pytest.raises(ForbiddenError) as exc_info:
            await authz_cached.check_permission_cached_or_db("u1", UserRole.USER, "user:delete")
        assert "必需" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_miss_db_permission_found(self, authz_cached, mock_user_repo, mock_role_repo, mock_cache):
        """L296-312：缓存未命中 + DB 查菜单 + 权限存在 → 写缓存 + 返回 USER。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)

        perm_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:add", rank=1, path=None, method=None
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[perm_menu])

        with (
            patch.object(authz_cached, "cache_service", mock_cache),
            patch.object(authz_cached, "role_repo", mock_role_repo),
        ):
            result = await authz_cached.check_permission_cached_or_db("u1", UserRole.USER, "user:add")

        assert result.is_superuser == UserRole.USER
        mock_cache.set_user_permissions.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_db_permission_not_found(self, authz_cached, mock_role_repo, mock_cache):
        """L314：缓存未命中 + DB 查菜单 + 无权限 → 抛 ForbiddenError。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)
        view_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:view", rank=1, path=None, method=None
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[view_menu])

        with (
            patch.object(authz_cached, "cache_service", mock_cache),
            patch.object(authz_cached, "role_repo", mock_role_repo),
            pytest.raises(ForbiddenError) as exc_info,
        ):
            await authz_cached.check_permission_cached_or_db("u1", UserRole.USER, "user:delete")
        assert "必需" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_cache_skip_and_db_hit(self, authz_no_cache, mock_role_repo):
        """L296 + L306：无 cache_service → 查 DB 权限并成功返回。"""
        perm_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="system:config", rank=1, path=None, method=None
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[perm_menu])

        with patch.object(authz_no_cache, "role_repo", mock_role_repo):
            result = await authz_no_cache.check_permission_cached_or_db("u1", UserRole.USER, "system:config")

        assert result.is_superuser == UserRole.USER


@pytest.mark.unit
class TestAuthorizationServiceCheckAPIPermissionCachedOrDb:
    """UserService.check_api_permission_cached_or_db 测试类 — 覆盖所有路径。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def authz_cached(self, mock_user_repo, mock_role_repo, mock_cache):
        return AuthorizationService(user_repo=mock_user_repo, role_repo=mock_role_repo, cache_service=mock_cache)

    @pytest.fixture
    def authz_no_cache(self, mock_user_repo, mock_role_repo):
        return AuthorizationService(user_repo=mock_user_repo, role_repo=mock_role_repo, cache_service=None)

    @pytest.mark.asyncio
    async def test_superuser_fastpath(self, authz_cached, mock_cache):
        """L323-326：超级用户快捷路径 → 返回 SUPERUSER 实体。"""
        result = await authz_cached.check_api_permission_cached_or_db("u1", UserRole.SUPERUSER, "/api/users", "GET")
        assert result.is_superuser == UserRole.SUPERUSER
        assert result.id == "u1"

    @pytest.mark.asyncio
    async def test_cache_hit_api_perm_found(self, authz_cached, mock_cache):
        """L328-335：缓存命中 + 匹配 API 权限 → 返回 USER 实体。"""
        mock_cache.get_user_permissions = AsyncMock(
            return_value=[
                {"type": "api", "path": "/api/users", "method": "GET", "name": "user:list"},
                {"type": "api", "path": "/api/users", "method": "POST", "name": "user:add"},
            ]
        )

        with patch.object(authz_cached, "cache_service", mock_cache):
            result = await authz_cached.check_api_permission_cached_or_db("u1", UserRole.USER, "/api/users", "GET")

        assert result.is_superuser == UserRole.USER

    @pytest.mark.asyncio
    async def test_cache_hit_api_perm_not_found(self, authz_cached, mock_cache):
        """L336：缓存命中 + 无匹配 API 权限 → 抛 ForbiddenError。"""
        mock_cache.get_user_permissions = AsyncMock(
            return_value=[{"type": "api", "path": "/api/users", "method": "GET", "name": "user:list"}]
        )

        with patch.object(authz_cached, "cache_service", mock_cache), pytest.raises(ForbiddenError) as exc_info:
            await authz_cached.check_api_permission_cached_or_db("u1", UserRole.USER, "/api/users", "DELETE")
        assert "必需" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_miss_db_api_perm_found(self, authz_cached, mock_user_repo, mock_role_repo, mock_cache):
        """L338-357：缓存未命中 + DB 查菜单 + 匹配 API 权限 → 写缓存 + 返回 USER。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)

        api_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:list", rank=1, path="/api/users", method="GET"
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[api_menu])

        with (
            patch.object(authz_cached, "cache_service", mock_cache),
            patch.object(authz_cached, "role_repo", mock_role_repo),
        ):
            result = await authz_cached.check_api_permission_cached_or_db("u1", UserRole.USER, "/api/users", "GET")

        assert result.is_superuser == UserRole.USER
        mock_cache.set_user_permissions.assert_called_once()
        call_args = mock_cache.set_user_permissions.call_args[0]
        perms = call_args[1]
        assert any(p.get("type") == "api" and p.get("path") == "/api/users" for p in perms)

    @pytest.mark.asyncio
    async def test_cache_miss_db_api_perm_not_found(self, authz_cached, mock_role_repo, mock_cache):
        """L359：缓存未命中 + DB 查菜单 + 不匹配 → 抛 ForbiddenError。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)
        api_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:list", rank=1, path="/api/users", method="GET"
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[api_menu])

        with (
            patch.object(authz_cached, "cache_service", mock_cache),
            patch.object(authz_cached, "role_repo", mock_role_repo),
            pytest.raises(ForbiddenError) as exc_info,
        ):
            await authz_cached.check_api_permission_cached_or_db("u1", UserRole.USER, "/api/users", "DELETE")
        assert "必需" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_cache_skip_and_db_hit(self, authz_no_cache, mock_role_repo):
        """L338 + L351：无 cache_service → 查 DB 权限并成功返回。"""
        api_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="system:list", rank=1, path="/api/system", method="GET"
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[api_menu])

        with patch.object(authz_no_cache, "role_repo", mock_role_repo):
            result = await authz_no_cache.check_api_permission_cached_or_db("u1", UserRole.USER, "/api/system", "GET")

        assert result.is_superuser == UserRole.USER

    @pytest.mark.asyncio
    async def test_cache_miss_db_no_path_method(self, authz_cached, mock_role_repo, mock_cache):
        """L343-349：缓存未命中 + DB 菜单无 path/method → fallback permission entry。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)
        perm_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:view", rank=1, path=None, method=None
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[perm_menu])

        with (
            patch.object(authz_cached, "cache_service", mock_cache),
            patch.object(authz_cached, "role_repo", mock_role_repo),
            pytest.raises(ForbiddenError),
        ):
            await authz_cached.check_api_permission_cached_or_db("u1", UserRole.USER, "/api/users", "GET")
