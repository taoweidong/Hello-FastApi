"""角色服务的单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.role_dto import RoleCreateDTO, RoleUpdateDTO
from src.application.services.role_service import RoleService
from src.domain.exceptions import ConflictError, NotFoundError
from src.infrastructure.database.models import Role


@pytest.mark.unit
class TestRoleService:
    """RoleService 测试类。"""

    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话。"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        return session

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
    def role_service(self, mock_session, mock_role_repo):
        """创建角色服务实例。"""
        return RoleService(session=mock_session, role_repo=mock_role_repo)

    @pytest.mark.asyncio
    async def test_create_role_success(self, role_service, mock_role_repo, mock_session):
        """测试创建角色成功。"""
        created_role = Role(id="role-id-1", name="管理员", code="admin", is_active=1)
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_by_code = AsyncMock(return_value=None)
        mock_role_repo.create = AsyncMock()
        mock_role_repo.get_by_code_after = AsyncMock(return_value=created_role)

        # 模拟create后再查询
        async def mock_get_by_code(code):
            if code == "admin":
                return created_role
            return None

        mock_role_repo.get_by_code = AsyncMock(side_effect=[None, created_role])
        mock_role_repo.get_role_menu_ids = AsyncMock(return_value=[])

        dto = RoleCreateDTO(name="管理员", code="admin", isActive=True)
        result = await role_service.create_role(dto)

        assert result.name == "管理员"
        assert result.code == "admin"

    @pytest.mark.asyncio
    async def test_create_role_duplicate_name(self, role_service, mock_role_repo):
        """测试创建角色时名称重复。"""
        existing = Role(name="管理员")
        mock_role_repo.get_by_name = AsyncMock(return_value=existing)

        dto = RoleCreateDTO(name="管理员", code="admin2")
        with pytest.raises(ConflictError) as exc_info:
            await role_service.create_role(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_role_duplicate_code(self, role_service, mock_role_repo):
        """测试创建角色时编码重复。"""
        existing = Role(code="admin")
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_by_code = AsyncMock(return_value=existing)

        dto = RoleCreateDTO(name="新角色", code="admin")
        with pytest.raises(ConflictError) as exc_info:
            await role_service.create_role(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_role_with_menu_ids(self, role_service, mock_role_repo):
        """测试创建角色并分配菜单。"""
        created_role = Role(id="role-id-1", name="测试角色", code="test_role", is_active=1)
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_by_code = AsyncMock(side_effect=[None, created_role])
        mock_role_repo.create = AsyncMock()
        mock_role_repo.get_role_menu_ids = AsyncMock(return_value=["menu-1", "menu-2"])

        dto = RoleCreateDTO(name="测试角色", code="test_role", menuIds=["menu-1", "menu-2"])
        result = await role_service.create_role(dto)

        mock_role_repo.assign_menus_to_role.assert_called_once_with("role-id-1", ["menu-1", "menu-2"])

    @pytest.mark.asyncio
    async def test_get_role_not_found(self, role_service, mock_role_repo):
        """测试获取不存在的角色。"""
        mock_role_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await role_service.get_role("non-existent-id")

    @pytest.mark.asyncio
    async def test_update_role_success(self, role_service, mock_role_repo, mock_session):
        """测试更新角色成功。"""
        existing_role = Role(id="role-id-1", name="旧角色", code="old_code", is_active=1)
        mock_role_repo.get_by_id = AsyncMock(return_value=existing_role)
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
        role = Role(id="role-id-1", name="测试角色")
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
        role = Role(id="role-id-1", name="测试角色")
        mock_role_repo.get_by_id = AsyncMock(return_value=role)
        mock_role_repo.assign_role_to_user = AsyncMock(return_value=True)

        result = await role_service.assign_role_to_user("user-id-1", "role-id-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_assign_role_to_user_already_assigned(self, role_service, mock_role_repo):
        """测试重复为用户分配角色。"""
        role = Role(id="role-id-1", name="测试角色")
        mock_role_repo.get_by_id = AsyncMock(return_value=role)
        mock_role_repo.assign_role_to_user = AsyncMock(return_value=False)

        with pytest.raises(ConflictError):
            await role_service.assign_role_to_user("user-id-1", "role-id-1")
