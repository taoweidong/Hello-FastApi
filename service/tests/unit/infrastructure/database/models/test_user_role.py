"""UserRole 模型单元测试。

测试表结构、字段类型、外键约束、关系及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.user_role import UserRole


@pytest.mark.unit
class TestUserRoleModel:
    """UserRole ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_userinfo_roles。"""
        assert UserRole.__tablename__ == "sys_userinfo_roles"

    def test_is_sqlmodel_table(self):
        """UserRole 应继承 SQLModel 并映射为表。"""
        assert issubclass(UserRole, SQLModel)
        assert hasattr(UserRole, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        ur = UserRole(userinfo_id="user-1", userrole_id="role-1")
        assert ur.id is not None
        assert len(ur.id) == 32

    def test_required_fields(self):
        """userinfo_id 和 userrole_id 应为必填字段。"""
        ur = UserRole(userinfo_id="user-1", userrole_id="role-1")
        assert ur.userinfo_id == "user-1"
        assert ur.userrole_id == "role-1"

    def test_relationships_exist(self):
        """UserRole 应定义 user 和 role 关系属性。"""
        ur = UserRole(userinfo_id="user-1", userrole_id="role-1")
        assert ur.user is None
        assert ur.role is None

    def test_repr(self):
        """__repr__ 应包含 userinfo_id 和 userrole_id。"""
        ur = UserRole(userinfo_id="user-123", userrole_id="role-456")
        r = repr(ur)
        assert "UserRole" in r
        assert "user-123" in r
        assert "role-456" in r
