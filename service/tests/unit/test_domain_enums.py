"""领域枚举的单元测试。

测试 src.domain.enums 中的所有枚举类型。
"""

import pytest

from src.domain.enums import (
    LoginStatusEnum,
    MenuTypeEnum,
    StatusEnum,
)


@pytest.mark.unit
class TestStatusEnum:
    """StatusEnum 测试类。"""

    def test_inactive_value(self):
        """测试 INACTIVE 枚举值。"""
        assert StatusEnum.INACTIVE == 0

    def test_active_value(self):
        """测试 ACTIVE 枚举值。"""
        assert StatusEnum.ACTIVE == 1

    def test_to_int_inactive(self):
        """测试 to_int 方法（INACTIVE）。"""
        assert StatusEnum.INACTIVE.to_int() == 0

    def test_to_int_active(self):
        """测试 to_int 方法（ACTIVE）。"""
        assert StatusEnum.ACTIVE.to_int() == 1

    def test_from_int_inactive(self):
        """测试 from_int 方法（0 -> INACTIVE）。"""
        result = StatusEnum.from_int(0)
        assert result == StatusEnum.INACTIVE

    def test_from_int_active(self):
        """测试 from_int 方法（1 -> ACTIVE）。"""
        result = StatusEnum.from_int(1)
        assert result == StatusEnum.ACTIVE

    def test_from_int_default(self):
        """测试 from_int 方法（默认 -> ACTIVE）。"""
        result = StatusEnum.from_int(99)
        assert result == StatusEnum.ACTIVE


@pytest.mark.unit
class TestMenuTypeEnum:
    """MenuTypeEnum 测试类。"""

    def test_directory_value(self):
        """测试 DIRECTORY 枚举值。"""
        assert MenuTypeEnum.DIRECTORY == 0

    def test_menu_value(self):
        """测试 MENU 枚举值。"""
        assert MenuTypeEnum.MENU == 1

    def test_permission_value(self):
        """测试 PERMISSION 枚举值。"""
        assert MenuTypeEnum.PERMISSION == 2


@pytest.mark.unit
class TestLoginStatusEnum:
    """LoginStatusEnum 测试类。"""

    def test_failed_value(self):
        """测试 FAILED 枚举值。"""
        assert LoginStatusEnum.FAILED == 0

    def test_success_value(self):
        """测试 SUCCESS 枚举值。"""
        assert LoginStatusEnum.SUCCESS == 1
