"""RoleRepository 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.menu import MenuEntity
from src.domain.entities.role import RoleEntity
from src.infrastructure.repositories.role_repository import RoleRepository


@pytest.mark.unit
class TestRoleRepository:
    """RoleRepository 测试类。"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return RoleRepository(mock_session)

    def test_init(self, repo, mock_session):
        """测试初始化设置 session。"""
        assert repo.session is mock_session

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, mock_session):
        """测试 get_by_id 找到角色。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = RoleEntity(id="1", name="管理员", code="admin")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("1")
        assert result is not None
        assert result.name == "管理员"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo, mock_session):
        """测试 get_by_id 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name_found(self, repo, mock_session):
        """测试 get_by_name 找到角色。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = RoleEntity(id="1", name="管理员", code="admin")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_name("管理员")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_code_found(self, repo, mock_session):
        """测试 get_by_code 找到角色。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = RoleEntity(id="1", name="管理员", code="admin")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_code("admin")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_all(self, repo, mock_session):
        """测试 get_all 返回分页角色列表。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = RoleEntity(id="1", name="管理员", code="admin")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(page_num=1, page_size=10)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, repo, mock_session):
        """测试 get_all 带筛选条件。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(role_name="管理员", is_active=1)
        assert result == []
        mock_session.exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_count(self, repo, mock_session):
        """测试 count 返回总数。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 5
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count()
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_with_filters(self, repo, mock_session):
        """测试 count 支持筛选。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 2
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count(role_name="管理员", is_active=1)
        assert result == 2

    @pytest.mark.asyncio
    async def test_create(self, repo, mock_session):
        """测试 create 创建角色。"""
        entity = RoleEntity(id="1", name="新角色", code="new_role")
        mock_model = MagicMock()
        mock_model.id = "1"
        mock_model.to_domain.return_value = entity

        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch("src.infrastructure.repositories.role_repository.Role.from_domain", return_value=mock_model):
            result = await repo.create(entity)

        assert result is not None
        assert result.id == "1"
        mock_session.add.assert_called_once_with(mock_model)

    @pytest.mark.asyncio
    async def test_update(self, repo, mock_session):
        """测试 update 更新角色。"""
        entity = RoleEntity(
            id="1", name="更新角色", code="upd", is_active=1, creator_id="u1", modifier_id="u2", description="desc"
        )
        mock_merged = MagicMock()
        mock_merged.id = "1"
        mock_merged.to_domain.return_value = entity

        mock_session.merge = AsyncMock(return_value=mock_merged)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        result = await repo.update(entity)

        assert result is not None
        assert result.id == "1"

    @pytest.mark.asyncio
    async def test_delete_success(self, repo, mock_session):
        """测试 delete 成功删除角色。"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.exec.return_value = mock_result

        result = await repo.delete("role-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repo, mock_session):
        """测试 delete 未找到返回 False。"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.exec.return_value = mock_result

        result = await repo.delete("not-exist")
        assert result is False

    @pytest.mark.asyncio
    async def test_assign_role_to_user_new(self, repo, mock_session):
        """测试 assign_role_to_user 分配新角色。"""
        mock_result = MagicMock()
        mock_result.one_or_none.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.assign_role_to_user("user-1", "role-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_assign_role_to_user_existing(self, repo, mock_session):
        """测试 assign_role_to_user 角色已存在返回 False。"""
        mock_session.exec = AsyncMock()
        mock_session.exec.return_value.one_or_none.return_value = MagicMock()

        result = await repo.assign_role_to_user("user-1", "role-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_role_from_user(self, repo, mock_session):
        """测试 remove_role_from_user 移除角色。"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.exec.return_value = mock_result

        result = await repo.remove_role_from_user("user-1", "role-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_roles(self, repo, mock_session):
        """测试 get_user_roles 获取用户角色列表。"""
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.to_domain.return_value = RoleEntity(id="1", name="管理员", code="admin")
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        roles = await repo.get_user_roles("user-1")
        assert len(roles) == 1

    @pytest.mark.asyncio
    async def test_assign_roles_to_user(self, repo, mock_session):
        """测试 assign_roles_to_user 批量分配角色。"""
        result = await repo.assign_roles_to_user("user-1", ["role-1", "role-2"])
        assert result is True

    @pytest.mark.asyncio
    async def test_assign_menus_to_role(self, repo, mock_session):
        """测试 assign_menus_to_role 分配菜单权限。"""
        result = await repo.assign_menus_to_role("role-1", ["menu-1", "menu-2"])
        assert result is True

    @pytest.mark.asyncio
    async def test_get_role_menus(self, repo, mock_session):
        """测试 get_role_menus 获取角色菜单列表。"""
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.to_domain.return_value = MenuEntity(id="menu-1", name="系统管理", menu_type="M")
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        menus = await repo.get_role_menus("role-1")
        assert len(menus) == 1

    @pytest.mark.asyncio
    async def test_get_role_menu_ids(self, repo, mock_session):
        """测试 get_role_menu_ids 获取角色菜单 ID 列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = ["menu-1", "menu-2"]
        mock_session.exec = AsyncMock(return_value=mock_result)

        menu_ids = await repo.get_role_menu_ids("role-1")
        assert len(menu_ids) == 2

    @pytest.mark.asyncio
    async def test_get_user_all_menus(self, repo, mock_session):
        """测试 get_user_all_menus 获取用户所有菜单。"""
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.id = "menu-1"
        mock_model.to_domain.return_value = MenuEntity(id="menu-1", name="系统管理", menu_type="M")
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        menus = await repo.get_user_all_menus("user-1")
        assert len(menus) == 1

    @pytest.mark.asyncio
    async def test_get_users_roles_batch(self, repo, mock_session):
        """测试 get_users_roles_batch 批量获取用户角色。"""
        mock_result = MagicMock()
        mock_role = MagicMock()
        mock_role.to_domain.return_value = RoleEntity(id="r1", name="管理员", code="admin")
        mock_result.all.return_value = [(mock_role, "user-1")]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_users_roles_batch(["user-1"])
        assert "user-1" in result
        assert len(result["user-1"]) == 1

    @pytest.mark.asyncio
    async def test_get_users_roles_batch_no_result(self, repo, mock_session):
        """测试 get_users_roles_batch 无结果时不包含空列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_users_roles_batch(["user-1", "user-2"])
        assert "user-1" not in result
        assert "user-2" not in result

    @pytest.mark.asyncio
    async def test_get_users_roles_batch_empty(self, repo):
        """测试 get_users_roles_batch 空列表返回空字典。"""
        result = await repo.get_users_roles_batch([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_roles_menu_ids_batch(self, repo, mock_session):
        """测试 get_roles_menu_ids_batch 批量获取角色菜单 ID。"""
        mock_result = MagicMock()
        mock_link = MagicMock()
        mock_link.userrole_id = "role-1"
        mock_link.menu_id = "menu-1"
        mock_result.all.return_value = [mock_link]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_roles_menu_ids_batch(["role-1"])
        assert "role-1" in result
        assert len(result["role-1"]) == 1

    @pytest.mark.asyncio
    async def test_get_roles_menu_ids_batch_no_result(self, repo, mock_session):
        """测试 get_roles_menu_ids_batch 无结果时返回空字典。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_roles_menu_ids_batch(["role-1", "role-2"])
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_roles_menu_ids_batch_empty(self, repo):
        """测试 get_roles_menu_ids_batch 空列表返回空字典。"""
        result = await repo.get_roles_menu_ids_batch([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, repo, mock_session):
        """测试 get_by_name 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_name("not-exist")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_code_not_found(self, repo, mock_session):
        """测试 get_by_code 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_code("not-exist")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_no_filters(self, repo, mock_session):
        """测试 get_all 无筛选条件。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all()

        assert result == []

    @pytest.mark.asyncio
    async def test_remove_role_from_user_not_found(self, repo, mock_session):
        """测试 remove_role_from_user 未找到关联。"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.exec.return_value = mock_result

        result = await repo.remove_role_from_user("user-1", "role-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_roles_empty(self, repo, mock_session):
        """测试 get_user_roles 用户无角色返回空列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        roles = await repo.get_user_roles("user-no-roles")

        assert roles == []

    @pytest.mark.asyncio
    async def test_get_role_menus_empty(self, repo, mock_session):
        """测试 get_role_menus 角色无菜单返回空列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        menus = await repo.get_role_menus("role-no-menus")

        assert menus == []

    @pytest.mark.asyncio
    async def test_get_role_menu_ids_empty(self, repo, mock_session):
        """测试 get_role_menu_ids 角色无菜单 ID 返回空列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        menu_ids = await repo.get_role_menu_ids("role-no-menus")

        assert menu_ids == []
