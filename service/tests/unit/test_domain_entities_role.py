"""角色领域实体的单元测试。

测试 RoleEntity 的所有状态查询属性、状态变更方法和工厂方法。
"""

import pytest

from src.domain.entities.role import RoleEntity


@pytest.mark.unit
class TestRoleEntity:
    """RoleEntity 测试类。"""

    # ---- 状态查询属性测试 ----

    def test_is_active_role_when_active(self):
        """测试 is_active_role 属性（已启用）。"""
        role = RoleEntity(id="role-1", name="Admin", code="admin", is_active=1)
        assert role.is_active_role is True

    def test_is_active_role_when_inactive(self):
        """测试 is_active_role 属性（未启用）。"""
        role = RoleEntity(id="role-1", name="Admin", code="admin", is_active=0)
        assert role.is_active_role is False

    # ---- 状态变更方法测试 ----

    def test_activate(self):
        """测试 activate 方法。"""
        role = RoleEntity(id="role-1", name="Admin", code="admin", is_active=0)
        role.activate()
        assert role.is_active == 1
        assert role.is_active_role is True

    def test_deactivate(self):
        """测试 deactivate 方法。"""
        role = RoleEntity(id="role-1", name="Admin", code="admin", is_active=1)
        role.deactivate()
        assert role.is_active == 0
        assert role.is_active_role is False

    def test_update_info_with_all_fields(self):
        """测试 update_info 方法（更新所有字段）。"""
        role = RoleEntity(id="role-1", name="Admin", code="admin")
        role.update_info(name="超级管理员", code="superadmin", description="描述", is_active=1)
        assert role.name == "超级管理员"
        assert role.code == "superadmin"
        assert role.description == "描述"
        assert role.is_active == 1

    def test_update_info_with_partial_fields(self):
        """测试 update_info 方法（部分字段）。"""
        role = RoleEntity(id="role-1", name="Admin", code="admin")
        role.update_info(name="新名称")
        assert role.name == "新名称"
        assert role.code == "admin"  # 未更新

    def test_update_info_ignore_none_fields(self):
        """测试 update_info 方法（忽略 None 字段）。"""
        role = RoleEntity(id="role-1", name="Admin", code="admin")
        role.update_info(name=None, description=None)
        assert role.name == "Admin"

    # ---- 工厂方法测试 ----

    def test_create_new(self):
        """测试 create_new 工厂方法。"""
        role = RoleEntity.create_new(name="Admin", code="admin", description="管理员角色")
        assert role.id is not None
        assert len(role.id) == 32
        assert role.name == "Admin"
        assert role.code == "admin"
        assert role.description == "管理员角色"
        assert role.is_active == 1

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        role = RoleEntity.create_new(name="User", code="user")
        assert role.name == "User"
        assert role.code == "user"
        assert role.is_active == 1
        assert role.description is None
