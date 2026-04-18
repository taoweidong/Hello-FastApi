"""认证服务的单元测试。"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.dto.auth_dto import LoginDTO, RegisterDTO
from src.application.services.auth_service import AuthService
from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.entities.role import RoleEntity
from src.domain.entities.user import UserEntity
from src.domain.exceptions import BusinessError, UnauthorizedError
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService


TEST_SECRET_KEY = "test-secret-key-for-auth-testing"
TEST_ALGORITHM = "HS256"


@pytest.mark.unit
class TestAuthService:
    """AuthService 测试类。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_menu_repo(self):
        return AsyncMock()

    @pytest.fixture
    def token_service(self):
        return TokenService(secret_key=TEST_SECRET_KEY, algorithm=TEST_ALGORITHM, access_expire_minutes=30, refresh_expire_days=7)

    @pytest.fixture
    def mock_password_service(self):
        service = MagicMock(spec=PasswordService)
        service.verify_password = MagicMock(return_value=True)
        service.hash_password = MagicMock(return_value="hashed_password")
        return service

    @pytest.fixture
    def mock_cache_service(self):
        return AsyncMock()

    @pytest.fixture
    def auth_service(self, mock_user_repo, mock_role_repo, mock_menu_repo, token_service, mock_password_service, mock_cache_service):
        return AuthService(user_repo=mock_user_repo, role_repo=mock_role_repo, menu_repo=mock_menu_repo, token_service=token_service, password_service=mock_password_service, cache_service=mock_cache_service)

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user_repo, mock_role_repo, mock_menu_repo):
        """测试登录成功。"""
        user = UserEntity(id="user-1", username="testuser", password="hashed", is_active=1, nickname="测试", avatar="a.png")
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[RoleEntity(id="r1", name="admin", code="admin")])
        mock_menu_repo.get_all = AsyncMock(return_value=[])

        dto = LoginDTO(username="testuser", password="TestPass123")
        result = await auth_service.login(dto)

        assert result["username"] == "testuser"
        assert result["nickname"] == "测试"
        assert "accessToken" in result
        assert "refreshToken" in result
        assert "expires" in result

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service, mock_user_repo):
        """测试登录时用户不存在。"""
        mock_user_repo.get_by_username = AsyncMock(return_value=None)

        dto = LoginDTO(username="nonexistent", password="TestPass123")
        with pytest.raises(UnauthorizedError) as exc_info:
            await auth_service.login(dto)
        assert "密码错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service, mock_user_repo, mock_password_service):
        """测试登录时密码错误。"""
        user = UserEntity(id="user-1", username="testuser", password="hashed", is_active=1)
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_password_service.verify_password = MagicMock(return_value=False)

        dto = LoginDTO(username="testuser", password="WrongPass123")
        with pytest.raises(UnauthorizedError) as exc_info:
            await auth_service.login(dto)
        assert "密码错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, auth_service, mock_user_repo, mock_password_service):
        """测试登录时用户被禁用。"""
        user = UserEntity(id="user-1", username="testuser", password="hashed", is_active=0)
        mock_user_repo.get_by_username = AsyncMock(return_value=user)

        dto = LoginDTO(username="testuser", password="TestPass123")
        with pytest.raises(UnauthorizedError) as exc_info:
            await auth_service.login(dto)
        assert "禁用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_superuser(self, auth_service, mock_user_repo, mock_role_repo, mock_menu_repo):
        """测试超级用户登录。"""
        user = UserEntity(id="su-1", username="admin", password="hashed", is_active=1, is_superuser=1)
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        # get_all 返回 list[RoleEntity]
        mock_role_repo.get_all = AsyncMock(return_value=[RoleEntity(id="r1", name="admin", code="admin")])
        mock_menu_repo.get_all = AsyncMock(return_value=[])

        dto = LoginDTO(username="admin", password="TestPass123")
        result = await auth_service.login(dto)
        assert "accessToken" in result
        assert "admin" in result["roles"]

    @pytest.mark.asyncio
    async def test_register_success(self, auth_service, mock_user_repo, mock_password_service):
        """测试注册成功。"""
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        created = UserEntity(id="new-1", username="newuser", password="hashed", nickname="新用户", email="new@test.com", phone="123456", is_active=1)
        mock_user_repo.create = AsyncMock(return_value=created)

        dto = RegisterDTO(username="newuser", password="TestPass123", nickname="新用户", email="new@test.com", phone="123456")
        result = await auth_service.register(dto)

        assert result["username"] == "newuser"
        assert result["nickname"] == "新用户"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, auth_service, mock_user_repo):
        """测试注册时用户名重复。"""
        existing = UserEntity(id="ex-1", username="existing", password="hash")
        mock_user_repo.get_by_username = AsyncMock(return_value=existing)

        dto = RegisterDTO(username="existing", password="TestPass123")
        with pytest.raises(BusinessError) as exc_info:
            await auth_service.register(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_user_repo, token_service):
        """测试刷新令牌成功。"""
        # 先创建一个刷新令牌
        refresh_token = token_service.create_refresh_token({"sub": "user-1", "username": "testuser"})
        user = UserEntity(id="user-1", username="testuser", password="hash", is_active=1)
        mock_user_repo.get_by_id = AsyncMock(return_value=user)

        result = await auth_service.refresh_token(refresh_token)
        assert "accessToken" in result
        assert "refreshToken" in result
        assert "expires" in result

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service):
        """测试刷新无效令牌。"""
        with pytest.raises(UnauthorizedError):
            await auth_service.refresh_token("invalid-token")

    @pytest.mark.asyncio
    async def test_refresh_token_wrong_type(self, auth_service, token_service):
        """测试使用访问令牌刷新。"""
        access_token = token_service.create_access_token({"sub": "user-1"})
        with pytest.raises(UnauthorizedError) as exc_info:
            await auth_service.refresh_token(access_token)
        assert "类型" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_token_user_inactive(self, auth_service, mock_user_repo, token_service):
        """测试刷新令牌时用户被禁用。"""
        refresh_token = token_service.create_refresh_token({"sub": "user-1"})
        user = UserEntity(id="user-1", username="testuser", password="hash", is_active=0)
        mock_user_repo.get_by_id = AsyncMock(return_value=user)

        with pytest.raises(UnauthorizedError):
            await auth_service.refresh_token(refresh_token)

    @pytest.mark.asyncio
    async def test_logout_with_cache(self, auth_service, mock_cache_service, token_service):
        """测试登出（有缓存服务）。"""
        access_token = token_service.create_access_token({"sub": "user-1"})
        mock_cache_service.add_token_to_blacklist = AsyncMock(return_value=True)

        result = await auth_service.logout(access_token)
        assert result is True

    @pytest.mark.asyncio
    async def test_logout_without_cache(self, mock_user_repo, mock_role_repo, mock_menu_repo, token_service, mock_password_service):
        """测试登出（无缓存服务）。"""
        service = AuthService(user_repo=mock_user_repo, role_repo=mock_role_repo, menu_repo=mock_menu_repo, token_service=token_service, password_service=mock_password_service, cache_service=None)

        result = await service.logout("any-token")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_async_routes_superuser(self, auth_service, mock_user_repo, mock_menu_repo):
        """测试超级用户获取动态路由。"""
        user = UserEntity(id="su-1", username="admin", password="hash", is_superuser=1)
        mock_user_repo.get_by_id = AsyncMock(return_value=user)
        meta = MenuMetaEntity(id="m1", title="首页")
        menus = [
            MenuEntity(id="1", name="home", menu_type=0, path="/home", rank=1, meta=meta),
            MenuEntity(id="2", name="about", menu_type=1, path="/about", rank=2, parent_id="1", meta=meta),
        ]
        mock_menu_repo.get_all = AsyncMock(return_value=menus)

        routes = await auth_service.get_async_routes("su-1")
        assert len(routes) >= 1

    @pytest.mark.asyncio
    async def test_get_async_routes_user_not_found(self, auth_service, mock_user_repo):
        """测试获取不存在用户的动态路由。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)
        routes = await auth_service.get_async_routes("non-existent")
        assert routes == []

    def test_build_route_tree(self, auth_service):
        """测试构建路由树。"""
        meta1 = MenuMetaEntity(id="m1", title="根菜单", icon="home")
        meta2 = MenuMetaEntity(id="m2", title="子菜单", icon="user")
        menus = [
            MenuEntity(id="1", name="root", menu_type=0, path="/root", rank=1, meta=meta1),
            MenuEntity(id="2", name="child", menu_type=1, path="/child", rank=2, parent_id="1", meta=meta2),
        ]
        tree = auth_service._build_route_tree(menus)
        assert len(tree) == 1
        assert tree[0]["name"] == "root"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["name"] == "child"

    def test_build_meta_with_meta(self, auth_service):
        """测试构建meta对象（有meta数据）。"""
        meta = MenuMetaEntity(id="m1", title="测试", icon="home", r_svg_name="ri-home", is_show_menu=1, is_show_parent=1, is_keepalive=1, frame_url="http://x.com", frame_loading=1, transition_enter="fade", transition_leave="slide", is_hidden_tag=1, fixed_tag=1, dynamic_level=2)
        menu = MenuEntity(id="1", name="test", meta=meta)
        result = auth_service._build_meta(menu)

        assert result["title"] == "测试"
        assert result["icon"] == "home"
        assert result["showLink"] is True
        assert result["transition"]["enter"] == "fade"
        assert result["dynamicLevel"] == 2

    def test_build_meta_without_meta(self, auth_service):
        """测试构建meta对象（无meta数据）。"""
        menu = MenuEntity(id="1", name="test", meta=None)
        result = auth_service._build_meta(menu)

        assert result["title"] == "test"
        assert result["showLink"] is True
        assert result["keepAlive"] is False
