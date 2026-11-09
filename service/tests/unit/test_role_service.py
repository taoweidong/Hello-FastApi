"""角色服务的单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.role_dto import ChangeDataScopeDTO, RoleCreateDTO, RoleUpdateDTO
from src.application.services.role_service import RoleService
from src.domain.entities.role import RoleEntity
from src.domain.enums import DataScope
from src.domain.exceptions import ConflictError, NotFoundError


@pytest.mark.unit
class TestRoleService:
    """RoleService 测试类。"""

    @pytest.fixture
    def mock_role_repo(self):
        """创建模拟角色仓储。"""
        repo = AsyncMock()
        repo.get_by_name = AsyncMock(return_value=None)
        repo.get_by_code = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock(return_value=False)
        repo.assign_menus_to_role = AsyncMock()
        repo.get_role_menu_ids = AsyncMock(return_value=[])
        repo.get_user_roles = AsyncMock(return_value=[])
        repo.assign_role_to_user = AsyncMock(return_value=True)
        repo.remove_role_from_user = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def role_service(self, mock_role_repo):
        """创建角色服务实例。"""
        return RoleService(role_repo=mock_role_repo)

    @pytest.mark.asyncio
    async def test_create_role_success(self, role_service, mock_role_repo):
        """测试创建角色成功。"""
        created_role = RoleEntity(id="role-id-1", name="管理员", code="admin", is_active=1)
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_by_code = AsyncMock(side_effect=[None, created_role])
        mock_role_repo.create = AsyncMock(return_value=created_role)
        mock_role_repo.get_role_menu_ids = AsyncMock(return_value=[])

        dto = RoleCreateDTO(name="管理员", code="admin", isActive=True)
        result = await role_service.create_role(dto)

        assert result.name == "管理员"
        assert result.code == "admin"

    @pytest.mark.asyncio
    async def test_create_role_duplicate_name(self, role_service, mock_role_repo):
        """测试创建角色时名称重复。"""
        existing = RoleEntity(id="ex-id", name="管理员", code="other")
        mock_role_repo.get_by_name = AsyncMock(return_value=existing)

        dto = RoleCreateDTO(name="管理员", code="admin2")
        with pytest.raises(ConflictError) as exc_info:
            await role_service.create_role(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_role_duplicate_code(self, role_service, mock_role_repo):
        """测试创建角色时编码重复。"""
        existing = RoleEntity(id="ex-id", code="admin", name="other")
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_by_code = AsyncMock(return_value=existing)

        dto = RoleCreateDTO(name="新角色", code="admin")
        with pytest.raises(ConflictError) as exc_info:
            await role_service.create_role(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_role_with_menu_ids(self, role_service, mock_role_repo):
        """测试创建角色并分配菜单。"""
        created_role = RoleEntity(id="role-id-1", name="测试角色", code="test_role", is_active=1)
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_by_code = AsyncMock(side_effect=[None, created_role])
        mock_role_repo.create = AsyncMock(return_value=created_role)
        mock_role_repo.get_role_menu_ids = AsyncMock(return_value=["menu-1", "menu-2"])

        dto = RoleCreateDTO(name="测试角色", code="test_role", menuIds=["menu-1", "menu-2"])
        await role_service.create_role(dto)

        mock_role_repo.assign_menus_to_role.assert_called_once_with("role-id-1", ["menu-1", "menu-2"])

    @pytest.mark.asyncio
    async def test_get_role_not_found(self, role_service, mock_role_repo):
        """测试获取不存在的角色。"""
        mock_role_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await role_service.get_role("non-existent-id")

    @pytest.mark.asyncio
    async def test_update_role_success(self, role_service, mock_role_repo):
        """测试更新角色成功。"""
        existing_role = RoleEntity(id="role-id-1", name="旧角色", code="old_code", is_active=1)
        updated_role = RoleEntity(id="role-id-1", name="新角色", code="old_code", is_active=1)
        mock_role_repo.get_by_id = AsyncMock(side_effect=[existing_role, updated_role])
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_role_menu_ids = AsyncMock(return_value=[])

        dto = RoleUpdateDTO(name="新角色")
        result = await role_service.update_role("role-id-1", dto)

        assert result.name == "新角色"
        mock_role_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_role_success(self, role_service, mock_role_repo):
        """测试删除角色成功。"""
        mock_role_repo.delete = AsyncMock(return_value=True)

        result = await role_service.delete_role("role-id-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_role_not_found(self, role_service, mock_role_repo):
        """测试删除不存在的角色。"""
        mock_role_repo.delete = AsyncMock(return_value=False)

        with pytest.raises(NotFoundError):
            await role_service.delete_role("non-existent-id")

    @pytest.mark.asyncio
    async def test_assign_menus(self, role_service, mock_role_repo):
        """测试为角色分配菜单权限。"""
        role = RoleEntity(id="role-id-1", name="测试角色", code="test")
        mock_role_repo.get_by_id = AsyncMock(return_value=role)

        result = await role_service.assign_menus("role-id-1", ["menu-1", "menu-2"])
        assert result is True
        mock_role_repo.assign_menus_to_role.assert_called_once_with("role-id-1", ["menu-1", "menu-2"])

    @pytest.mark.asyncio
    async def test_assign_menus_role_not_found(self, role_service, mock_role_repo):
        """测试为不存在的角色分配菜单。"""
        mock_role_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await role_service.assign_menus("non-existent-id", ["menu-1"])

    @pytest.mark.asyncio
    async def test_assign_role_to_user(self, role_service, mock_role_repo):
        """测试为用户分配角色。"""
        role = RoleEntity(id="role-id-1", name="测试角色", code="test")
        mock_role_repo.get_by_id = AsyncMock(return_value=role)
        mock_role_repo.assign_role_to_user = AsyncMock(return_value=True)

        result = await role_service.assign_role_to_user("user-id-1", "role-id-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_assign_role_to_user_already_assigned(self, role_service, mock_role_repo):
        """测试重复为用户分配角色。"""
        role = RoleEntity(id="role-id-1", name="测试角色", code="test")
        mock_role_repo.get_by_id = AsyncMock(return_value=role)
        mock_role_repo.assign_role_to_user = AsyncMock(return_value=False)

        with pytest.raises(ConflictError):
            await role_service.assign_role_to_user("user-id-1", "role-id-1")

    @pytest.mark.asyncio
    async def test_assign_role_to_user_role_not_found(self, role_service, mock_role_repo):
        """测试分配角色时角色不存在。"""
        mock_role_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await role_service.assign_role_to_user("user-id-1", "non-existent")

    @pytest.mark.asyncio
    async def test_get_role_success(self, role_service, mock_role_repo):
        """测试获取角色成功。"""
        role = RoleEntity(id="role-id-1", name="管理员", code="admin", is_active=1)
        mock_role_repo.get_by_id = AsyncMock(return_value=role)
        mock_role_repo.get_role_menu_ids = AsyncMock(return_value=["menu-1", "menu-2"])

        result = await role_service.get_role("role-id-1")
        assert result.id == "role-id-1"
        assert result.name == "管理员"
        assert len(result.menus) == 2

    @pytest.mark.asyncio
    async def test_get_roles_empty(self, role_service, mock_role_repo):
        """测试获取空角色列表。"""
        from src.application.dto.role_dto import RoleListQueryDTO

        mock_role_repo.count = AsyncMock(return_value=0)
        mock_role_repo.get_all = AsyncMock(return_value=[])
        mock_role_repo.get_roles_menu_ids_batch = AsyncMock(return_value={})

        query = RoleListQueryDTO(pageNum=1, pageSize=10)
        results, total = await role_service.get_roles(query)
        assert total == 0
        assert results == []

    @pytest.mark.asyncio
    async def test_get_roles_with_filters(self, role_service, mock_role_repo):
        """测试按名称/状态筛选角色列表。"""
        from src.application.dto.role_dto import RoleListQueryDTO

        role = RoleEntity(id="r1", name="管理员", code="admin", is_active=1)
        mock_role_repo.count = AsyncMock(return_value=1)
        mock_role_repo.get_all = AsyncMock(return_value=[role])
        mock_role_repo.get_roles_menu_ids_batch = AsyncMock(return_value={"r1": ["m1"]})

        query = RoleListQueryDTO(name="管理员", isActive=1, pageNum=1, pageSize=10)
        results, total = await role_service.get_roles(query)
        assert total == 1
        assert len(results) == 1
        assert results[0].name == "管理员"

    @pytest.mark.asyncio
    async def test_update_role_with_menu_ids(self, role_service, mock_role_repo):
        """测试更新角色时重新分配菜单。"""
        existing = RoleEntity(id="role-id-1", name="旧角色", code="old", is_active=1)
        updated = RoleEntity(id="role-id-1", name="新角色", code="new", is_active=1)
        mock_role_repo.get_by_id = AsyncMock(side_effect=[existing, updated])
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_by_code = AsyncMock(return_value=None)
        mock_role_repo.get_role_menu_ids = AsyncMock(return_value=["menu-1"])

        dto = RoleUpdateDTO(name="新角色", code="new", menuIds=["menu-1", "menu-2"])
        result = await role_service.update_role("role-id-1", dto)
        assert result.name == "新角色"
        mock_role_repo.assign_menus_to_role.assert_called_once_with("role-id-1", ["menu-1", "menu-2"])

    @pytest.mark.asyncio
    async def test_update_role_not_found(self, role_service, mock_role_repo):
        """测试更新不存在的角色。"""
        mock_role_repo.get_by_id = AsyncMock(return_value=None)
        dto = RoleUpdateDTO(name="新角色")
        with pytest.raises(NotFoundError):
            await role_service.update_role("non-existent-id", dto)

    @pytest.mark.asyncio
    async def test_update_role_duplicate_name(self, role_service, mock_role_repo):
        """测试更新角色时名称与其他角色重复。"""
        existing = RoleEntity(id="role-id-1", name="角色", code="old", is_active=1)
        other = RoleEntity(id="role-id-2", name="现有角色", code="other")
        mock_role_repo.get_by_id = AsyncMock(return_value=existing)
        mock_role_repo.get_by_name = AsyncMock(return_value=other)

        dto = RoleUpdateDTO(name="现有角色")
        with pytest.raises(ConflictError):
            await role_service.update_role("role-id-1", dto)

    @pytest.mark.asyncio
    async def test_update_role_duplicate_code(self, role_service, mock_role_repo):
        """测试更新角色时编码重复。"""
        existing = RoleEntity(id="role-id-1", name="角色", code="old", is_active=1)
        other = RoleEntity(id="role-id-2", name="其他", code="other")
        mock_role_repo.get_by_id = AsyncMock(return_value=existing)
        mock_role_repo.get_by_code = AsyncMock(return_value=other)

        dto = RoleUpdateDTO(code="other")
        with pytest.raises(ConflictError):
            await role_service.update_role("role-id-1", dto)

    @pytest.mark.asyncio
    async def test_remove_role_from_user_success(self, role_service, mock_role_repo):
        """测试移除用户角色成功。"""
        mock_role_repo.remove_role_from_user = AsyncMock(return_value=True)
        result = await role_service.remove_role_from_user("user-id-1", "role-id-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_remove_role_from_user_not_found(self, role_service, mock_role_repo):
        """测试移除不存在的用户角色关系。"""
        mock_role_repo.remove_role_from_user = AsyncMock(return_value=False)
        with pytest.raises(NotFoundError):
            await role_service.remove_role_from_user("user-id-1", "role-id-1")

    @pytest.mark.asyncio
    async def test_get_user_roles_success(self, role_service, mock_role_repo):
        """测试获取用户的所有角色。"""
        roles = [RoleEntity(id="r1", name="管理员", code="admin"), RoleEntity(id="r2", name="用户", code="user")]
        mock_role_repo.get_user_roles = AsyncMock(return_value=roles)
        mock_role_repo.get_role_menu_ids = AsyncMock(return_value=[])

        result = await role_service.get_user_roles("user-id-1")
        assert len(result) == 2
        assert result[0].name == "管理员"

    @pytest.mark.asyncio
    async def test_get_user_roles_empty(self, role_service, mock_role_repo):
        """测试获取无角色用户。"""
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])
        result = await role_service.get_user_roles("user-id-1")
        assert result == []

    def test_role_to_response_with_menus(self, role_service):
        """测试 _role_to_response_with_menus 静态方法。"""
        from datetime import datetime

        role = RoleEntity(
            id="r1",
            name="管理员",
            code="admin",
            is_active=1,
            creator_id="u1",
            modifier_id="u2",
            created_time=datetime.now(),
            updated_time=datetime.now(),
            description="描述",
        )
        result = role_service._role_to_response_with_menus(role, ["m1", "m2"])
        assert result.id == "r1"
        assert result.name == "管理员"
        assert len(result.menus) == 2

    def test_role_to_response_with_menus_empty(self, role_service):
        """测试 _role_to_response_with_menus 无菜单。"""
        role = RoleEntity(id="r1", name="测试", code="test")
        result = role_service._role_to_response_with_menus(role, [])
        assert result.menus == []

    @pytest.mark.asyncio
    async def test_update_role_not_found_mid_update(self, role_service, mock_role_repo):
        """测试更新角色后重载时不存在。"""
        existing = RoleEntity(id="role-id-1", name="角色", code="old", is_active=1)
        mock_role_repo.get_by_id = AsyncMock(side_effect=[existing, None])
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_by_code = AsyncMock(return_value=None)
        mock_role_repo.update = AsyncMock()

        dto = RoleUpdateDTO(name="新角色")
        with pytest.raises(NotFoundError):
            await role_service.update_role("role-id-1", dto)

    @pytest.mark.asyncio
    async def test_change_data_scope_custom(self, role_service, mock_role_repo):
        """测试修改数据权限为自定义并分配部门。"""
        role = RoleEntity(id="role-id-1", name="测试角色", code="test", data_scope=DataScope.ALL)
        mock_role_repo.get_by_id = AsyncMock(return_value=role)

        dto = ChangeDataScopeDTO(dataScope=DataScope.CUSTOM, deptIds=["dept-1", "dept-2"])
        result = await role_service.change_data_scope("role-id-1", dto)

        assert result is True
        assert role.data_scope == DataScope.CUSTOM
        mock_role_repo.update.assert_called_once_with(role)
        mock_role_repo.assign_depts_to_role.assert_called_once_with("role-id-1", ["dept-1", "dept-2"])

    @pytest.mark.asyncio
    async def test_change_data_scope_not_custom_clears_depts(self, role_service, mock_role_repo):
        """测试修改为非自定义数据权限时清空部门关联。"""
        role = RoleEntity(id="role-id-1", name="测试角色", code="test", data_scope=DataScope.CUSTOM)
        mock_role_repo.get_by_id = AsyncMock(return_value=role)

        dto = ChangeDataScopeDTO(dataScope=DataScope.DEPT_AND_CHILD)
        result = await role_service.change_data_scope("role-id-1", dto)

        assert result is True
        assert role.data_scope == DataScope.DEPT_AND_CHILD
        mock_role_repo.assign_depts_to_role.assert_called_once_with("role-id-1", [])

    @pytest.mark.asyncio
    async def test_change_data_scope_role_not_found(self, role_service, mock_role_repo):
        """测试修改不存在角色的数据权限。"""
        mock_role_repo.get_by_id = AsyncMock(return_value=None)

        dto = ChangeDataScopeDTO(dataScope=DataScope.ALL)
        with pytest.raises(NotFoundError):
            await role_service.change_data_scope("non-existent-id", dto)


@pytest.mark.unit
class TestRoleServiceCacheInvalidation:
    """角色权限变更后必须失效相关用户的权限缓存（防越权窗口）。"""

    @pytest.fixture
    def mock_role_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_user_ids_by_role = AsyncMock(return_value=[])
        repo.delete = AsyncMock(return_value=False)
        repo.assign_menus_to_role = AsyncMock()
        repo.assign_depts_to_role = AsyncMock()
        repo.update = AsyncMock()
        repo.assign_role_to_user = AsyncMock(return_value=True)
        repo.remove_role_from_user = AsyncMock(return_value=True)
        repo.get_role_menu_ids = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def role_service(self, mock_role_repo, mock_cache):
        return RoleService(role_repo=mock_role_repo, cache_service=mock_cache)

    @pytest.mark.asyncio
    async def test_assign_menus_invalidates_role_users(self, role_service, mock_role_repo, mock_cache):
        """分配菜单后失效该角色下所有用户的缓存。"""
        role = RoleEntity(id="role-1", name="测试", code="test")
        mock_role_repo.get_by_id = AsyncMock(return_value=role)
        mock_role_repo.get_user_ids_by_role = AsyncMock(return_value=["u1", "u2"])

        await role_service.assign_menus("role-1", ["m1"])

        mock_cache.invalidate_users_batch.assert_awaited_once_with(["u1", "u2"])

    @pytest.mark.asyncio
    async def test_change_data_scope_invalidates_role_users(self, role_service, mock_role_repo, mock_cache):
        """修改数据权限后失效该角色下所有用户的缓存。"""
        role = RoleEntity(id="role-1", name="测试", code="test")
        mock_role_repo.get_by_id = AsyncMock(return_value=role)
        mock_role_repo.get_user_ids_by_role = AsyncMock(return_value=["u1"])

        await role_service.change_data_scope("role-1", ChangeDataScopeDTO(dataScope=DataScope.ALL))

        mock_cache.invalidate_users_batch.assert_awaited_once_with(["u1"])

    @pytest.mark.asyncio
    async def test_update_role_invalidates_role_users(self, role_service, mock_role_repo, mock_cache):
        """更新角色（菜单/状态）后失效该角色下所有用户的缓存。"""
        role = RoleEntity(id="role-1", name="旧名", code="test")
        mock_role_repo.get_by_id = AsyncMock(side_effect=[role, role])
        mock_role_repo.get_user_ids_by_role = AsyncMock(return_value=["u1", "u2", "u3"])

        await role_service.update_role("role-1", RoleUpdateDTO(isActive=0))

        mock_cache.invalidate_users_batch.assert_awaited_once_with(["u1", "u2", "u3"])

    @pytest.mark.asyncio
    async def test_delete_role_invalidates_users_before_delete(self, role_service, mock_role_repo, mock_cache):
        """删除角色前先取用户列表，删除后失效其缓存。"""
        mock_role_repo.delete = AsyncMock(return_value=True)
        mock_role_repo.get_user_ids_by_role = AsyncMock(return_value=["u1"])

        await role_service.delete_role("role-1")

        mock_cache.invalidate_users_batch.assert_awaited_once_with(["u1"])

    @pytest.mark.asyncio
    async def test_assign_role_to_user_invalidates_target_user(self, role_service, mock_role_repo, mock_cache):
        """给用户分配角色后失效该用户缓存。"""
        mock_role_repo.get_by_id = AsyncMock(return_value=RoleEntity(id="role-1", name="r", code="r"))

        await role_service.assign_role_to_user("user-9", "role-1")

        mock_cache.invalidate_users_batch.assert_awaited_once_with(["user-9"])

    @pytest.mark.asyncio
    async def test_remove_role_from_user_invalidates_target_user(self, role_service, mock_role_repo, mock_cache):
        """移除用户角色后失效该用户缓存。"""
        await role_service.remove_role_from_user("user-9", "role-1")

        mock_cache.invalidate_users_batch.assert_awaited_once_with(["user-9"])

    @pytest.mark.asyncio
    async def test_no_cache_service_skips_invalidation(self, mock_role_repo):
        """未注入缓存服务时（降级）不报错。"""
        svc = RoleService(role_repo=mock_role_repo, cache_service=None)
        mock_role_repo.get_by_id = AsyncMock(return_value=RoleEntity(id="role-1", name="r", code="r"))

        result = await svc.assign_menus("role-1", ["m1"])
        assert result is True

    @pytest.mark.asyncio
    async def test_repo_query_failure_does_not_block_business(self, role_service, mock_role_repo, mock_cache):
        """用户列表查询失败仅跳过失效，不阻断业务操作（TTL 到期自然一致）。"""
        role = RoleEntity(id="role-1", name="r", code="r")
        mock_role_repo.get_by_id = AsyncMock(return_value=role)
        mock_role_repo.get_user_ids_by_role = AsyncMock(side_effect=RuntimeError("db error"))

        result = await role_service.assign_menus("role-1", ["m1"])
        assert result is True
        mock_cache.invalidate_users_batch.assert_not_awaited()


@pytest.mark.unit
class TestRoleServiceMenuAncestorCompletion:
    """角色授权的祖先补全：防御客户端半选丢失父级导致路由孤儿。"""

    @pytest.fixture
    def mock_user_cache(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=RoleEntity(id="role-1", name="r", code="r"))
        repo.assign_menus_to_role = AsyncMock()
        repo.get_role_menu_ids = AsyncMock(return_value=[])
        repo.get_user_ids_by_role = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_menu_repo(self):
        from src.domain.entities.menu import MenuEntity
        from src.domain.entities.menu_meta import MenuMetaEntity

        repo = AsyncMock()
        meta = MenuMetaEntity(id="m0", title="x")
        # System(dir) -> User(page) -> user:add(btn) 层级
        repo.get_all = AsyncMock(
            return_value=[
                MenuEntity(id="System", name="System", menu_type=0, rank=0, parent_id=None, meta=meta),
                MenuEntity(id="User", name="User", menu_type=1, rank=1, parent_id="System", meta=meta),
                MenuEntity(id="user:add", name="user:add", menu_type=2, rank=2, parent_id="User", meta=meta),
            ]
        )
        return repo

    @pytest.fixture
    def service(self, mock_role_repo, mock_menu_repo, mock_user_cache):
        from src.application.services.role_service import RoleService

        return RoleService(role_repo=mock_role_repo, cache_service=mock_user_cache, menu_repo=mock_menu_repo)

    async def test_assign_menus_completes_ancestors(self, service, mock_role_repo):
        """仅传叶子按钮码时，父目录/页面节点自动补全。"""
        await service.assign_menus("role-1", ["user:add"])
        mock_role_repo.assign_menus_to_role.assert_awaited_once()
        completed = mock_role_repo.assign_menus_to_role.await_args.args[1]
        assert set(completed) == {"user:add", "User", "System"}

    async def test_unknown_ids_ignored(self, service, mock_role_repo):
        """未知 ID 静默忽略（防御脏输入）。"""
        await service.assign_menus("role-1", ["user:add", "ghost-id"])
        completed = mock_role_repo.assign_menus_to_role.await_args.args[1]
        assert set(completed) == {"user:add", "User", "System"}

    async def test_menu_repo_missing_returns_original(self, mock_role_repo, mock_user_cache):
        """菜单仓储未注入时原样返回（仅测试场景）。"""
        from src.application.services.role_service import RoleService

        svc = RoleService(role_repo=mock_role_repo, cache_service=mock_user_cache, menu_repo=None)
        result = await svc._complete_menu_ancestors(["m1"])
        assert result == ["m1"]
