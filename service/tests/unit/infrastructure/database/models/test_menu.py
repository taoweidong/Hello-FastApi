"""Menu 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.menu import Menu


@pytest.mark.unit
class TestMenuModel:
    """Menu ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_menus。"""
        assert Menu.__tablename__ == "sys_menus"

    def test_is_sqlmodel_table(self):
        """Menu 应继承 SQLModel 并映射为表。"""
        assert issubclass(Menu, SQLModel)
        assert hasattr(Menu, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        menu = Menu(name="用户管理", meta_id="meta-1")
        assert menu.id is not None
        assert len(menu.id) == 32

    def test_field_defaults(self):
        """测试字段默认值。"""
        menu = Menu(name="用户管理", meta_id="meta-1")
        assert menu.menu_type == 0
        assert menu.rank == 0
        assert menu.path == ""
        assert menu.is_active == 1

    def test_optional_fields_default_none(self):
        """可选字段默认应为 None。"""
        menu = Menu(name="用户管理", meta_id="meta-1")
        assert menu.component is None
        assert menu.method is None
        assert menu.creator_id is None
        assert menu.modifier_id is None
        assert menu.parent_id is None
        assert menu.created_time is None
        assert menu.updated_time is None
        assert menu.description is None

    def test_field_max_length(self):
        """字段应有正确的 max_length 限制。"""
        assert Menu.name.type.length == 128
        assert Menu.path.type.length == 255
        assert Menu.component.type.length == 255
        assert Menu.method.type.length == 10
        assert Menu.creator_id.type.length == 150
        assert Menu.modifier_id.type.length == 150
        assert Menu.description.type.length == 256

    def test_name_is_unique(self):
        """name 字段应标记为 unique。"""
        assert Menu.name.unique is True

    def test_meta_id_is_required(self):
        """meta_id 应为必填字段。"""
        assert Menu.meta_id is not None

    def test_to_domain(self):
        """to_domain 应返回 MenuEntity 实例。"""
        from src.domain.entities.menu import MenuEntity

        menu = Menu(
            id="menu-1",
            menu_type=1,
            name="用户管理",
            rank=1,
            path="/system/user",
            component="system/user/index",
            is_active=1,
            meta_id="meta-1",
        )
        entity = menu.to_domain()
        assert isinstance(entity, MenuEntity)
        assert entity.id == "menu-1"
        assert entity.name == "用户管理"
        assert entity.path == "/system/user"
        assert entity.meta_id == "meta-1"

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.menu import MenuEntity

        entity = MenuEntity(
            id="menu-2",
            menu_type=2,
            name="创建用户",
            rank=2,
            path="/system/user/create",
            component=None,
            is_active=1,
            method="POST",
            meta_id="meta-2",
        )
        menu = Menu.from_domain(entity)
        assert isinstance(menu, Menu)
        assert menu.id == "menu-2"
        assert menu.menu_type == 2
        assert menu.name == "创建用户"
        assert menu.method == "POST"

    def test_repr(self):
        """__repr__ 应包含 id 和 name。"""
        menu = Menu(name="角色管理", meta_id="meta-3")
        menu.id = "menu-123"
        r = repr(menu)
        assert "Menu" in r
        assert "menu-123" in r
        assert "角色管理" in r
