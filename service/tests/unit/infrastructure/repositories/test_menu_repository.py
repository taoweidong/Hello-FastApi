"""MenuRepository 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.infrastructure.repositories.menu_repository import MenuRepository


@pytest.mark.unit
class TestMenuRepository:
    """MenuRepository 测试类。"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return MenuRepository(mock_session)

    def test_init(self, repo, mock_session):
        """测试初始化设置 session。"""
        assert repo.session is mock_session

    @pytest.mark.asyncio
    async def test_get_all(self, repo, mock_session):
        """测试 get_all 返回所有菜单。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = MenuEntity(id="1", name="首页", rank=1, menu_type="M")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, mock_session):
        """测试 get_by_id 找到菜单。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = MenuEntity(id="1", name="系统管理")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("1")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo, mock_session):
        """测试 get_by_id 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, repo, mock_session):
        """测试 create 创建菜单。"""
        entity = MenuEntity(id="1", name="新菜单", menu_type="M", rank=1)
        mock_model = MagicMock()
        mock_model.id = "1"
        mock_model.to_domain.return_value = entity

        def exec_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.first.return_value = mock_model
            return mock_result

        mock_session.exec = AsyncMock(side_effect=exec_side_effect)

        with patch("src.infrastructure.repositories.menu_repository.Menu.from_domain", return_value=mock_model):
            result = await repo.create(entity)

        assert result is not None
        assert result.id == "1"

    @pytest.mark.asyncio
    async def test_update(self, repo, mock_session):
        """测试 update 更新菜单。"""
        entity = MenuEntity(
            id="1",
            name="更新菜单",
            menu_type="M",
            rank=2,
            is_active=1,
            parent_id=None,
            creator_id="u1",
            modifier_id="u2",
            description="desc",
        )
        mock_merged = MagicMock()
        mock_merged.id = "1"
        mock_merged.to_domain.return_value = entity

        def exec_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.first.return_value = mock_merged
            return mock_result

        mock_session.exec = AsyncMock(side_effect=exec_side_effect)

        result = await repo.update(entity)

        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_success(self, repo, mock_session):
        """测试 delete 成功删除。"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.delete("menu-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repo, mock_session):
        """测试 delete 未找到返回 False。"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.delete("not-exist")
        assert result is False

    @pytest.mark.asyncio
    async def test_count(self, repo, mock_session):
        """测试 count 返回总数。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 10
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count()
        assert result == 10

    @pytest.mark.asyncio
    async def test_get_by_name_found(self, repo, mock_session):
        """测试 get_by_name 找到菜单。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = MenuEntity(id="1", name="系统管理", menu_type="M")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_name("系统管理")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_parent_id(self, repo, mock_session):
        """测试 get_by_parent_id 返回子菜单。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = MenuEntity(id="2", name="子菜单", rank=1, parent_id="1")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_parent_id("1")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_meta(self, repo, mock_session):
        """测试 create_meta 创建元数据。"""
        entity = MenuMetaEntity(id="meta-1", title="系统管理")
        mock_model = MagicMock()
        mock_model.id = "meta-1"
        mock_model.to_domain.return_value = entity

        def exec_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.first.return_value = mock_model
            return mock_result

        mock_session.exec = AsyncMock(side_effect=exec_side_effect)

        with patch("src.infrastructure.repositories.menu_repository.MenuMeta.from_domain", return_value=mock_model):
            result = await repo.create_meta(entity)

        assert result is not None

    @pytest.mark.asyncio
    async def test_update_meta(self, repo, mock_session):
        """测试 update_meta 更新元数据。"""
        entity = MenuMetaEntity(
            id="meta-1",
            title="新标题",
            icon="setting",
            r_svg_name=None,
            is_show_menu=1,
            is_show_parent=0,
            is_keepalive=0,
            frame_url=None,
            frame_loading=0,
            transition_enter=None,
            transition_leave=None,
            is_hidden_tag=0,
            fixed_tag=0,
            dynamic_level=None,
            creator_id="u1",
            modifier_id="u2",
            description="desc",
        )
        mock_merged = MagicMock()
        mock_merged.id = "meta-1"
        mock_merged.to_domain.return_value = entity

        def exec_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.first.return_value = mock_merged
            return mock_result

        mock_session.exec = AsyncMock(side_effect=exec_side_effect)

        result = await repo.update_meta(entity)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_meta_by_id_found(self, repo, mock_session):
        """测试 get_meta_by_id 找到元数据。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = MenuMetaEntity(id="meta-1", title="系统管理")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_meta_by_id("meta-1")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_meta_by_id_not_found(self, repo, mock_session):
        """测试 get_meta_by_id 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_meta_by_id("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_meta_success(self, repo, mock_session):
        """测试 delete_meta 成功删除。"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.delete_meta("meta-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_all_empty(self, repo, mock_session):
        """测试 get_all 无数据返回空列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, repo, mock_session):
        """测试 get_by_name 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_name("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_parent_id_empty(self, repo, mock_session):
        """测试 get_by_parent_id 无子菜单返回空列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_parent_id("parent-1")

        assert result == []
