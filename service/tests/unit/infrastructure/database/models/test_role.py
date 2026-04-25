"""Role 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.role import Role


@pytest.mark.unit
class TestRoleModel:
    """Role ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_roles。"""
        assert Role.__tablename__ == "sys_roles"

    def test_is_sqlmodel_table(self):
        """Role 应继承 SQLModel 并映射为表。"""
        assert issubclass(Role, SQLModel)
        assert hasattr(Role, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        role = Role(name="管理员", code="admin")
        assert role.id is not None
        assert len(role.id) == 32

    def test_field_defaults(self):
        """测试字段默认值。"""
        role = Role(name="管理员", code="admin")
        assert role.is_active == 1

    def test_optional_fields_default_none(self):
        """可选字段默认应为 None。"""
        role = Role(name="管理员", code="admin")
        assert role.creator_id is None
        assert role.modifier_id is None
        assert role.created_time is None
        assert role.updated_time is None
        assert role.description is None

    def test_field_max_length(self):
        """字段应有正确的 max_length 限制。"""
        assert Role.name.type.length == 128
        assert Role.code.type.length == 128
        assert Role.creator_id.type.length == 150
        assert Role.modifier_id.type.length == 150
        assert Role.description.type.length == 256

    def test_name_is_unique_and_indexed(self):
        """name 字段应标记为 unique 和 index。"""
        assert Role.name.unique is True
        assert Role.name.index is True

    def test_code_is_unique(self):
        """code 字段应标记为 unique。"""
        assert Role.code.unique is True

    def test_to_domain(self):
        """to_domain 应返回 RoleEntity 实例。"""
        from src.domain.entities.role import RoleEntity

        role = Role(id="role-1", name="管理员", code="admin", is_active=1, description="系统管理员")
        entity = role.to_domain()
        assert isinstance(entity, RoleEntity)
        assert entity.id == "role-1"
        assert entity.name == "管理员"
        assert entity.code == "admin"
        assert entity.is_active == 1
        assert entity.description == "系统管理员"

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.role import RoleEntity

        entity = RoleEntity(id="role-2", name="普通用户", code="user", is_active=0, description="普通用户角色")
        role = Role.from_domain(entity)
        assert isinstance(role, Role)
        assert role.id == "role-2"
        assert role.name == "普通用户"
        assert role.code == "user"
        assert role.is_active == 0
        assert role.description == "普通用户角色"

    def test_repr(self):
        """__repr__ 应包含 id 和 name。"""
        role = Role(name="测试角色", code="test")
        role.id = "role-123"
        r = repr(role)
        assert "Role" in r
        assert "role-123" in r
        assert "测试角色" in r
