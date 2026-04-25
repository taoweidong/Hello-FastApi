"""菜单仓储接口的单元测试。

测试 MenuRepositoryInterface 抽象基类的方法签名和返回类型。
"""

import pytest

from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.repositories.menu_repository import MenuRepositoryInterface


class ConcreteMenuRepository(MenuRepositoryInterface):
    """用于测试的 MenuRepositoryInterface 最小化具体实现。"""

    def __init__(self, session=None):
        self.session = session

    async def get_all(self) -> list[MenuEntity]:
        return []

    async def get_by_id(self, menu_id: str) -> MenuEntity | None:
        return None

    async def create(self, menu: MenuEntity) -> MenuEntity:
        return menu

    async def update(self, menu: MenuEntity) -> MenuEntity:
        return menu

    async def delete(self, menu_id: str) -> bool:
        return True

    async def get_by_name(self, name: str) -> MenuEntity | None:
        return None

    async def get_by_parent_id(self, parent_id: str | None) -> list[MenuEntity]:
        return []

    async def create_meta(self, meta: MenuMetaEntity) -> MenuMetaEntity:
        return meta

    async def update_meta(self, meta: MenuMetaEntity) -> MenuMetaEntity:
        return meta

    async def get_meta_by_id(self, meta_id: str) -> MenuMetaEntity | None:
        return None

    async def delete_meta(self, meta_id: str) -> bool:
        return True


@pytest.mark.unit
class TestMenuRepositoryInterface:
    """MenuRepositoryInterface 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            MenuRepositoryInterface(session=None)  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        repo = ConcreteMenuRepository()
        assert repo is not None
        assert isinstance(repo, MenuRepositoryInterface)

    # ---- get_all ----

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        """测试 get_all 返回列表。"""
        repo = ConcreteMenuRepository()
        result = await repo.get_all()
        assert isinstance(result, list)

    # ---- get_by_id ----

    @pytest.mark.asyncio
    async def test_get_by_id_accepts_str(self):
        """测试 get_by_id 接受字符串参数。"""
        repo = ConcreteMenuRepository()
        result = await repo.get_by_id("menu-1")
        assert result is None

    # ---- create ----

    @pytest.mark.asyncio
    async def test_create_returns_menu_entity(self):
        """测试 create 返回菜单实体。"""
        repo = ConcreteMenuRepository()
        entity = MenuEntity(id="menu-1", name="系统管理")
        result = await repo.create(entity)
        assert isinstance(result, MenuEntity)

    # ---- update ----

    @pytest.mark.asyncio
    async def test_update_returns_menu_entity(self):
        """测试 update 返回菜单实体。"""
        repo = ConcreteMenuRepository()
        entity = MenuEntity(id="menu-1", name="系统管理")
        result = await repo.update(entity)
        assert isinstance(result, MenuEntity)

    # ---- delete ----

    @pytest.mark.asyncio
    async def test_delete_returns_bool(self):
        """测试 delete 返回布尔值。"""
        repo = ConcreteMenuRepository()
        result = await repo.delete("menu-1")
        assert isinstance(result, bool)

    # ---- get_by_name ----

    @pytest.mark.asyncio
    async def test_get_by_name_accepts_str(self):
        """测试 get_by_name 接受字符串参数。"""
        repo = ConcreteMenuRepository()
        result = await repo.get_by_name("系统管理")
        assert result is None

    # ---- get_by_parent_id ----

    @pytest.mark.asyncio
    async def test_get_by_parent_id_accepts_str_or_none(self):
        """测试 get_by_parent_id 接受字符串或 None。"""
        repo = ConcreteMenuRepository()
        result = await repo.get_by_parent_id("parent-1")
        assert isinstance(result, list)
        result_none = await repo.get_by_parent_id(None)
        assert isinstance(result_none, list)

    # ---- create_meta ----

    @pytest.mark.asyncio
    async def test_create_meta_returns_menu_meta_entity(self):
        """测试 create_meta 返回菜单元数据实体。"""
        repo = ConcreteMenuRepository()
        meta = MenuMetaEntity(id="meta-1", title="系统管理")
        result = await repo.create_meta(meta)
        assert isinstance(result, MenuMetaEntity)

    # ---- update_meta ----

    @pytest.mark.asyncio
    async def test_update_meta_returns_menu_meta_entity(self):
        """测试 update_meta 返回菜单元数据实体。"""
        repo = ConcreteMenuRepository()
        meta = MenuMetaEntity(id="meta-1", title="系统管理")
        result = await repo.update_meta(meta)
        assert isinstance(result, MenuMetaEntity)

    # ---- get_meta_by_id ----

    @pytest.mark.asyncio
    async def test_get_meta_by_id_accepts_str(self):
        """测试 get_meta_by_id 接受字符串参数。"""
        repo = ConcreteMenuRepository()
        result = await repo.get_meta_by_id("meta-1")
        assert result is None

    # ---- delete_meta ----

    @pytest.mark.asyncio
    async def test_delete_meta_returns_bool(self):
        """测试 delete_meta 返回布尔值。"""
        repo = ConcreteMenuRepository()
        result = await repo.delete_meta("meta-1")
        assert isinstance(result, bool)
