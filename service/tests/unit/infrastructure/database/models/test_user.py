"""User 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.user import User


@pytest.mark.unit
class TestUserModel:
    """User ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_users。"""
        assert User.__tablename__ == "sys_users"

    def test_is_sqlmodel_table(self):
        """User 应继承 SQLModel 并映射为表。"""
        assert issubclass(User, SQLModel)
        assert hasattr(User, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        user = User(username="testuser", password="hash123")
        assert user.id is not None
        assert len(user.id) == 32

    def test_field_defaults(self):
        """测试字段默认值。"""
        user = User(username="testuser", password="hash123")
        assert user.is_superuser == 0
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.is_staff == 0
        assert user.is_active == 1
        assert user.mode_type == 0
        assert user.nickname == ""
        assert user.gender == 0
        assert user.phone == ""
        assert user.email == ""

    def test_optional_fields_default_none(self):
        """可选字段默认应为 None。"""
        user = User(username="testuser", password="hash123")
        assert user.last_login is None
        assert user.date_joined is None
        assert user.avatar is None
        assert user.creator_id is None
        assert user.modifier_id is None
        assert user.dept_id is None
        assert user.created_time is None
        assert user.updated_time is None
        assert user.description is None

    def test_field_max_length(self):
        """字段应有正确的 max_length 限制。"""
        assert User.password.type.length == 128
        assert User.username.type.length == 150
        assert User.first_name.type.length == 150
        assert User.last_name.type.length == 150
        assert User.avatar.type.length == 100
        assert User.nickname.type.length == 150
        assert User.phone.type.length == 16
        assert User.email.type.length == 254
        assert User.creator_id.type.length == 150
        assert User.modifier_id.type.length == 150
        assert User.description.type.length == 256

    def test_username_is_unique_and_indexed(self):
        """username 字段应标记为 unique 和 index。"""
        assert User.username.unique is True
        assert User.username.index is True

    def test_to_domain(self):
        """to_domain 应返回 UserEntity 实例。"""
        from src.domain.entities.user import UserEntity

        user = User(
            id="user-1",
            username="admin",
            password="hash",
            is_superuser=1,
            is_active=1,
            nickname="管理员",
            gender=1,
            phone="13800138000",
            email="admin@example.com",
        )
        entity = user.to_domain()
        assert isinstance(entity, UserEntity)
        assert entity.id == "user-1"
        assert entity.username == "admin"
        assert entity.is_superuser == 1
        assert entity.nickname == "管理员"
        assert entity.email == "admin@example.com"

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.user import UserEntity

        entity = UserEntity(
            id="user-2",
            username="test",
            password="hash456",
            is_superuser=0,
            is_active=1,
            nickname="测试用户",
            gender=0,
            phone="13900139000",
            email="test@example.com",
        )
        user = User.from_domain(entity)
        assert isinstance(user, User)
        assert user.id == "user-2"
        assert user.username == "test"
        assert user.is_superuser == 0
        assert user.nickname == "测试用户"
        assert user.email == "test@example.com"

    def test_repr(self):
        """__repr__ 应包含 id 和 username。"""
        user = User(username="hello", password="pwd")
        user.id = "user-123"
        r = repr(user)
        assert "User" in r
        assert "user-123" in r
        assert "hello" in r
