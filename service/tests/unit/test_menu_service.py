"""菜单服务的单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.menu_dto import MenuCreateDTO, MenuUpdateDTO
from src.application.services.menu_service import MenuService
from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.exceptions import ConflictError, NotFoundError


@pytest.mark.unit
class TestMenuService:
    """MenuService 测试类。"""

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
    def menu_service(self, mock_menu_repo):
        """创建菜单服务实例。"""
        return MenuService(menu_repo=mock_menu_repo)

    @pytest.mark.asyncio
    async def test_create_menu_success(self, menu_service, mock_menu_repo):
        """测试创建菜单成功。"""
        mock_menu_repo.get_by_name = AsyncMock(return_value=None)

        # 模拟 create_meta 和 create 的返回
        created_meta = MenuMetaEntity(id="meta-id-1", title="测试菜单", icon="menu", is_show_menu=1, is_keepalive=1)
        created_menu = MenuEntity(id="menu-id-1", name="test_menu", menu_type=0, path="/test", rank=0, is_active=1, meta_id="meta-id-1", meta=created_meta)
        mock_menu_repo.create_meta = AsyncMock(return_value=created_meta)
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
        existing = MenuEntity(id="ex-id", name="existing_menu")
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
    async def test_update_menu_success(self, menu_service, mock_menu_repo):
        """测试更新菜单成功。"""
        meta = MenuMetaEntity(id="meta-id-1", title="旧标题", icon="menu", is_show_menu=1, is_keepalive=1)
        existing_menu = MenuEntity(id="menu-id-1", name="test_menu", menu_type=0, path="/test", rank=0, is_active=1, meta_id="meta-id-1", meta=meta)
        # get_by_id called: first for fetch, second for re-read after update
        updated_menu = MenuEntity(id="menu-id-1", name="updated_menu", menu_type=0, path="/test", rank=0, is_active=1, meta_id="meta-id-1", meta=meta)
        mock_menu_repo.get_by_id = AsyncMock(side_effect=[existing_menu, updated_menu])
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
        existing_menu = MenuEntity(id="menu-id-1", name="test_menu", menu_type=0)
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing_menu)

        dto = MenuUpdateDTO(parentId="menu-id-1")
        with pytest.raises(ConflictError) as exc_info:
            await menu_service.update_menu("menu-id-1", dto)
        assert "自己" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_menu_success(self, menu_service, mock_menu_repo):
        """测试删除菜单成功。"""
        meta = MenuMetaEntity(id="meta-id-1", title="测试")
        existing_menu = MenuEntity(id="menu-id-1", name="test_menu", meta_id="meta-id-1", meta=meta)
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing_menu)
        mock_menu_repo.get_by_parent_id = AsyncMock(return_value=[])
        mock_menu_repo.delete = AsyncMock(return_value=True)
        mock_menu_repo.delete_meta = AsyncMock(return_value=True)

        result = await menu_service.delete_menu("menu-id-1")
        assert result is True
        mock_menu_repo.delete.assert_called_once_with("menu-id-1")
        mock_menu_repo.delete_meta.assert_called_once_with("meta-id-1")

    @pytest.mark.asyncio
    async def test_delete_menu_with_children(self, menu_service, mock_menu_repo):
        """测试删除有子菜单的菜单。"""
        existing_menu = MenuEntity(id="menu-id-1", name="parent_menu")
        child_menu = MenuEntity(id="menu-id-2", name="child_menu", parent_id="menu-id-1")
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing_menu)
        mock_menu_repo.get_by_parent_id = AsyncMock(return_value=[child_menu])

        with pytest.raises(ConflictError) as exc_info:
            await menu_service.delete_menu("menu-id-1")
        assert "子菜单" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_menu_tree(self, menu_service, mock_menu_repo):
        """测试获取菜单树。"""
        meta1 = MenuMetaEntity(id="m1", title="根菜单")
        meta2 = MenuMetaEntity(id="m2", title="子菜单")
        menus = [MenuEntity(id="1", name="root", menu_type=0, parent_id=None, rank=0, meta=meta1), MenuEntity(id="2", name="child", menu_type=1, parent_id="1", rank=0, meta=meta2)]
        mock_menu_repo.get_all = AsyncMock(return_value=menus)

        tree = await menu_service.get_menu_tree()

        assert len(tree) == 1
        assert tree[0]["name"] == "root"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["name"] == "child"

    @pytest.mark.asyncio
    async def test_get_menu_list(self, menu_service, mock_menu_repo):
        """测试获取扁平菜单列表。"""
        meta = MenuMetaEntity(id="m1", title="菜单")
        menus = [MenuEntity(id="1", name="test", menu_type=0, rank=0, meta=meta)]
        mock_menu_repo.get_all = AsyncMock(return_value=menus)

        result = await menu_service.get_menu_list()
        assert len(result) == 1
        assert result[0]["name"] == "test"

    @pytest.mark.asyncio
    async def test_get_menu_tree_empty(self, menu_service, mock_menu_repo):
        """测试获取空菜单树。"""
        mock_menu_repo.get_all = AsyncMock(return_value=[])
        tree = await menu_service.get_menu_tree()
        assert tree == []

    @pytest.mark.asyncio
    async def test_get_user_menus(self, menu_service, mock_menu_repo):
        """测试获取用户菜单。"""
        meta = MenuMetaEntity(id="m1", title="菜单")
        menus = [MenuEntity(id="1", name="test", menu_type=0, rank=0, meta=meta)]
        mock_menu_repo.get_all = AsyncMock(return_value=menus)

        result = await menu_service.get_user_menus("user-1", [])
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_menus_from_cache(self, mock_menu_repo):
        """测试从缓存获取菜单。"""
        cache = AsyncMock()
        cached = [{"id": "1", "menu_type": 0, "name": "cached", "rank": 1, "path": "/cached", "component": "", "is_active": 1, "method": "", "creator_id": None, "modifier_id": None, "parent_id": None, "meta_id": "m1", "created_time": None, "updated_time": None, "description": None, "meta": {"id": "m1", "title": "缓存菜单", "icon": "", "r_svg_name": "", "is_show_menu": 1, "is_show_parent": 0, "is_keepalive": 0, "frame_url": "", "frame_loading": 1, "transition_enter": "", "transition_leave": "", "is_hidden_tag": 0, "fixed_tag": 0, "dynamic_level": 0}}]
        cache.get_all_menus = AsyncMock(return_value=cached)
        service = MenuService(menu_repo=mock_menu_repo, cache_service=cache)

        menus = await service._get_all_menus()
        assert len(menus) == 1
        assert menus[0].id == "1"
        assert menus[0].meta.title == "缓存菜单"

    @pytest.mark.asyncio
    async def test_create_menu_loaded_is_none(self, menu_service, mock_menu_repo):
        """测试创建菜单后重载返回 None。"""
        created_meta = MenuMetaEntity(id="meta-id-1", title="测试")
        created_menu = MenuEntity(id="menu-id-1", name="test", menu_type=0, meta_id="meta-id-1")
        mock_menu_repo.get_by_name = AsyncMock(return_value=None)
        mock_menu_repo.create_meta = AsyncMock(return_value=created_meta)
        mock_menu_repo.create = AsyncMock(return_value=created_menu)
        mock_menu_repo.get_by_id = AsyncMock(return_value=None)

        dto = MenuCreateDTO(name="test", menuType=0, isActive=1)
        with pytest.raises(NotFoundError) as exc_info:
            await menu_service.create_menu(dto)
        assert "无法加载" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_menu_parent_not_found(self, menu_service, mock_menu_repo):
        """测试更新菜单时父菜单不存在。"""
        existing = MenuEntity(id="menu-id-1", name="test", menu_type=0)
        mock_menu_repo.get_by_id = AsyncMock(side_effect=[existing, None])

        dto = MenuUpdateDTO(parentId="non-existent")
        with pytest.raises(NotFoundError) as exc_info:
            await menu_service.update_menu("menu-id-1", dto)
        assert "父菜单" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_menu_duplicate_name(self, menu_service, mock_menu_repo):
        """测试更新菜单时名称与其他菜单重复。"""
        existing = MenuEntity(id="menu-id-1", name="test", menu_type=0)
        other = MenuEntity(id="menu-id-2", name="test2")
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing)
        mock_menu_repo.get_by_name = AsyncMock(return_value=other)

        dto = MenuUpdateDTO(name="test2")
        with pytest.raises(ConflictError) as exc_info:
            await menu_service.update_menu("menu-id-1", dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_menu_parent_id_cleared(self, menu_service, mock_menu_repo):
        """测试更新菜单时清除 parentId。"""
        meta = MenuMetaEntity(id="meta-id-1", title="菜单")
        existing = MenuEntity(id="menu-id-1", name="test", menu_type=0, parent_id="parent-1", meta=meta)
        updated = MenuEntity(id="menu-id-1", name="test", menu_type=0, parent_id=None, meta=meta)
        mock_menu_repo.get_by_id = AsyncMock(side_effect=[existing, updated])
        mock_menu_repo.get_by_name = AsyncMock(return_value=None)
        mock_menu_repo.update = AsyncMock()

        dto = MenuUpdateDTO(parentId="")
        result = await menu_service.update_menu("menu-id-1", dto)
        assert result.parentId is None or result.parentId == ""

    @pytest.mark.asyncio
    async def test_delete_menu_without_meta_id(self, menu_service, mock_menu_repo):
        """测试删除没有 meta_id 的菜单。"""
        existing = MenuEntity(id="menu-id-1", name="test", meta_id=None)
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing)
        mock_menu_repo.get_by_parent_id = AsyncMock(return_value=[])
        mock_menu_repo.delete = AsyncMock(return_value=True)

        result = await menu_service.delete_menu("menu-id-1")
        assert result is True
        mock_menu_repo.delete_meta.assert_not_called()

    def test_entity_to_dict_with_meta(self, menu_service):
        """测试 _entity_to_dict 含 meta。"""
        meta = MenuMetaEntity(id="m1", title="测试", icon="home")
        menu = MenuEntity(id="1", name="test", menu_type=0, path="/test", rank=1, meta=meta)
        result = menu_service._entity_to_dict(menu)
        assert result["id"] == "1"
        assert result["meta"]["title"] == "测试"

    def test_entity_to_dict_without_meta(self, menu_service):
        """测试 _entity_to_dict 不含 meta。"""
        menu = MenuEntity(id="1", name="test", menu_type=0, path="/test", rank=1)
        result = menu_service._entity_to_dict(menu)
        assert "meta" not in result

    def test_dict_to_entity_with_meta(self, menu_service):
        """测试 _dict_to_entity 含 meta。"""
        data = {"id": "1", "menu_type": 0, "name": "test", "rank": 1, "path": "/test", "component": "", "is_active": 1, "method": "", "creator_id": None, "modifier_id": None, "parent_id": None, "meta_id": "m1", "created_time": None, "updated_time": None, "description": None, "meta": {"id": "m1", "title": "测试", "icon": "home", "r_svg_name": "", "is_show_menu": 1, "is_show_parent": 0, "is_keepalive": 0, "frame_url": "", "frame_loading": 1, "transition_enter": "", "transition_leave": "", "is_hidden_tag": 0, "fixed_tag": 0, "dynamic_level": 0}}
        entity = menu_service._dict_to_entity(data)
        assert entity.id == "1"
        assert entity.meta.title == "测试"

    def test_dict_to_entity_without_meta(self, menu_service):
        """测试 _dict_to_entity 不含 meta。"""
        data = {"id": "1", "menu_type": 0, "name": "test", "rank": 1, "path": "/test", "component": "", "is_active": 1, "method": "", "creator_id": None, "modifier_id": None, "parent_id": None, "meta_id": None, "created_time": None, "updated_time": None, "description": None}
        entity = menu_service._dict_to_entity(data)
        assert entity.id == "1"
        assert entity.meta is None

    def test_to_response_without_meta(self, menu_service):
        """测试 _to_response 不含 meta。"""
        menu = MenuEntity(id="1", name="test", menu_type=0, rank=1)
        result = menu_service._to_response(menu)
        assert result["id"] == "1"
        assert result["meta"] is not None
        assert result["meta"]["title"] == "test"

    def test_to_response_dto_with_meta(self, menu_service):
        """测试 _to_response_dto 含 meta。"""
        meta = MenuMetaEntity(id="m1", title="测试", icon="home")
        menu = MenuEntity(id="1", name="test", menu_type=0, meta=meta)
        result = menu_service._to_response_dto(menu)
        assert result.id == "1"
        assert result.meta is not None
        assert result.meta.title == "测试"

    def test_to_response_dto_without_meta(self, menu_service):
        """测试 _to_response_dto 不含 meta。"""
        menu = MenuEntity(id="1", name="test", menu_type=0)
        result = menu_service._to_response_dto(menu)
        assert result.id == "1"
        assert result.meta is None

    def test_build_tree_empty(self, menu_service):
        """测试构建空菜单树。"""
        tree = menu_service._build_tree([], None)
        assert tree == []

    def test_build_tree_sorted(self, menu_service):
        """测试菜单树按 rank 排序。"""
        m1 = MenuEntity(id="2", name="second", menu_type=0, rank=2)
        m2 = MenuEntity(id="1", name="first", menu_type=0, rank=1)
        tree = menu_service._build_tree([m1, m2], None)
        assert tree[0]["name"] == "first"
        assert tree[1]["name"] == "second"

    @pytest.mark.asyncio
    async def test_get_all_menus_cache_miss_sets_cache(self, mock_menu_repo):
        """测试缓存未命中时写入缓存。"""
        cache = AsyncMock()
        cache.get_all_menus = AsyncMock(return_value=None)
        service = MenuService(menu_repo=mock_menu_repo, cache_service=cache)
        menus = [MenuEntity(id="1", name="test", menu_type=0, rank=1)]
        mock_menu_repo.get_all = AsyncMock(return_value=menus)

        result = await service._get_all_menus()
        assert len(result) == 1
        cache.set_all_menus.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_menu_with_valid_parent(self, menu_service, mock_menu_repo):
        """测试更新菜单时设置已存在的父菜单。"""
        meta = MenuMetaEntity(id="m1", title="菜单")
        existing = MenuEntity(id="menu-id-1", name="test", menu_type=0, parent_id=None, meta=meta)
        parent = MenuEntity(id="parent-id", name="parent", menu_type=0)
        updated = MenuEntity(id="menu-id-1", name="test", menu_type=0, parent_id="parent-id", meta=meta)
        mock_menu_repo.get_by_id = AsyncMock(side_effect=[existing, parent, updated])
        mock_menu_repo.get_by_name = AsyncMock(return_value=None)
        mock_menu_repo.update = AsyncMock()

        dto = MenuUpdateDTO(parentId="parent-id")
        result = await menu_service.update_menu("menu-id-1", dto)
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_menu_reload_not_found(self, menu_service, mock_menu_repo):
        """测试更新菜单后重载时不存在。"""
        existing = MenuEntity(id="menu-id-1", name="test", menu_type=0)
        mock_menu_repo.get_by_id = AsyncMock(side_effect=[existing, None])
        mock_menu_repo.get_by_name = AsyncMock(return_value=None)
        mock_menu_repo.update = AsyncMock()

        dto = MenuUpdateDTO(name="newname")
        with pytest.raises(NotFoundError):
            await menu_service.update_menu("menu-id-1", dto)

    def test_to_response_dto_with_meta_all_fields(self, menu_service):
        """测试 _to_response_dto 包含 meta 所有字段。"""
        meta = MenuMetaEntity(id="m1", title="测试", icon="home", r_svg_name="ri-home", is_show_menu=1, is_show_parent=0, is_keepalive=1, frame_url="http://x.com", frame_loading=1, transition_enter="fade", transition_leave="slide", is_hidden_tag=0, fixed_tag=1, dynamic_level=2)
        menu = MenuEntity(id="1", name="test", menu_type=0, meta=meta)
        result = menu_service._to_response_dto(menu)
        assert result.meta.title == "测试"
        assert result.meta.icon == "home"
        assert result.meta.dynamicLevel == 2

    @pytest.mark.asyncio
    async def test_delete_menu_not_found(self, menu_service, mock_menu_repo):
        """测试删除不存在的菜单。"""
        mock_menu_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await menu_service.delete_menu("non-existent-id")

    @pytest.mark.asyncio
    async def test_delete_menu_with_cache_service(self, mock_menu_repo):
        """测试删除菜单时使缓存失效。"""
        cache = AsyncMock()
        service = MenuService(menu_repo=mock_menu_repo, cache_service=cache)
        existing = MenuEntity(id="menu-id-1", name="test", meta_id=None)
        mock_menu_repo.get_by_id = AsyncMock(return_value=existing)
        mock_menu_repo.get_by_parent_id = AsyncMock(return_value=[])
        mock_menu_repo.delete = AsyncMock(return_value=True)

        result = await service.delete_menu("menu-id-1")
        assert result is True
        cache.invalidate_all_menus.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_menu_with_full_params(self, menu_service, mock_menu_repo):
        """测试创建菜单包含所有可选参数。"""
        mock_menu_repo.get_by_name = AsyncMock(return_value=None)
        created_meta = MenuMetaEntity(id="meta-id-1", title="完整菜单", icon="setting", is_show_menu=1, is_keepalive=0)
        created_menu = MenuEntity(id="menu-id-1", name="full_menu", menu_type=1, path="/full", component="Full", rank=5, is_active=1, method="GET", meta_id="meta-id-1", meta=created_meta)
        mock_menu_repo.create_meta = AsyncMock(return_value=created_meta)
        mock_menu_repo.create = AsyncMock(return_value=created_menu)
        mock_menu_repo.get_by_id = AsyncMock(return_value=created_menu)

        dto = MenuCreateDTO(name="full_menu", menuType=1, path="/full", component="Full", rank=5, isActive=1, method="GET", title="完整菜单", icon="setting", isShowMenu=1, isKeepalive=0)
        result = await menu_service.create_menu(dto)
        assert result.name == "full_menu"
        assert result.menuType == 1
