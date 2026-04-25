"""用户领域实体的单元测试。

测试 UserEntity 的所有状态查询属性、状态变更方法和工厂方法。
"""

import pytest

from src.domain.entities.user import UserEntity


@pytest.mark.unit
class TestUserEntity:
    """UserEntity 测试类。"""

    # ---- 状态查询属性测试 ----

    def test_is_superuser_user_when_superuser(self):
        """测试 is_superuser_user 属性（是超级管理员）。"""
        user = UserEntity(id="user-1", username="admin", password="hash", is_superuser=1)
        assert user.is_superuser_user is True

    def test_is_superuser_user_when_not_superuser(self):
        """测试 is_superuser_user 属性（非超级管理员）。"""
        user = UserEntity(id="user-1", username="user", password="hash", is_superuser=0)
        assert user.is_superuser_user is False

    def test_is_active_user_when_active(self):
        """测试 is_active_user 属性（已启用）。"""
        user = UserEntity(id="user-1", username="user", password="hash", is_active=1)
        assert user.is_active_user is True

    def test_is_active_user_when_inactive(self):
        """测试 is_active_user 属性（未启用）。"""
        user = UserEntity(id="user-1", username="user", password="hash", is_active=0)
        assert user.is_active_user is False

    # ---- 状态变更方法测试 ----

    def test_activate(self):
        """测试 activate 方法。"""
        user = UserEntity(id="user-1", username="user", password="hash", is_active=0)
        user.activate()
        assert user.is_active == 1
        assert user.is_active_user is True

    def test_deactivate(self):
        """测试 deactivate 方法。"""
        user = UserEntity(id="user-1", username="user", password="hash", is_active=1)
        user.deactivate()
        assert user.is_active == 0
        assert user.is_active_user is False

    def test_change_password(self):
        """测试 change_password 方法。"""
        user = UserEntity(id="user-1", username="user", password="old_hash")
        user.change_password("new_hash")
        assert user.password == "new_hash"

    def test_update_profile_with_all_fields(self):
        """测试 update_profile 方法（更新所有字段）。"""
        user = UserEntity(id="user-1", username="user", password="hash")
        user.update_profile(
            email="test@example.com",
            nickname="测试",
            first_name="名",
            last_name="姓",
            phone="13800138000",
            gender=1,
            avatar="avatar.png",
            is_active=1,
            is_staff=1,
            mode_type=1,
            dept_id="dept-1",
            description="描述",
        )
        assert user.email == "test@example.com"
        assert user.nickname == "测试"
        assert user.first_name == "名"
        assert user.last_name == "姓"
        assert user.phone == "13800138000"
        assert user.gender == 1
        assert user.avatar == "avatar.png"
        assert user.is_active == 1
        assert user.is_staff == 1
        assert user.mode_type == 1
        assert user.dept_id == "dept-1"
        assert user.description == "描述"

    def test_update_profile_with_partial_fields(self):
        """测试 update_profile 方法（部分字段）。"""
        user = UserEntity(id="user-1", username="user", password="hash")
        user.update_profile(email="test@example.com", nickname="测试")
        assert user.email == "test@example.com"
        assert user.nickname == "测试"
        # 其他字段保持不变
        assert user.username == "user"
        assert user.gender == 0

    def test_update_profile_ignore_none_fields(self):
        """测试 update_profile 方法（忽略 None 字段）。"""
        user = UserEntity(id="user-1", username="user", password="hash", nickname="原始昵称")
        user.update_profile(email=None, nickname=None)
        assert user.nickname == "原始昵称"

    # ---- 工厂方法测试 ----

    def test_create_new(self):
        """测试 create_new 工厂方法。"""
        user = UserEntity.create_new(
            username="newuser",
            hashed_password="hashed",
            email="new@example.com",
            nickname="新用户",
            first_name="名",
            last_name="姓",
            phone="13800138000",
            gender=1,
            avatar="avatar.png",
            is_active=1,
            is_staff=0,
            mode_type=0,
            dept_id="dept-1",
            description="描述",
        )
        assert user.id is not None
        assert len(user.id) == 32  # UUID hex 32位
        assert user.username == "newuser"
        assert user.password == "hashed"
        assert user.email == "new@example.com"
        assert user.nickname == "新用户"
        assert user.first_name == "名"
        assert user.last_name == "姓"
        assert user.phone == "13800138000"
        assert user.gender == 1
        assert user.avatar == "avatar.png"
        assert user.is_active == 1
        assert user.is_staff == 0
        assert user.mode_type == 0
        assert user.dept_id == "dept-1"
        assert user.description == "描述"

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        user = UserEntity.create_new(username="user", hashed_password="hash")
        assert user.username == "user"
        assert user.password == "hash"
        assert user.is_active == 1
        assert user.is_staff == 0
        assert user.nickname == ""

    def test_create_superuser_entity(self):
        """测试 create_superuser_entity 工厂方法。"""
        user = UserEntity.create_superuser_entity(
            username="admin",
            hashed_password="hashed",
            email="admin@example.com",
            nickname="管理员",
            mode_type=0,
        )
        assert user.id is not None
        assert user.username == "admin"
        assert user.password == "hashed"
        assert user.email == "admin@example.com"
        assert user.nickname == "管理员"
        assert user.is_active == 1
        assert user.is_staff == 1
        assert user.is_superuser == 1

    def test_create_superuser_entity_with_defaults(self):
        """测试 create_superuser_entity 工厂方法（使用默认值）。"""
        user = UserEntity.create_superuser_entity(username="admin", hashed_password="hash")
        assert user.is_active == 1
        assert user.is_staff == 1
        assert user.is_superuser == 1
