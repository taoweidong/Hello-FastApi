"""用户 DTO 的单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.application.dto.user_dto import (
    AssignRoleDTO,
    BatchDeleteDTO,
    ChangePasswordDTO,
    ResetPasswordDTO,
    UpdateStatusDTO,
    UserCreateDTO,
    UserListQueryDTO,
    UserResponseDTO,
    UserUpdateDTO,
)


@pytest.mark.unit
class TestUserCreateDTO:
    """UserCreateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的用户创建数据。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", isActive=True)
        assert dto.username == "testuser"
        assert dto.isActive == 1
        assert dto.isStaff == 0
        assert dto.modeType == 0
        assert dto.nickname is None
        assert dto.dept_id is None

    def test_valid_input_all_fields(self):
        """测试所有字段。"""
        dto = UserCreateDTO(
            username="testuser",
            password="TestPass123",
            nickname="昵称",
            firstName="张",
            lastName="三",
            email="user@example.com",
            phone="13800138000",
            gender=1,
            avatar="https://example.com/avatar.png",
            isActive=1,
            isStaff=1,
            modeType=1,
            deptId="dept-001",
            description="备注",
        )
        assert dto.nickname == "昵称"
        assert dto.gender == 1
        assert dto.isStaff == 1
        assert dto.dept_id == "dept-001"

    def test_empty_str_converts_to_none(self):
        """测试空字符串转换为 None。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", nickname="", email="", phone="", avatar="", description="", isActive=True)
        assert dto.nickname is None
        assert dto.email is None
        assert dto.phone is None
        assert dto.avatar is None
        assert dto.description is None

    def test_zero_dept_id_converts_to_none(self):
        """测试 0 的 deptId 转换为 None。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", deptId=0, isActive=True)
        assert dto.dept_id is None

    def test_empty_dept_id_converts_to_none(self):
        """测试空字符串 deptId 转换为 None。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", deptId="", isActive=True)
        assert dto.dept_id is None

    def test_string_dept_id_remains(self):
        """测试字符串 deptId 保留。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", deptId="dept-001", isActive=True)
        assert dto.dept_id == "dept-001"

    def test_gender_zero_converts_to_none(self):
        """测试 gender 为 0 转换为 None。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", gender=0, isActive=True)
        assert dto.gender is None

    def test_empty_gender_converts_to_none(self):
        """测试空字符串 gender 转换为 None。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", gender="", isActive=True)
        assert dto.gender is None

    def test_is_staff_zero_converts_to_none(self):
        """测试 isStaff 为 0 转换为 None 后因 int 类型校验失败。"""
        with pytest.raises(ValidationError):
            UserCreateDTO(username="testuser", password="TestPass123", isStaff=0, isActive=True)

    def test_is_staff_gender_one_preserved(self):
        """测试 isStaff 为 1 时保留。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", isStaff=1, isActive=True)
        assert dto.isStaff == 1

    def test_mode_type_zero_converts_to_none(self):
        """测试 modeType 为 0 转换为 None 后因 int 类型校验失败。"""
        with pytest.raises(ValidationError):
            UserCreateDTO(username="testuser", password="TestPass123", modeType=0, isActive=True)

    def test_mode_type_one_preserved(self):
        """测试 modeType 为 1 时保留。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", modeType=1, isActive=True)
        assert dto.modeType == 1

    def test_is_active_zero_preserved(self):
        """测试 isActive 为 0 时保留。"""
        dto = UserCreateDTO(username="testuser", password="TestPass123", isActive=0)
        assert dto.isActive == 0

    def test_is_active_empty_converts_to_none(self):
        """测试空字符串 isActive 转换为 None 后因 int 类型校验失败。"""
        with pytest.raises(ValidationError):
            UserCreateDTO(username="testuser", password="TestPass123", isActive="")

    def test_username_too_short(self):
        """测试用户名过短。"""
        with pytest.raises(ValidationError):
            UserCreateDTO(username="ab", password="TestPass123", isActive=True)

    def test_password_too_short(self):
        """测试密码过短。"""
        with pytest.raises(ValidationError):
            UserCreateDTO(username="testuser", password="short", isActive=True)

    def test_missing_username(self):
        """测试缺少用户名。"""
        with pytest.raises(ValidationError):
            UserCreateDTO(password="TestPass123", isActive=True)


