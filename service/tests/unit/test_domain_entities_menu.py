"""菜单领域实体的单元测试。

测试 MenuEntity 的所有状态查询属性、业务规则方法和工厂方法。
"""

import pytest

from src.domain.entities.menu import MenuEntity


@pytest.mark.unit
class TestMenuEntity:
    """MenuEntity 测试类。"""

    # ---- 类型常量测试 ----

    def test_directory_constant(self):
        """测试 DIRECTORY 类型常量。"""
        assert MenuEntity.DIRECTORY == 0

    def test_menu_page_constant(self):
        """测试 MENU_PAGE 类型常量。"""
        assert MenuEntity.MENU_PAGE == 1

    def test_permission_constant(self):
        """测试 PERMISSION 类型常量。"""
        assert MenuEntity.PERMISSION == 2

    # ---- 状态查询属性测试 ----

    def test_is_directory_when_directory_type(self):
        """测试 is_directory 属性（目录类型）。"""
        menu = MenuEntity(id="menu-1", name="System", menu_type=0, path="/system")
        assert menu.is_directory is True
        assert menu.is_menu_page is False
        assert menu.is_permission is False

    def test_is_menu_page_when_menu_type(self):
        """测试 is_menu_page 属性（菜单页面类型）。"""
        menu = MenuEntity(id="menu-1", name="User", menu_type=1, path="/user")
        assert menu.is_menu_page is True
        assert menu.is_directory is False

    def test_is_permission_when_permission_type(self):
        """测试 is_permission 属性（权限类型）。"""
        menu = MenuEntity(id="menu-1", name="user:view", menu_type=2, path="/user", method="GET")
        assert menu.is_permission is True
        assert menu.is_directory is False

    def test_is_active_menu_when_active(self):
        """测试 is_active_menu 属性（已启用）。"""
        menu = MenuEntity(id="menu-1", name="System", menu_type=0, is_active=1)
        assert menu.is_active_menu is True

    def test_is_active_menu_when_inactive(self):
        """测试 is_active_menu 属性（未启用）。"""
        menu = MenuEntity(id="menu-1", name="System", menu_type=0, is_active=0)
        assert menu.is_active_menu is False

    # ---- 业务规则方法测试 ----

    def test_is_circular_reference_true(self):
        """测试 is_circular_reference 方法（自身引用）。"""
        menu = MenuEntity(id="menu-1", name="System", menu_type=0)
        assert menu.is_circular_reference("menu-1") is True

    def test_is_circular_reference_different_parent(self):
        """测试 is_circular_reference 方法（不同父节点）。"""
        menu = MenuEntity(id="menu-1", name="System", menu_type=0)
        assert menu.is_circular_reference("menu-2") is False

    def test_is_circular_reference_none(self):
        """测试 is_circular_reference 方法（无父节点）。"""
        menu = MenuEntity(id="menu-1", name="System", menu_type=0)
        assert menu.is_circular_reference(None) is False

    # ---- 状态变更方法测试 ----

    def test_update_info_with_all_fields(self):
        """测试 update_info 方法（更新所有字段）。"""
        menu = MenuEntity(id="menu-1", name="System", menu_type=0, path="/system")
        menu.update_info(
            menu_type=1,
            name="用户管理",
            path="/system/user",
            component="system/user",
            rank=1,
            is_active=1,
            method="GET",
            parent_id="parent-1",
            description="描述",
        )
        assert menu.menu_type == 1
        assert menu.name == "用户管理"
        assert menu.path == "/system/user"
        assert menu.component == "system/user"
        assert menu.rank == 1
        assert menu.is_active == 1
        assert menu.method == "GET"
        assert menu.parent_id == "parent-1"
        assert menu.description == "描述"

    def test_update_info_with_partial_fields(self):
        """测试 update_info 方法（部分字段）。"""
        menu = MenuEntity(id="menu-1", name="System", menu_type=0)
        menu.update_info(name="新名称", rank=5)
        assert menu.name == "新名称"
        assert menu.rank == 5
        assert menu.menu_type == 0

    def test_update_info_ignore_none_fields(self):
        """测试 update_info 方法（忽略 None 字段）。"""
        menu = MenuEntity(id="menu-1", name="System", menu_type=0, rank=1)
        menu.update_info(name=None, rank=None)
        assert menu.name == "System"
        assert menu.rank == 1

    # ---- 工厂方法测试 ----

    def test_create_new_directory(self):
        """测试 create_new 工厂方法（目录类型）。"""
        menu = MenuEntity.create_new(
            name="System",
            menu_type=0,
            path="/system",
            component=None,
            rank=1,
            is_active=1,
            method=None,
            parent_id=None,
            description="系统管理",
        )
        assert menu.id is not None
        assert len(menu.id) == 32
        assert menu.name == "System"
        assert menu.menu_type == 0
        assert menu.path == "/system"
        assert menu.is_active == 1

    def test_create_new_menu_page(self):
        """测试 create_new 工厂方法（菜单页面类型）。"""
        menu = MenuEntity.create_new(
            name="User",
            menu_type=1,
            path="/system/user",
            component="system/user/index",
            rank=1,
        )
        assert menu.menu_type == 1
        assert menu.component == "system/user/index"

    def test_create_new_permission(self):
        """测试 create_new 工厂方法（权限类型）。"""
        menu = MenuEntity.create_new(
            name="user:view",
            menu_type=2,
            path="/system/user",
            method="GET",
        )
        assert menu.menu_type == 2
        assert menu.method == "GET"

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        menu = MenuEntity.create_new(name="Test")
        assert menu.name == "Test"
        assert menu.menu_type == 0
        assert menu.path == ""
        assert menu.is_active == 1
        assert menu.rank == 0
