"""菜单服务的单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.menu_dto import MenuCreateDTO, MenuUpdateDTO
from src.application.services.menu_service import MenuService
from src.domain.exceptions import ConflictError, NotFoundError
from src.infrastructure.database.models import Menu, MenuMeta


@pytest.mark.unit
class TestMenuService:
    """MenuService 测试类。"""

    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话。"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def mock_menu_repo(self):
        """创建模拟菜单仓储。"""
        repo = AsyncMock()
        repo.get_by_name = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_all = AsyncMock(return_value=[])
        repo.get_by_parent_id = AsyncMock(return_value=[])
        repo.create = AsyncMock()
        repo.create_meta = AsyncMock()
        repo.update = AsyncMock()
        repo.update_meta = AsyncMock()
        repo.delete = AsyncMock(return_value=True)
        repo.delete_meta = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def menu_service(self, mock_session, mock_menu_repo):
        """创建菜单服务实例。"""
        return MenuService(session=mock_session, menu_repo=mock_menu_repo)

    @pytest.mark.asyncio
    async def test_create_menu_success(self, menu_service, mock_menu_repo, mock_session):
        """测试创建菜单成功。"""
        mock_menu_repo.get_by_name = AsyncMock(return_value=None)

        meta = MenuMeta(id="meta-id-1", title="测试菜单", icon="menu", is_show_menu=1, is_keepalive=1)
        mock_menu_repo.create_meta = AsyncMock(return_value=meta)

        created_menu = Menu(id="menu-id-1", name="test_menu", menu_type=0, path="/test", rank=0, is_active=1, meta_id="meta-id-1", meta=meta)
        mock_menu_repo.create = AsyncMock(return_value=created_menu)
        mock_menu_repo.get_by_id = AsyncMock(return_value=created_menu)

        dto = MenuCreateDTO(name="test_menu", menuType=0, path="/test", title="测试菜单", isActive=1)
        result = await menu_service.create_menu(dto)

        assert result.name == "test_menu"
        assert result.menuType == 0
        mock_menu_repo.create_meta.assert_called_once()
        mock_menu_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_menu_duplicate_name(self, menu_service, mock_menu_repo):
        """测试创建菜单时名称重复。"""
        existing = Menu(name="existing_menu")
        mock_menu_repo.get_by_name = AsyncMock(return_value=existing)

        dto = MenuCreateDTO(name="existing_menu", menuType=0, isActive=1)
        with pytest.raises(ConflictError) as exc_info:
            await menu_service.create_menu(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_menu_parent_not_found(self, menu_service, mock_menu_repo):
        """测试创建菜单时父菜单不存在。"""
        mock_menu_repo.get_by_name = AsyncMock(return_value=None)
        mock_menu_repo.get_by_id = AsyncMock(return_value=None)

        dto = MenuCreateDTO(name="child_menu", menuType=1, parentId="non-existent-id", isActive=1)
        with pytest.raises(NotFoundError):
            await menu_service.create_menu(dto)

    @pytest.mark.asyncio
    async def test_update_menu_success(self, menu_service, mock_menu_repo, mock_session):
        """测试更新菜单成功。"""
        meta = MenuMeta(id="meta-id-1", title="旧标题", icon="menu", is_show_menu=1, is_keepalive=1)
        existing_menu = Menu(id="menu-id-1", name="test_menu", menu_type=0, path="/test", rank=0, is_active=1, meta_id="meta-id-1", meta=meta)
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing_menu)
        mock_menu_repo.get_by_name = AsyncMock(return_value=None)
        mock_menu_repo.update = AsyncMock()
        mock_menu_repo.update_meta = AsyncMock()

        dto = MenuUpdateDTO(name="updated_menu", title="新标题")
        result = await menu_service.update_menu("menu-id-1", dto)

        assert result.name == "updated_menu"
        mock_menu_repo.update.assert_called_once()
        mock_menu_repo.update_meta.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_menu_not_found(self, menu_service, mock_menu_repo):
        """测试更新不存在的菜单。"""
        mock_menu_repo.get_by_id = AsyncMock(return_value=None)

        dto = MenuUpdateDTO(name="updated_menu")
        with pytest.raises(NotFoundError):
            await menu_service.update_menu("non-existent-id", dto)

    @pytest.mark.asyncio
    async def test_update_menu_circular_reference(self, menu_service, mock_menu_repo):
        """测试更新菜单时设置自身为父菜单。"""
        existing_menu = Menu(id="menu-id-1", name="test_menu", menu_type=0)
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing_menu)

        dto = MenuUpdateDTO(parentId="menu-id-1")
        with pytest.raises(ConflictError) as exc_info:
            await menu_service.update_menu("menu-id-1", dto)
        assert "自己" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_menu_success(self, menu_service, mock_menu_repo, mock_session):
        """测试删除菜单成功。"""
        meta = MenuMeta(id="meta-id-1", title="测试")
        existing_menu = Menu(id="menu-id-1", name="test_menu", meta_id="meta-id-1")
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing_menu)
        mock_menu_repo.get_by_parent_id = AsyncMock(return_value=[])
        mock_menu_repo.delete = AsyncMock(return_value=True)
        mock_menu_repo.delete_meta = AsyncMock(return_value=True)

        result = await menu_service.delete_menu("menu-id-1")
        assert result is True
        mock_menu_repo.delete.assert_called_once_with("menu-id-1", session=mock_session)
        mock_menu_repo.delete_meta.assert_called_once_with("meta-id-1", session=mock_session)

    @pytest.mark.asyncio
    async def test_delete_menu_with_children(self, menu_service, mock_menu_repo):
        """测试删除有子菜单的菜单。"""
        existing_menu = Menu(id="menu-id-1", name="parent_menu")
        child_menu = Menu(id="menu-id-2", name="child_menu", parent_id="menu-id-1")
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing_menu)
        mock_menu_repo.get_by_parent_id = AsyncMock(return_value=[child_menu])

        with pytest.raises(ConflictError) as exc_info:
            await menu_service.delete_menu("menu-id-1")
        assert "子菜单" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_menu_tree(self, menu_service, mock_menu_repo):
        """测试获取菜单树。"""
        meta1 = MenuMeta(id="m1", title="根菜单")
        meta2 = MenuMeta(id="m2", title="子菜单")
        menus = [Menu(id="1", name="root", menu_type=0, parent_id=None, rank=0, meta=meta1), Menu(id="2", name="child", menu_type=1, parent_id="1", rank=0, meta=meta2)]
        mock_menu_repo.get_all = AsyncMock(return_value=menus)

        tree = await menu_service.get_menu_tree()

        assert len(tree) == 1
        assert tree[0]["name"] == "root"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["name"] == "child"
