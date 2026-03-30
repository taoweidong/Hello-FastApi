"""DTO 验证器的单元测试。"""

import pytest
from pydantic import ValidationError

from src.application.dto.user_dto import UserCreateDTO, UserUpdateDTO, UserListQueryDTO
from src.application.dto.rbac_dto import RoleCreateDTO, RoleUpdateDTO


@pytest.mark.unit
class TestUserCreateDTO:
    """UserCreateDTO 验证测试。"""

    def test_valid_user_create(self):
        """测试有效的用户创建数据。"""
        dto = UserCreateDTO(
            username="testuser",
            password="TestPass123",
            nickname="测试用户",
            email="test@example.com",
            status=1,
        )
        assert dto.username == "testuser"
        assert dto.nickname == "测试用户"

    def test_empty_str_converts_to_none(self):
        """测试空字符串转换为 None。"""
        dto = UserCreateDTO(
            username="testuser",
            password="TestPass123",
            nickname="",
            email="",
            phone="",
            remark="",
            status=1,
        )
        assert dto.nickname is None
        assert dto.email is None
        assert dto.phone is None
        assert dto.remark is None

    def test_zero_dept_id_converts_to_none(self):
        """测试 0 的 dept_id 转换为 None。"""
        dto = UserCreateDTO(
            username="testuser",
            password="TestPass123",
            deptId=0,
            status=1,
        )
        assert dto.dept_id is None

    def test_string_dept_id_converts_to_int(self):
        """测试字符串 dept_id 转换为整数。"""
        dto = UserCreateDTO(
            username="testuser",
            password="TestPass123",
            deptId="123",
            status=1,
        )
        assert dto.dept_id == 123

    def test_username_too_short(self):
        """测试用户名过短。"""
        with pytest.raises(ValidationError):
            UserCreateDTO(
                username="ab",
                password="TestPass123",
                status=1,
            )

    def test_password_too_short(self):
        """测试密码过短。"""
        with pytest.raises(ValidationError):
            UserCreateDTO(
                username="testuser",
                password="short",
                status=1,
            )


@pytest.mark.unit
class TestUserUpdateDTO:
    """UserUpdateDTO 验证测试。"""

    def test_valid_user_update(self):
        """测试有效的用户更新数据。"""
        dto = UserUpdateDTO(
            nickname="新昵称",
            email="new@example.com",
            status=1,
        )
        assert dto.nickname == "新昵称"
        assert dto.email == "new@example.com"

    def test_empty_str_converts_to_none(self):
        """测试空字符串转换为 None。"""
        dto = UserUpdateDTO(
            nickname="",
            email="",
            phone="",
        )
        assert dto.nickname is None
        assert dto.email is None
        assert dto.phone is None

    def test_partial_update(self):
        """测试部分更新。"""
        dto = UserUpdateDTO(nickname="仅更新昵称")
        assert dto.nickname == "仅更新昵称"
        assert dto.email is None
        assert dto.status is None


@pytest.mark.unit
class TestUserListQueryDTO:
    """UserListQueryDTO 验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        dto = UserListQueryDTO()
        assert dto.pageNum == 1
        assert dto.pageSize == 10

    def test_custom_values(self):
        """测试自定义值。"""
        dto = UserListQueryDTO(
            pageNum=2,
            pageSize=20,
            username="test",
            status=1,
        )
        assert dto.pageNum == 2
        assert dto.pageSize == 20
        assert dto.username == "test"
        assert dto.status == 1

    def test_empty_status_converts_to_none(self):
        """测试空状态转换为 None。"""
        dto = UserListQueryDTO(status="")
        assert dto.status is None


@pytest.mark.unit
class TestRoleCreateDTO:
    """RoleCreateDTO 验证测试。"""

    def test_valid_role_create(self):
        """测试有效的角色创建数据。"""
        dto = RoleCreateDTO(
            name="管理员",
            code="admin",
            remark="管理员角色",
            status=1,
        )
        assert dto.name == "管理员"
        assert dto.code == "admin"

    def test_empty_remark_converts_to_none(self):
        """测试空备注转换为 None。"""
        dto = RoleCreateDTO(
            name="管理员",
            code="admin",
            remark="",
        )
        assert dto.remark is None

    def test_default_permission_ids(self):
        """测试默认权限 ID 列表。"""
        dto = RoleCreateDTO(
            name="管理员",
            code="admin",
        )
        assert dto.permissionIds == []


@pytest.mark.unit
class TestRoleUpdateDTO:
    """RoleUpdateDTO 验证测试。"""

    def test_valid_role_update(self):
        """测试有效的角色更新数据。"""
        dto = RoleUpdateDTO(
            name="新名称",
            status=1,  # 使用 1 而不是 0，因为 0 会被转换为 None
        )
        assert dto.name == "新名称"
        assert dto.status == 1

    def test_status_zero_converts_to_none(self):
        """测试 status=0 转换为 None（表示不更新状态）。"""
        dto = RoleUpdateDTO(status=0)
        assert dto.status is None

    def test_empty_status_converts_to_none(self):
        """测试空状态转换为 None。"""
        dto = RoleUpdateDTO(status="")
        assert dto.status is None

    def test_default_status_is_none(self):
        """测试默认 status 为 None。"""
        dto = RoleUpdateDTO()
        assert dto.status is None
