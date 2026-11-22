"""高频接口读穿透缓存的单元测试（路由树 / user:info:full / role:options）。

验证三个缓存点的「命中不查库」与「变更后失效」行为：
- 路由树（routes:user:{id}）：认证服务 get_async_routes 读写；
  角色/菜单/角色分配变更经 invalidate_users_batch 链路失效。
- 用户完整信息（user:info:full:{id}）：用户服务 get_user 读写；
  invalidate_user_info 连带删除（完整信息是基础信息的超集）。
- 角色选项（role:options）：角色服务 get_all_simple_roles 读写；
  角色增/改/删主动失效。

缓存替身使用内存字典实现真实读写语义（与 fakes.py 的替身思路一致），
而非仅断言「某方法被调用过」的纯 Mock。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.dto.role_dto import RoleCreateDTO
from src.application.dto.user_dto import UserUpdateDTO
from src.application.mappers.user_mapper import UserMapper
from src.application.services.auth_service import AuthService
from src.application.services.role_service import RoleService
from src.application.services.user_service import UserService
from src.domain.entities.menu import MenuEntity
from src.domain.entities.role import RoleEntity
from src.domain.entities.user import UserEntity
from src.domain.enums import MenuType, UserRole
from src.domain.services.cache_port import RoleCachePort, UserCachePort
from src.domain.services.token_service import TokenService
from tests.unit.fakes import RecordingCacheService

TEST_SECRET_KEY = "test-secret-key-for-auth-testing"


class DictBackedUserCache(UserCachePort):
    """内存字典实现的用户缓存替身：真实读写/失效语义。

    失效语义与真实 CacheService 对齐：
    - invalidate_user_info 连带删除完整信息（user:info:full）；
    - invalidate_users_batch 走端口默认逐条实现（info+full/perms/routes）。
    """

    def __init__(self) -> None:
        self.store: dict[str, object] = {}

    async def get_user_permissions(self, user_id: str):
        return self.store.get(f"perms:{user_id}")

    async def set_user_permissions(self, user_id: str, permissions: list) -> bool:
        self.store[f"perms:{user_id}"] = permissions
        return True

    async def invalidate_user_permissions(self, user_id: str) -> bool:
        self.store.pop(f"perms:{user_id}", None)
        return True

    async def get_user_info(self, user_id: str):
        return self.store.get(f"info:{user_id}")

    async def set_user_info(self, user_id: str, info: dict) -> bool:
        self.store[f"info:{user_id}"] = info
        return True

    async def invalidate_user_info(self, user_id: str) -> bool:
        # 与真实实现一致：连带删除完整信息
        self.store.pop(f"info:{user_id}", None)
        self.store.pop(f"info_full:{user_id}", None)
        return True

    async def get_user_info_full(self, user_id: str):
        return self.store.get(f"info_full:{user_id}")

    async def set_user_info_full(self, user_id: str, info: dict) -> bool:
        self.store[f"info_full:{user_id}"] = info
        return True

    async def get_user_routes(self, user_id: str):
        return self.store.get(f"routes:{user_id}")

    async def set_user_routes(self, user_id: str, routes: list) -> bool:
        self.store[f"routes:{user_id}"] = routes
        return True

    async def invalidate_user_routes(self, user_id: str) -> bool:
        self.store.pop(f"routes:{user_id}", None)
        return True


class DictBackedRoleCache(RoleCachePort):
    """内存字典实现的角色选项缓存替身。"""

    def __init__(self) -> None:
        self.store: dict[str, object] = {}

    async def get_role_options(self):
        return self.store.get("options")

    async def set_role_options(self, options: list) -> bool:
        self.store["options"] = options
        return True

    async def invalidate_role_options(self) -> bool:
        self.store.pop("options", None)
        return True


def make_user(user_id: str = "u1", username: str = "alice") -> UserEntity:
    return UserEntity(id=user_id, username=username, password="hashed")


@pytest.mark.unit
class TestAsyncRoutesCache:
    """动态路由树缓存（routes:user:{id}）的行为。"""

    @pytest.fixture
    def deps(self):
        token_service = TokenService(
            secret_key=TEST_SECRET_KEY, algorithm="HS256", access_expire_minutes=30, refresh_expire_days=7
        )
        user_repo = AsyncMock()
        role_repo = AsyncMock()
        menu_repo = AsyncMock()
        password_service = MagicMock()
        return user_repo, role_repo, menu_repo, token_service, password_service

    @pytest.mark.asyncio
    async def test_cache_hit_skips_db(self, deps):
        """缓存命中时直接返回缓存路由树，不再查用户与菜单。"""
        user_repo, role_repo, menu_repo, token_service, password_service = deps
        cache = DictBackedUserCache()
        cached_tree = [{"path": "/home", "name": "home", "meta": {"title": "首页"}}]
        await cache.set_user_routes("u1", cached_tree)
        service = AuthService(
            user_repo=user_repo,
            role_repo=role_repo,
            menu_repo=menu_repo,
            token_service=token_service,
            password_service=password_service,
            user_cache=cache,
        )

        tree = await service.get_async_routes("u1")

        assert tree == cached_tree
        user_repo.get_by_id.assert_not_called()
        menu_repo.get_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_builds_tree_and_sets_cache(self, deps):
        """缓存未命中时查库建树并写回缓存（超管取全量菜单）。"""
        user_repo, role_repo, menu_repo, token_service, password_service = deps
        cache = DictBackedUserCache()
        user = UserEntity(id="u1", username="admin", password="x", is_superuser=UserRole.SUPERUSER)
        user_repo.get_by_id = AsyncMock(return_value=user)
        menu_repo.get_all = AsyncMock(
            return_value=[MenuEntity(id="m1", name="home", menu_type=int(MenuType.DIRECTORY), rank=1, path="/home")]
        )
        service = AuthService(
            user_repo=user_repo,
            role_repo=role_repo,
            menu_repo=menu_repo,
            token_service=token_service,
            password_service=password_service,
            user_cache=cache,
        )

        tree = await service.get_async_routes("u1")

        assert tree and tree[0]["path"] == "/home"
        assert await cache.get_user_routes("u1") == tree

    @pytest.mark.asyncio
    async def test_reuses_pre_resolved_user_entity(self, deps):
        """传入已解析的用户实体时跳过按 ID 重复查库。"""
        user_repo, role_repo, menu_repo, token_service, password_service = deps
        user = UserEntity(id="u1", username="admin", password="x", is_superuser=UserRole.SUPERUSER)
        user_repo.get_by_id = AsyncMock()
        menu_repo.get_all = AsyncMock(
            return_value=[MenuEntity(id="m1", name="home", menu_type=int(MenuType.DIRECTORY), rank=1, path="/home")]
        )
        service = AuthService(
            user_repo=user_repo,
            role_repo=role_repo,
            menu_repo=menu_repo,
            token_service=token_service,
            password_service=password_service,
        )

        tree = await service.get_async_routes("u1", user=user)

        assert tree and tree[0]["path"] == "/home"
        user_repo.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_role_assignment_invalidates_routes(self):
        """角色分配/移除（role_service）经批量失效链路清掉该用户路由树缓存。"""
        role_repo = AsyncMock()
        role_repo.get_by_id = AsyncMock(return_value=RoleEntity(id="r1", name="管理员", code="admin"))
        role_repo.assign_role_to_user = AsyncMock(return_value=True)
        role_repo.remove_role_from_user = AsyncMock(return_value=True)
        cache = RecordingCacheService()
        service = RoleService(role_repo=role_repo, cache_service=cache)

        await service.assign_role_to_user("u1", "r1")
        await service.remove_role_from_user("u1", "r1")

        assert cache.batch_calls == [["u1"], ["u1"]]
        # 批量失效语义覆盖路由树缓存
        assert cache.invalidate_user_routes_calls == ["u1", "u1"]

    @pytest.mark.asyncio
    async def test_user_assign_roles_invalidates_routes(self):
        """用户服务 assign_roles（覆盖式分配）同样失效该用户路由树缓存。"""
        user_repo = AsyncMock()
        user_repo.get_by_id = AsyncMock(return_value=make_user())
        role_repo = AsyncMock()
        role_repo.assign_roles_to_user = AsyncMock(return_value=True)
        password_service = MagicMock()
        cache = RecordingCacheService()
        service = UserService(
            repo=user_repo, password_service=password_service, role_repo=role_repo, cache_service=cache
        )

        await service.assign_roles("u1", ["r1"])

        assert cache.batch_calls == [["u1"]]
        assert cache.invalidate_user_routes_calls == ["u1"]


@pytest.mark.unit
class TestUserInfoFullCache:
    """/user/info 完整信息缓存（user:info:full:{id}）的行为。"""

    @pytest.fixture
    def user_service_deps(self):
        user_repo = AsyncMock()
        role_repo = AsyncMock()
        password_service = MagicMock()
        return user_repo, role_repo, password_service

    def make_dto(self, user: UserEntity) -> dict:
        return UserMapper.to_response(user, [RoleEntity(id="r1", name="管理员", code="admin")]).model_dump(mode="json")

    @pytest.mark.asyncio
    async def test_cache_hit_skips_db(self, user_service_deps):
        """缓存命中时直接还原 DTO，不再查库。"""
        user_repo, role_repo, password_service = user_service_deps
        cache = DictBackedUserCache()
        alice = make_user()
        await cache.set_user_info_full(alice.id, self.make_dto(alice))
        user_repo.get_by_id = AsyncMock()
        role_repo.get_user_roles = AsyncMock()
        service = UserService(
            repo=user_repo, password_service=password_service, role_repo=role_repo, cache_service=cache
        )

        dto = await service.get_user(alice.id)

        assert dto.id == alice.id
        assert dto.username == "alice"
        assert dto.roles == [{"id": "r1", "name": "管理员"}]
        user_repo.get_by_id.assert_not_called()
        role_repo.get_user_roles.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_queries_db_and_sets_cache(self, user_service_deps):
        """缓存未命中时查库构建 DTO 并写回缓存。"""
        user_repo, role_repo, password_service = user_service_deps
        cache = DictBackedUserCache()
        alice = make_user()
        user_repo.get_by_id = AsyncMock(return_value=alice)
        role_repo.get_user_roles = AsyncMock(return_value=[])
        service = UserService(
            repo=user_repo, password_service=password_service, role_repo=role_repo, cache_service=cache
        )

        dto = await service.get_user(alice.id)

        assert dto.username == "alice"
        cached = await cache.get_user_info_full(alice.id)
        assert cached is not None
        assert cached["username"] == "alice"

    @pytest.mark.asyncio
    async def test_update_own_profile_invalidates_full_cache(self, user_service_deps):
        """用户自身资料更新后，完整信息缓存被连带失效（invalidate_user_info）。"""
        user_repo, role_repo, password_service = user_service_deps
        cache = DictBackedUserCache()
        alice = make_user()
        await cache.set_user_info_full(alice.id, self.make_dto(alice))
        user_repo.get_by_id = AsyncMock(return_value=alice)
        user_repo.update = AsyncMock(return_value=alice)
        role_repo.get_user_roles = AsyncMock(return_value=[])

        service = UserService(
            repo=user_repo, password_service=password_service, role_repo=role_repo, cache_service=cache
        )
        await service.update_own_profile(alice.id, UserUpdateDTO(nickname="新昵称"))

        assert await cache.get_user_info_full(alice.id) is None


@pytest.mark.unit
class TestRoleOptionsCache:
    """角色选项缓存（role:options）的行为。"""

    @pytest.fixture
    def mock_role_repo(self):
        repo = AsyncMock()
        repo.get_by_name = AsyncMock(return_value=None)
        repo.get_by_code = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_all = AsyncMock(return_value=[RoleEntity(id="r1", name="管理员", code="admin")])
        repo.create = AsyncMock()
        repo.get_role_menu_ids = AsyncMock(return_value=[])
        repo.get_user_ids_by_role = AsyncMock(return_value=[])
        return repo

    @pytest.mark.asyncio
    async def test_cache_hit_skips_db(self, mock_role_repo):
        """缓存命中时直接返回选项，不查角色仓储。"""
        cache = DictBackedRoleCache()
        await cache.set_role_options([{"id": "r1", "name": "管理员"}])
        mock_role_repo.get_all = AsyncMock()
        service = RoleService(role_repo=mock_role_repo, options_cache=cache)

        options = await service.get_all_simple_roles()

        assert options == [{"id": "r1", "name": "管理员"}]
        mock_role_repo.get_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_queries_and_sets(self, mock_role_repo):
        """缓存未命中时查仓储并写回缓存。"""
        cache = DictBackedRoleCache()
        service = RoleService(role_repo=mock_role_repo, options_cache=cache)

        options = await service.get_all_simple_roles()

        assert options == [{"id": "r1", "name": "管理员"}]
        assert await cache.get_role_options() == options

    @pytest.mark.asyncio
    async def test_create_role_invalidates_options(self, mock_role_repo):
        """创建角色后选项缓存失效。"""
        cache = DictBackedRoleCache()
        await cache.set_role_options([{"id": "r1", "name": "管理员"}])
        created = RoleEntity(id="r2", name="审计员", code="auditor", is_active=1)
        mock_role_repo.create = AsyncMock(return_value=created)
        service = RoleService(role_repo=mock_role_repo, options_cache=cache)

        await service.create_role(RoleCreateDTO(name="审计员", code="auditor", isActive=True))

        assert await cache.get_role_options() is None

    @pytest.mark.asyncio
    async def test_delete_role_invalidates_options(self, mock_role_repo):
        """删除角色后选项缓存失效。"""
        mock_role_repo.delete = AsyncMock(return_value=True)
        cache = DictBackedRoleCache()
        await cache.set_role_options([{"id": "r1", "name": "管理员"}])
        service = RoleService(role_repo=mock_role_repo, options_cache=cache)

        await service.delete_role("r1")

        assert await cache.get_role_options() is None
