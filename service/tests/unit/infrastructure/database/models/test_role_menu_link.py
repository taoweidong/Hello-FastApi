"""RoleMenuLink 模型单元测试。

测试表结构、字段类型、外键约束及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.role_menu_link import RoleMenuLink


@pytest.mark.unit
class TestRoleMenuLinkModel:
    """RoleMenuLink ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_userrole_menu。"""
        assert RoleMenuLink.__tablename__ == "sys_userrole_menu"

    def test_is_sqlmodel_table(self):
        """RoleMenuLink 应继承 SQLModel 并映射为表。"""
        assert issubclass(RoleMenuLink, SQLModel)
        assert hasattr(RoleMenuLink, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        link = RoleMenuLink(userrole_id="role-1", menu_id="menu-1")
        assert link.id is not None
        assert len(link.id) == 32

    def test_required_fields(self):
        """userrole_id 和 menu_id 应为必填字段。"""
        link = RoleMenuLink(userrole_id="role-1", menu_id="menu-1")
        assert link.userrole_id == "role-1"
        assert link.menu_id == "menu-1"

    def test_userrole_id_foreign_key(self):
        """userrole_id 应外键引用 sys_roles.id。"""
        col = RoleMenuLink.userrole_id
        assert col is not None

    def test_menu_id_foreign_key(self):
        """menu_id 应外键引用 sys_menus.id。"""
        col = RoleMenuLink.menu_id
        assert col is not None

    def test_repr(self):
        """__repr__ 应包含 userrole_id 和 menu_id。"""
        link = RoleMenuLink(userrole_id="role-123", menu_id="menu-456")
        r = repr(link)
        assert "RoleMenuLink" in r
        assert "role-123" in r
        assert "menu-456" in r