@pytest.mark.unit
class TestUserUpdateDTO:
    """UserUpdateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的用户更新数据。"""
        dto = UserUpdateDTO(nickname="新昵称", email="new@example.com")
        assert dto.nickname == "新昵称"
        assert dto.email == "new@example.com"

    def test_empty_input(self):
        """测试空更新。"""
        dto = UserUpdateDTO()
        assert dto.nickname is None
        assert dto.isActive is None
        assert dto.isStaff is None

    def test_empty_str_converts_to_none(self):
        """测试空字符串转换为 None。"""
        dto = UserUpdateDTO(nickname="", email="", phone="", avatar="", description="")
        assert dto.nickname is None
        assert dto.email is None
        assert dto.phone is None
        assert dto.avatar is None
        assert dto.description is None

    def test_gender_zero_converts_to_none(self):
        """测试 gender 为 0 转换为 None。"""
        dto = UserUpdateDTO(gender=0)
        assert dto.gender is None

    def test_is_staff_zero_converts_to_none(self):
        """测试 isStaff 为 0 转换为 None。"""
        dto = UserUpdateDTO(isStaff=0)
        assert dto.isStaff is None

    def test_mode_type_zero_converts_to_none(self):
        """测试 modeType 为 0 转换为 None。"""
        dto = UserUpdateDTO(modeType=0)
        assert dto.modeType is None

    def test_is_active_zero_preserved(self):
        """测试 isActive 为 0 时保留。"""
        dto = UserUpdateDTO(isActive=0)
        assert dto.isActive == 0

    def test_is_active_empty_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = UserUpdateDTO(isActive="")
        assert dto.isActive is None

    def test_dept_id_zero_converts_to_none(self):
        """测试 deptId 为 0 转换为 None。"""
        dto = UserUpdateDTO(deptId=0)
        assert dto.dept_id is None

    def test_dept_id_empty_converts_to_none(self):
        """测试空字符串 deptId 转换为 None。"""
        dto = UserUpdateDTO(deptId="")
        assert dto.dept_id is None

    def test_partial_update(self):
        """测试部分更新。"""
        dto = UserUpdateDTO(nickname="仅更新昵称")
        assert dto.nickname == "仅更新昵称"
        assert dto.email is None
        assert dto.isActive is None


@pytest.mark.unit
class TestUserResponseDTO:
    """UserResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的用户响应数据。"""
        dto = UserResponseDTO(id="1", username="testuser")
        assert dto.id == "1"
        assert dto.username == "testuser"
        assert dto.isActive == 1
        assert dto.isStaff == 0
        assert dto.modeType == 0
        assert dto.roles == []
        assert dto.nickname is None

    def test_with_all_fields(self):
        """测试所有字段。"""
        now = datetime.now()
        dto = UserResponseDTO(
            id="1",
            username="testuser",
            nickname="昵称",
            firstName="张",
            lastName="三",
            avatar="avatar.png",
            email="user@example.com",
            phone="13800138000",
            gender=1,
            isActive=1,
            isStaff=1,
            modeType=1,
            roles=[{"id": "r1", "name": "管理员"}],
            creatorId="u1",
            modifierId="u2",
            createdTime=now,
            updatedTime=now,
            description="备注",
        )
        assert dto.nickname == "昵称"
        assert dto.roles == [{"id": "r1", "name": "管理员"}]
        assert dto.createdTime == now

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            UserResponseDTO(username="testuser")

    def test_missing_username(self):
        """测试缺少用户名。"""
        with pytest.raises(ValidationError):
            UserResponseDTO(id="1")


