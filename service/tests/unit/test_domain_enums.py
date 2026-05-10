"""领域枚举的单元测试。

测试 src.domain.enums 中的所有枚举类型。
"""

import pytest

from src.domain.enums import Gender, LoginStatus, MenuType, PermissionMode, UserStatus, UserRole


@pytest.mark.unit
class TestUserStatus:
    """UserStatus 测试类。"""

    def test_inactive_value(self):
        """测试 INACTIVE 枚举值。"""
        assert UserStatus.INACTIVE == 0

    def test_active_value(self):
        """测试 ACTIVE 枚举值。"""
        assert UserStatus.ACTIVE == 1

    def test_to_int_inactive(self):
        """测试 to_int 方法（INACTIVE）。"""
        assert UserStatus.INACTIVE == int(0)

    def test_to_int_active(self):
        """测试 to_int 方法（ACTIVE）。"""
        assert UserStatus.ACTIVE == int(1)

    def test_from_int_inactive(self):
        """测试 from_int 方法（0 -> INACTIVE）。"""
        result = UserStatus(0)
        assert result == UserStatus.INACTIVE

    def test_from_int_active(self):
        """测试 from_int 方法（1 -> ACTIVE）。"""
        result = UserStatus(1)
        assert result == UserStatus.ACTIVE


@pytest.mark.unit
class TestUserRole:
    """UserRole 测试类。"""

    def test_user_value(self):
        """测试 USER 枚举值。"""
        assert UserRole.USER == 0

    def test_staff_value(self):
        """测试 STAFF 枚举值。"""
        assert UserRole.STAFF == 1

    def test_superuser_value(self):
        """测试 SUPERUSER 枚举值。"""
        assert UserRole.SUPERUSER == 1


@pytest.mark.unit
class TestMenuType:
    """MenuType 测试类。"""

    def test_directory_value(self):
        """测试 DIRECTORY 枚举值。"""
        assert MenuType.DIRECTORY == 0

    def test_menu_value(self):
        """测试 MENU 枚举值。"""
        assert MenuType.MENU == 1

    def test_permission_value(self):
        """测试 PERMISSION 枚举值。"""
        assert MenuType.PERMISSION == 2


@pytest.mark.unit
class TestLoginStatus:
    """LoginStatus 测试类。"""

    def test_failed_value(self):
        """测试 FAILED 枚举值。"""
        assert LoginStatus.FAILED == 0

    def test_success_value(self):
        """测试 SUCCESS 枚举值。"""
        assert LoginStatus.SUCCESS == 1


@pytest.mark.unit
class TestGender:
    """Gender 测试类。"""

    def test_unknown_value(self):
        """测试 UNKNOWN 枚举值。"""
        assert Gender.UNKNOWN == 0

    def test_male_value(self):
        """测试 MALE 枚举值。"""
        assert Gender.MALE == 1

    def test_female_value(self):
        """测试 FEMALE 枚举值。"""
        assert Gender.FEMALE == 2


@pytest.mark.unit
class TestPermissionMode:
    """PermissionMode 测试类。"""

    def test_or_value(self):
        """测试 OR 枚举值。"""
        assert PermissionMode.OR == 0

    def test_and_value(self):
        """测试 AND 枚举值。"""
        assert PermissionMode.AND == 1
