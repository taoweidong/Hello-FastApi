"""角色服务的单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.role_dto import RoleCreateDTO, RoleUpdateDTO
from src.application.services.role_service import RoleService
from src.domain.entities.role import RoleEntity
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
        roles = [
            RoleEntity(id="r1", name="管理员", code="admin"),
            RoleEntity(id="r2", name="用户", code="user"),
        ]
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
