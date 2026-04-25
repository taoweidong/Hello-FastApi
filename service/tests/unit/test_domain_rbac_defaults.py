"""RBAC 默认数据的单元测试。

测试 src.domain.rbac_defaults 中的默认角色和菜单数据。
"""

import pytest

from src.domain import rbac_defaults


@pytest.mark.unit
class TestDefaultRoles:
    """DEFAULT_ROLES 测试类。"""

    def test_default_roles_type(self):
        """测试 DEFAULT_ROLES 是字典类型。"""
        assert isinstance(rbac_defaults.DEFAULT_ROLES, dict)

    def test_default_roles_keys(self):
        """测试 DEFAULT_ROLES 包含所有默认角色。"""
        assert "admin" in rbac_defaults.DEFAULT_ROLES
        assert "user" in rbac_defaults.DEFAULT_ROLES
        assert "moderator" in rbac_defaults.DEFAULT_ROLES

    def test_default_roles_admin_description(self):
        """测试 admin 角色描述。"""
        assert "管理员" in rbac_defaults.DEFAULT_ROLES["admin"]
        assert "所有权限" in rbac_defaults.DEFAULT_ROLES["admin"]

    def test_default_roles_user_description(self):
        """测试 user 角色描述。"""
        assert "普通用户" in rbac_defaults.DEFAULT_ROLES["user"]
        assert "只读" in rbac_defaults.DEFAULT_ROLES["user"]

    def test_default_roles_count(self):
        """测试默认角色数量。"""
        assert len(rbac_defaults.DEFAULT_ROLES) == 3


@pytest.mark.unit
class TestDefaultMenus:
    """DEFAULT_MENUS 测试类。"""

    def test_default_menus_type(self):
        """测试 DEFAULT_MENUS 是列表类型。"""
        assert isinstance(rbac_defaults.DEFAULT_MENUS, list)

    def test_default_menus_count(self):
        """测试默认菜单数量。"""
        assert len(rbac_defaults.DEFAULT_MENUS) > 0

    def test_default_menus_have_required_fields(self):
        """测试每个菜单包含必需字段。"""
        required_fields = ["name", "path", "menu_type"]
        for menu in rbac_defaults.DEFAULT_MENUS:
            for field in required_fields:
                assert field in menu, f"菜单缺少必需字段: {field}"

    def test_default_menus_system_directory(self):
        """测试系统管理目录。"""
        system_menu = next(m for m in rbac_defaults.DEFAULT_MENUS if m["name"] == "System")
        assert system_menu["menu_type"] == 0  # DIRECTORY
        assert system_menu["meta"]["title"] == "系统管理"

    def test_default_menus_user_menu(self):
        """测试用户管理菜单。"""
        user_menu = next(m for m in rbac_defaults.DEFAULT_MENUS if m["name"] == "User")
        assert user_menu["menu_type"] == 1  # MENU
        assert user_menu["parent_id"] == "System"

    def test_default_menus_permission_types(self):
        """测试权限类型菜单。"""
        permission_menus = [m for m in rbac_defaults.DEFAULT_MENUS if m["menu_type"] == 2]
        assert len(permission_menus) > 0
        for menu in permission_menus:
            assert "method" in menu, f"权限菜单缺少 method 字段: {menu['name']}"

    def test_default_menus_monitor_directory(self):
        """测试系统监控目录。"""
        monitor_menu = next(m for m in rbac_defaults.DEFAULT_MENUS if m["name"] == "Monitor")
        assert monitor_menu["menu_type"] == 0  # DIRECTORY


@pytest.mark.unit
class TestAdminMenuNames:
    """ADMIN_MENU_NAMES 测试类。"""

    def test_admin_menu_names_type(self):
        """测试 ADMIN_MENU_NAMES 是列表类型。"""
        assert isinstance(rbac_defaults.ADMIN_MENU_NAMES, list)

    def test_admin_menu_names_not_empty(self):
        """测试 ADMIN_MENU_NAMES 不为空。"""
        assert len(rbac_defaults.ADMIN_MENU_NAMES) > 0

    def test_admin_menu_names_contains_all_default_menus(self):
        """测试 ADMIN_MENU_NAMES 包含所有默认菜单。"""
        default_menu_names = [m["name"] for m in rbac_defaults.DEFAULT_MENUS]
        for name in default_menu_names:
            assert name in rbac_defaults.ADMIN_MENU_NAMES


@pytest.mark.unit
class TestUserMenuNames:
    """USER_MENU_NAMES 测试类。"""

    def test_user_menu_names_type(self):
        """测试 USER_MENU_NAMES 是列表类型。"""
        assert isinstance(rbac_defaults.USER_MENU_NAMES, list)

    def test_user_menu_names_not_empty(self):
        """测试 USER_MENU_NAMES 不为空。"""
        assert len(rbac_defaults.USER_MENU_NAMES) > 0

    def test_user_menu_names_subset_of_admin(self):
        """测试 USER_MENU_NAMES 是 ADMIN_MENU_NAMES 的子集。"""
        for name in rbac_defaults.USER_MENU_NAMES:
            assert name in rbac_defaults.ADMIN_MENU_NAMES

    def test_user_menu_names_only_view_permissions(self):
        """测试 user 角色只有查看权限。"""
        # user 角色不应该有写权限
        write_permissions = ["add", "edit", "delete", "manage"]
        for perm in write_permissions:
            # 检查是否包含修改类权限
            matching = [name for name in rbac_defaults.USER_MENU_NAMES if perm in name.lower()]
            # 如果有匹配的，这些应该是目录类型而不是操作权限
            # 或者不应该存在
            for name in matching:
                menu = next((m for m in rbac_defaults.DEFAULT_MENUS if m["name"] == name), None)
                if menu:
                    # 目录和菜单类型可以有 view 权限包含 add/edit/delete（表示可见）
                    # 但 PERMISSION 类型的 user:add, user:edit 等不应该在 user 角色中
                    if menu["menu_type"] == 2:  # PERMISSION
                        assert perm not in ["add", "edit", "delete", "manage"], f"user 角色不应该有 {name} 权限"


@pytest.mark.unit
class TestRbacDefaultsConsistency:
    """测试 RBAC 默认数据一致性。"""

    def test_menu_parent_ids_reference_existing(self):
        """测试菜单的 parent_id 引用已存在的菜单名。"""
        menu_names = {m["name"] for m in rbac_defaults.DEFAULT_MENUS}
        for menu in rbac_defaults.DEFAULT_MENUS:
            if menu.get("parent_id"):
                assert menu["parent_id"] in menu_names, f"parent_id 引用不存在的菜单: {menu['parent_id']}"

    def test_permission_methods_valid(self):
        """测试权限菜单的 HTTP 方法有效。"""
        valid_methods = ["GET", "POST", "PUT", "DELETE"]
        for menu in rbac_defaults.DEFAULT_MENUS:
            if menu["menu_type"] == 2:  # PERMISSION
                assert menu.get("method") in valid_methods, f"无效的 HTTP 方法: {menu.get('method')}"
