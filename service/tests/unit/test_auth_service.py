"""认证服务的单元测试。"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.dto.auth_dto import LoginDTO, RegisterDTO
from src.application.services.auth_service import AuthService, LoginRequestInfo
from src.domain.entities.log import LoginLogEntity
from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.entities.role import RoleEntity
from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole
from src.domain.exceptions import BusinessError, NotFoundError, UnauthorizedError
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
        return TokenService(
            secret_key=TEST_SECRET_KEY, algorithm=TEST_ALGORITHM, access_expire_minutes=30, refresh_expire_days=7
        )

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
    def mock_log_repo(self):
        return AsyncMock()

    @pytest.fixture
    def auth_service(
        self, mock_user_repo, mock_role_repo, mock_menu_repo, token_service, mock_password_service, mock_cache_service
    ):
        return AuthService(
            user_repo=mock_user_repo,
            role_repo=mock_role_repo,
            menu_repo=mock_menu_repo,
            token_service=token_service,
            password_service=mock_password_service,
            cache_service=mock_cache_service,
        )

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user_repo, mock_role_repo, mock_menu_repo):
        """测试登录成功。"""
        user = UserEntity(
            id="user-1", username="testuser", password="hashed", is_active=1, nickname="测试", avatar="a.png"
        )
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
    async def test_login_superuser(
        self, auth_service, mock_user_repo, mock_role_repo, mock_menu_repo, mock_cache_service
    ):
        """测试超级用户登录。"""
        user = UserEntity(id="su-1", username="admin", password="hashed", is_active=1, is_superuser=UserRole.SUPERUSER)
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        # get_all 返回 list[RoleEntity]
        mock_role_repo.get_all = AsyncMock(return_value=[RoleEntity(id="r1", name="admin", code="admin")])
        mock_menu_repo.get_all = AsyncMock(return_value=[])
        # 缓存未命中，走数据库查询
        mock_cache_service.get_all_menus = AsyncMock(return_value=None)

        dto = LoginDTO(username="admin", password="TestPass123")
        result = await auth_service.login(dto)
        assert "accessToken" in result
        assert "admin" in result["roles"]

    @pytest.mark.asyncio
    async def test_register_success(self, auth_service, mock_user_repo, mock_password_service):
        """测试注册成功。"""
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        created = UserEntity(
            id="new-1",
            username="newuser",
            password="hashed",
            nickname="新用户",
            email="new@test.com",
            phone="123456",
            is_active=1,
        )
        mock_user_repo.create = AsyncMock(return_value=created)

        dto = RegisterDTO(
            username="newuser", password="TestPass123", nickname="新用户", email="new@test.com", phone="123456"
        )
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
    async def test_logout_without_cache(
        self, mock_user_repo, mock_role_repo, mock_menu_repo, token_service, mock_password_service
    ):
        """测试登出（无缓存服务）。"""
        service = AuthService(
            user_repo=mock_user_repo,
            role_repo=mock_role_repo,
            menu_repo=mock_menu_repo,
            token_service=token_service,
            password_service=mock_password_service,
            cache_service=None,
        )

        result = await service.logout("any-token")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_async_routes_superuser(self, auth_service, mock_user_repo, mock_menu_repo, mock_cache_service):
        """测试超级用户获取动态路由。"""
        user = UserEntity(id="su-1", username="admin", password="hash", is_superuser=UserRole.SUPERUSER)
        mock_user_repo.get_by_id = AsyncMock(return_value=user)
        meta = MenuMetaEntity(id="m1", title="首页")
        menus = [
            MenuEntity(id="1", name="home", menu_type=0, path="/home", rank=1, meta=meta),
            MenuEntity(id="2", name="about", menu_type=1, path="/about", rank=2, parent_id="1", meta=meta),
        ]
        mock_menu_repo.get_all = AsyncMock(return_value=menus)
        # 缓存未命中，走数据库查询
        mock_cache_service.get_all_menus = AsyncMock(return_value=None)

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
        meta = MenuMetaEntity(
            id="m1",
            title="测试",
            icon="home",
            r_svg_name="ri-home",
            is_show_menu=1,
            is_show_parent=1,
            is_keepalive=1,
            frame_url="http://x.com",
            frame_loading=1,
            transition_enter="fade",
            transition_leave="slide",
            is_hidden_tag=1,
            fixed_tag=1,
            dynamic_level=2,
        )
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

    @pytest.mark.asyncio
    async def test_register_create_returns_none(self, auth_service, mock_user_repo, mock_password_service):
        """测试注册时 create 返回 None。"""
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        mock_user_repo.create = AsyncMock(return_value=None)

        dto = RegisterDTO(username="newuser", password="TestPass123", nickname="新用户")
        with pytest.raises(NotFoundError) as exc_info:
            await auth_service.register(dto)
        assert "无法加载" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, auth_service, mock_cache_service):
        """测试登出时无效的 token。"""
        result = await auth_service.logout("invalid-token")
        assert result is True

    @pytest.mark.asyncio
    async def test_logout_token_no_exp(self, auth_service, mock_cache_service, token_service):
        """测试登出时 token 没有 exp。"""
        from src.domain.services.token_service import TokenService

        # Create a token with zero expiry to avoid 'exp' claim
        minimal_service = TokenService(
            secret_key=TEST_SECRET_KEY, algorithm=TEST_ALGORITHM, access_expire_minutes=0, refresh_expire_days=0
        )
        token = minimal_service.create_access_token({"sub": "user-1"})
        # token has no 'exp' -> should return True without calling cache
        mock_cache_service.add_token_to_blacklist = AsyncMock(return_value=True)
        result = await auth_service.logout(token)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_async_routes_user(
        self, auth_service, mock_user_repo, mock_role_repo, mock_menu_repo, mock_cache_service
    ):
        """测试普通用户获取动态路由。"""
        user = UserEntity(id="u1", username="testuser", password="hash", is_active=1)
        mock_user_repo.get_by_id = AsyncMock(return_value=user)
        meta = MenuMetaEntity(id="m1", title="首页", is_show_menu=1, is_keepalive=1)
        menus = [MenuEntity(id="1", name="home", menu_type=0, path="/home", rank=0, meta=meta)]
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=menus)

        routes = await auth_service.get_async_routes("u1")
        assert len(routes) == 1
        assert routes[0]["name"] == "home"

    @pytest.mark.asyncio
    async def test_get_async_routes_normal_user(self, auth_service, mock_user_repo, mock_role_repo):
        """测试普通用户获取动态路由。"""
        user = UserEntity(id="u-1", username="normal", password="hash", is_superuser=0)
        mock_user_repo.get_by_id = AsyncMock(return_value=user)
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[])

        routes = await auth_service.get_async_routes("u-1")
        assert routes == []

    def test_build_route_tree_empty(self, auth_service):
        """测试构建空路由树。"""
        tree = auth_service._build_route_tree([])
        assert tree == []

    def test_build_route_tree_single(self, auth_service):
        """测试构建单节点路由树。"""
        meta = MenuMetaEntity(id="m1", title="首页", icon="home")
        menus = [MenuEntity(id="1", name="home", menu_type=0, path="/home", rank=1, meta=meta)]
        tree = auth_service._build_route_tree(menus)
        assert len(tree) == 1
        assert tree[0]["name"] == "home"
        assert "children" not in tree[0]

    def test_menu_entity_to_dict_with_meta(self, auth_service):
        """测试 _menu_entity_to_dict 含 meta。"""
        meta = MenuMetaEntity(
            id="m1",
            title="测试",
            icon="home",
            r_svg_name="ri-home",
            is_show_menu=1,
            is_show_parent=0,
            is_keepalive=1,
            frame_url="",
            frame_loading=1,
            transition_enter="",
            transition_leave="",
            is_hidden_tag=0,
            fixed_tag=0,
            dynamic_level=0,
        )
        menu = MenuEntity(
            id="1",
            name="test",
            menu_type=0,
            path="/test",
            rank=1,
            is_active=1,
            component="",
            method="",
            creator_id=None,
            modifier_id=None,
            parent_id=None,
            meta_id="m1",
            description=None,
            meta=meta,
        )
        result = auth_service._menu_entity_to_dict(menu)
        assert result["id"] == "1"
        assert result["name"] == "test"
        assert result["meta"]["title"] == "测试"
        assert result["meta"]["icon"] == "home"

    def test_menu_entity_to_dict_without_meta(self, auth_service):
        """测试 _menu_entity_to_dict 不含 meta。"""
        menu = MenuEntity(id="1", name="test", menu_type=0, path="/test", rank=1)
        result = auth_service._menu_entity_to_dict(menu)
        assert result["id"] == "1"
        assert "meta" not in result

    def test_menu_dict_to_entity_with_meta(self, auth_service):
        """测试 _menu_dict_to_entity 含 meta。"""
        data = {
            "id": "1",
            "menu_type": 0,
            "name": "test",
            "rank": 1,
            "path": "/test",
            "component": "",
            "is_active": 1,
            "method": "",
            "creator_id": None,
            "modifier_id": None,
            "parent_id": None,
            "meta_id": "m1",
            "created_time": None,
            "updated_time": None,
            "description": None,
            "meta": {
                "id": "m1",
                "title": "测试",
                "icon": "home",
                "r_svg_name": "",
                "is_show_menu": 1,
                "is_show_parent": 0,
                "is_keepalive": 0,
                "frame_url": "",
                "frame_loading": 1,
                "transition_enter": "",
                "transition_leave": "",
                "is_hidden_tag": 0,
                "fixed_tag": 0,
                "dynamic_level": 0,
            },
        }
        entity = auth_service._menu_dict_to_entity(data)
        assert entity.id == "1"
        assert entity.meta is not None
        assert entity.meta.title == "测试"

    def test_menu_dict_to_entity_without_meta(self, auth_service):
        """测试 _menu_dict_to_entity 不含 meta。"""
        data = {
            "id": "1",
            "menu_type": 0,
            "name": "test",
            "rank": 1,
            "path": "/test",
            "component": "",
            "is_active": 1,
            "method": "",
            "creator_id": None,
            "modifier_id": None,
            "parent_id": None,
            "meta_id": None,
            "created_time": None,
            "updated_time": None,
            "description": None,
        }
        entity = auth_service._menu_dict_to_entity(data)
        assert entity.id == "1"
        assert entity.meta is None

    @pytest.mark.asyncio
    async def test_refresh_token_no_sub_claim(self, auth_service, mock_user_repo, token_service):
        """测试刷新令牌时 payload 缺少 sub。"""
        from jose import jwt as pyjwt

        # Forge a refresh token with no "sub" claim but valid structure
        forged = pyjwt.encode({"type": "refresh", "exp": 9999999999}, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        with pytest.raises(UnauthorizedError):
            await auth_service.refresh_token(forged)

    @pytest.mark.asyncio
    async def test_logout_token_no_exp_claim(self, auth_service, mock_cache_service, token_service):
        """测试登出时 token 无 exp 声明。"""
        from jose import jwt as pyjwt

        forged = pyjwt.encode({"sub": "user-1", "type": "access"}, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        result = await auth_service.logout(forged)
        assert result is True

    def test_build_meta_partial(self, auth_service):
        """测试构建 meta 对象（只有部分字段）。"""
        meta = MenuMetaEntity(id="m1", title="部分")
        menu = MenuEntity(id="1", name="test", meta=meta)
        result = auth_service._build_meta(menu)
        assert result["title"] == "部分"
        assert result["icon"] == ""
        assert result["transition"] == {}

    @pytest.mark.asyncio
    async def test_login_superuser_cached_menus(
        self, auth_service, mock_user_repo, mock_role_repo, mock_menu_repo, mock_cache_service
    ):
        """测试超级用户登录时菜单从缓存读取。"""
        user = UserEntity(id="su-1", username="admin", password="hashed", is_active=1, is_superuser=UserRole.SUPERUSER)
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_role_repo.get_all = AsyncMock(return_value=[RoleEntity(id="r1", name="admin", code="admin")])
        cached_menus = [
            {
                "id": "1",
                "menu_type": 2,
                "name": "btn:add",
                "rank": 1,
                "path": "",
                "component": "",
                "is_active": 1,
                "method": "",
                "creator_id": None,
                "modifier_id": None,
                "parent_id": "p1",
                "meta_id": None,
                "created_time": None,
                "updated_time": None,
                "description": None,
            }
        ]
        mock_cache_service.get_all_menus = AsyncMock(return_value=cached_menus)

        dto = LoginDTO(username="admin", password="TestPass123")
        result = await auth_service.login(dto)
        assert "accessToken" in result
        assert "btn:add" in result["permissions"]

    # ── 登录日志与在线会话登记 ──

    def _service_with_log_repo(
        self,
        mock_user_repo,
        mock_role_repo,
        mock_menu_repo,
        token_service,
        mock_password_service,
        mock_cache_service,
        mock_log_repo,
    ):
        """构造注入日志仓储的服务实例。"""
        return AuthService(
            user_repo=mock_user_repo,
            role_repo=mock_role_repo,
            menu_repo=mock_menu_repo,
            token_service=token_service,
            password_service=mock_password_service,
            cache_service=mock_cache_service,
            log_repo=mock_log_repo,
        )

    @pytest.mark.asyncio
    async def test_login_writes_log_and_registers_session(
        self,
        mock_user_repo,
        mock_role_repo,
        mock_menu_repo,
        token_service,
        mock_password_service,
        mock_cache_service,
        mock_log_repo,
    ):
        """登录成功时写入登录日志并登记在线会话。"""
        user = UserEntity(
            id="user-1", username="testuser", password="hashed", is_active=1, nickname="测试", avatar="a.png"
        )
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[RoleEntity(id="r1", name="admin", code="admin")])
        mock_menu_repo.get_all = AsyncMock(return_value=[])
        service = self._service_with_log_repo(
            mock_user_repo,
            mock_role_repo,
            mock_menu_repo,
            token_service,
            mock_password_service,
            mock_cache_service,
            mock_log_repo,
        )

        dto = LoginDTO(username="testuser", password="TestPass123")
        request_info = LoginRequestInfo(
            client_ip="127.0.0.1",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        result = await service.login(dto, request_info)

        # 登录日志：状态/账号/IP/浏览器/系统/创建人/登录类型
        mock_log_repo.create_login_log.assert_awaited_once()
        entity = mock_log_repo.create_login_log.await_args.args[0]
        assert isinstance(entity, LoginLogEntity)
        assert entity.status == 1
        assert entity.username == "testuser"
        assert entity.ipaddress == "127.0.0.1"
        assert entity.browser == "Chrome"
        assert entity.system == "Windows"
        assert entity.login_type == 0
        assert entity.creator_id == "user-1"
        assert entity.description == "登录成功"

        # 在线会话：session_key 与 Token 哈希一致，信息字段完整
        mock_cache_service.set_online_user.assert_awaited_once()
        session_key, info, expires_at = mock_cache_service.set_online_user.await_args.args
        assert session_key == token_service.hash_token(result["accessToken"])
        assert info["userId"] == "user-1"
        assert info["username"] == "testuser"
        assert info["ip"] == "127.0.0.1"
        assert info["browser"] == "Chrome"
        assert info["system"] == "Windows"
        assert info["loginTime"]
        assert info["expiresAt"]

    @pytest.mark.asyncio
    async def test_login_without_request_info_unknown_fields(
        self,
        mock_user_repo,
        mock_role_repo,
        mock_menu_repo,
        token_service,
        mock_password_service,
        mock_cache_service,
        mock_log_repo,
    ):
        """未提供请求信息时日志与会话使用 unknown/None 兜底。"""
        user = UserEntity(id="user-1", username="testuser", password="hashed", is_active=1)
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])
        mock_menu_repo.get_all = AsyncMock(return_value=[])
        service = self._service_with_log_repo(
            mock_user_repo,
            mock_role_repo,
            mock_menu_repo,
            token_service,
            mock_password_service,
            mock_cache_service,
            mock_log_repo,
        )

        dto = LoginDTO(username="testuser", password="TestPass123")
        await service.login(dto)

        entity = mock_log_repo.create_login_log.await_args.args[0]
        assert entity.status == 1
        assert entity.ipaddress is None
        assert entity.browser == "unknown"
        assert entity.system == "unknown"
        _, info, _ = mock_cache_service.set_online_user.await_args.args
        assert info["ip"] is None
        assert info["browser"] == "unknown"
        assert info["system"] == "unknown"

    @pytest.mark.asyncio
    async def test_login_failure_writes_failed_log(
        self,
        mock_user_repo,
        mock_role_repo,
        mock_menu_repo,
        token_service,
        mock_password_service,
        mock_cache_service,
        mock_log_repo,
    ):
        """认证失败时写入 status=0 日志且不登记在线会话。"""
        user = UserEntity(id="user-1", username="testuser", password="hashed", is_active=1)
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_password_service.verify_password = MagicMock(return_value=False)
        service = self._service_with_log_repo(
            mock_user_repo,
            mock_role_repo,
            mock_menu_repo,
            token_service,
            mock_password_service,
            mock_cache_service,
            mock_log_repo,
        )

        dto = LoginDTO(username="testuser", password="WrongPass123")
        with pytest.raises(UnauthorizedError):
            await service.login(dto)

        mock_log_repo.create_login_log.assert_awaited_once()
        entity = mock_log_repo.create_login_log.await_args.args[0]
        assert entity.status == 0
        assert entity.username == "testuser"
        assert entity.creator_id is None
        mock_cache_service.set_online_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_log_repo_error_degraded(
        self,
        mock_user_repo,
        mock_role_repo,
        mock_menu_repo,
        token_service,
        mock_password_service,
        mock_cache_service,
        mock_log_repo,
    ):
        """日志仓储异常时登录流程降级不阻断。"""
        user = UserEntity(id="user-1", username="testuser", password="hashed", is_active=1)
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])
        mock_menu_repo.get_all = AsyncMock(return_value=[])
        mock_log_repo.create_login_log = AsyncMock(side_effect=Exception("数据库连接失败"))
        service = self._service_with_log_repo(
            mock_user_repo,
            mock_role_repo,
            mock_menu_repo,
            token_service,
            mock_password_service,
            mock_cache_service,
            mock_log_repo,
        )

        dto = LoginDTO(username="testuser", password="TestPass123")
        result = await service.login(dto)
        assert "accessToken" in result

    @pytest.mark.asyncio
    async def test_login_session_cache_error_degraded(
        self,
        mock_user_repo,
        mock_role_repo,
        mock_menu_repo,
        token_service,
        mock_password_service,
        mock_cache_service,
        mock_log_repo,
    ):
        """在线会话登记异常时登录流程降级不阻断。"""
        user = UserEntity(id="user-1", username="testuser", password="hashed", is_active=1)
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])
        mock_menu_repo.get_all = AsyncMock(return_value=[])
        mock_cache_service.set_online_user = AsyncMock(side_effect=Exception("Redis 连接失败"))
        service = self._service_with_log_repo(
            mock_user_repo,
            mock_role_repo,
            mock_menu_repo,
            token_service,
            mock_password_service,
            mock_cache_service,
            mock_log_repo,
        )

        dto = LoginDTO(username="testuser", password="TestPass123")
        result = await service.login(dto)
        assert "accessToken" in result
        mock_log_repo.create_login_log.assert_awaited_once()

    # ── 个人安全日志（mine-logs） ──

    @pytest.mark.asyncio
    async def test_get_mine_logs_returns_user_records(
        self,
        mock_user_repo,
        mock_role_repo,
        mock_menu_repo,
        token_service,
        mock_password_service,
        mock_cache_service,
        mock_log_repo,
    ):
        """按当前用户名过滤查询最近登录记录并透传分页参数。"""
        logs = [
            LoginLogEntity(
                id="log-1",
                status=1,
                username="testuser",
                ipaddress="127.0.0.1",
                browser="Chrome",
                system="Windows",
                created_time=datetime(2026, 8, 23, 10, 0, 0),
            ),
            LoginLogEntity(
                id="log-2",
                status=0,
                username="testuser",
                ipaddress="10.0.0.1",
                created_time=datetime(2026, 8, 22, 9, 0, 0),
            ),
        ]
        mock_log_repo.get_login_logs = AsyncMock(return_value=(logs, 2))
        service = self._service_with_log_repo(
            mock_user_repo,
            mock_role_repo,
            mock_menu_repo,
            token_service,
            mock_password_service,
            mock_cache_service,
            mock_log_repo,
        )

        result, total = await service.get_mine_logs(username="testuser", page_num=1, page_size=10)

        assert total == 2
        assert result == logs
        mock_log_repo.get_login_logs.assert_awaited_once_with(page_num=1, page_size=10, username="testuser")

    @pytest.mark.asyncio
    async def test_get_mine_logs_empty_without_log_repo(self, auth_service):
        """未注入日志仓储时返回空列表，不抛异常。"""
        result, total = await auth_service.get_mine_logs(username="testuser")
        assert result == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_mine_logs_error_degraded(
        self,
        mock_user_repo,
        mock_role_repo,
        mock_menu_repo,
        token_service,
        mock_password_service,
        mock_cache_service,
        mock_log_repo,
    ):
        """日志查询异常时降级返回空列表，不阻断请求。"""
        mock_log_repo.get_login_logs = AsyncMock(side_effect=Exception("数据库连接失败"))
        service = self._service_with_log_repo(
            mock_user_repo,
            mock_role_repo,
            mock_menu_repo,
            token_service,
            mock_password_service,
            mock_cache_service,
            mock_log_repo,
        )

        result, total = await service.get_mine_logs(username="testuser")

        assert result == []
        assert total == 0