@pytest.mark.unit
class TestUserListQueryDTO:
    """UserListQueryDTO 验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        dto = UserListQueryDTO()
        assert dto.pageNum == 1
        assert dto.pageSize == 10
        assert dto.username is None
        assert dto.phone is None
        assert dto.email is None
        assert dto.isActive is None
        assert dto.deptId is None

    def test_custom_values(self):
        """测试自定义值。"""
        dto = UserListQueryDTO(pageNum=2, pageSize=20, username="test", phone="138", email="test@", isActive=1, deptId="dept-001")
        assert dto.pageNum == 2
        assert dto.username == "test"
        assert dto.isActive == 1
        assert dto.deptId == "dept-001"

    def test_page_size_out_of_range(self):
        """测试 pageSize 超出范围。"""
        with pytest.raises(ValidationError):
            UserListQueryDTO(pageSize=101)

    def test_empty_is_active_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = UserListQueryDTO(isActive="")
        assert dto.isActive is None

    def test_dept_id_zero_converts_to_none(self):
        """测试 deptId 为 0 转换为 None。"""
        dto = UserListQueryDTO(deptId=0)
        assert dto.deptId is None

    def test_dept_id_empty_converts_to_none(self):
        """测试空字符串 deptId 转换为 None。"""
        dto = UserListQueryDTO(deptId="")
        assert dto.deptId is None

    def test_dept_id_string_remains(self):
        """测试字符串 deptId 保留。"""
        dto = UserListQueryDTO(deptId="dept-001")
        assert dto.deptId == "dept-001"


@pytest.mark.unit
class TestChangePasswordDTO:
    """ChangePasswordDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的修改密码数据。"""
        dto = ChangePasswordDTO(oldPassword="OldPass123", newPassword="NewPass456")
        assert dto.oldPassword == "OldPass123"
        assert dto.newPassword == "NewPass456"

    def test_new_password_too_short(self):
        """测试新密码过短。"""
        with pytest.raises(ValidationError):
            ChangePasswordDTO(oldPassword="OldPass123", newPassword="short")

    def test_missing_old_password(self):
        """测试缺少旧密码。"""
        with pytest.raises(ValidationError):
            ChangePasswordDTO(newPassword="NewPass456")


@pytest.mark.unit
class TestResetPasswordDTO:
    """ResetPasswordDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的重置密码数据。"""
        dto = ResetPasswordDTO(newPassword="NewPass456")
        assert dto.newPassword == "NewPass456"

    def test_new_password_too_short(self):
        """测试新密码过短。"""
        with pytest.raises(ValidationError):
            ResetPasswordDTO(newPassword="short")

    def test_new_password_too_long(self):
        """测试新密码过长。"""
        with pytest.raises(ValidationError):
            ResetPasswordDTO(newPassword="a" * 129)


@pytest.mark.unit
class TestUpdateStatusDTO:
    """UpdateStatusDTO 验证测试。"""

    def test_valid_active(self):
        """测试有效的启用状态。"""
        dto = UpdateStatusDTO(isActive=1)
        assert dto.isActive == 1

    def test_valid_inactive(self):
        """测试有效的禁用状态。"""
        dto = UpdateStatusDTO(isActive=0)
        assert dto.isActive == 0

    def test_is_active_out_of_range(self):
        """测试 isActive 超出范围。"""
        with pytest.raises(ValidationError):
            UpdateStatusDTO(isActive=2)

    def test_is_active_negative(self):
        """测试 isActive 为负数。"""
        with pytest.raises(ValidationError):
            UpdateStatusDTO(isActive=-1)

    def test_missing_is_active(self):
        """测试缺少 isActive。"""
        with pytest.raises(ValidationError):
            UpdateStatusDTO()


@pytest.mark.unit
class TestBatchDeleteDTO:
    """BatchDeleteDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的批量删除数据。"""
        dto = BatchDeleteDTO(ids=["1", "2", "3"])
        assert dto.ids == ["1", "2", "3"]

    def test_empty_ids(self):
        """测试空 ID 列表。"""
        dto = BatchDeleteDTO(ids=[])
        assert dto.ids == []

    def test_missing_ids(self):
        """测试缺少 ID 列表。"""
        with pytest.raises(ValidationError):
            BatchDeleteDTO()


@pytest.mark.unit
class TestUserAssignRoleDTO:
    """AssignRoleDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的分配角色数据。"""
        dto = AssignRoleDTO(userId="u1", roleIds=["r1", "r2"])
        assert dto.userId == "u1"
        assert dto.roleIds == ["r1", "r2"]

    def test_empty_role_ids(self):
        """测试空角色 ID 列表。"""
        dto = AssignRoleDTO(userId="u1", roleIds=[])
        assert dto.roleIds == []

    def test_missing_user_id(self):
        """测试缺少用户 ID。"""
        with pytest.raises(ValidationError):
            AssignRoleDTO(roleIds=["r1"])

    def test_missing_role_ids(self):
        """测试缺少角色 ID。"""
        with pytest.raises(ValidationError):
            AssignRoleDTO(userId="u1")
