"""应用层验证器的单元测试。"""

import pytest

from src.application.validators import (
    empty_str_or_zero_to_none,
    empty_str_to_none,
    normalize_optional_id,
    parse_status,
    parse_time_range,
    validate_password_strength,
    validate_username,
)
from src.domain.exceptions import ValidationError


@pytest.mark.unit
class TestValidateUsername:
    """validate_username 测试。"""

    def test_valid_username(self):
        """测试合法用户名。"""
        assert validate_username("abc") == "abc"
        assert validate_username("test_user_123") == "test_user_123"
        assert validate_username("A" * 50) == "A" * 50

    def test_too_short(self):
        """测试用户名太短。"""
        with pytest.raises(ValidationError) as exc_info:
            validate_username("ab")
        assert "3-50" in str(exc_info.value)

    def test_too_long(self):
        """测试用户名太长。"""
        with pytest.raises(ValidationError):
            validate_username("a" * 51)

    def test_special_characters(self):
        """测试包含特殊字符。"""
        with pytest.raises(ValidationError):
            validate_username("test-user")
        with pytest.raises(ValidationError):
            validate_username("test@user")
        with pytest.raises(ValidationError):
            validate_username("用户名")

    def test_empty_string(self):
        """测试空字符串。"""
        with pytest.raises(ValidationError):
            validate_username("")


@pytest.mark.unit
class TestValidatePasswordStrength:
    """validate_password_strength 测试。"""

    def test_strong_password(self):
        """测试强密码。"""
        assert validate_password_strength("TestPass123") == "TestPass123"

    def test_too_short(self):
        """测试密码太短。"""
        with pytest.raises(ValidationError) as exc_info:
            validate_password_strength("Ab1")
        assert "8" in str(exc_info.value)

    def test_no_uppercase(self):
        """测试缺少大写字母。"""
        with pytest.raises(ValidationError) as exc_info:
            validate_password_strength("testpass123")
        assert "大写" in str(exc_info.value)

    def test_no_lowercase(self):
        """测试缺少小写字母。"""
        with pytest.raises(ValidationError) as exc_info:
            validate_password_strength("TESTPASS123")
        assert "小写" in str(exc_info.value)

    def test_no_digit(self):
        """测试缺少数字。"""
        with pytest.raises(ValidationError) as exc_info:
            validate_password_strength("TestPassword")
        assert "数字" in str(exc_info.value)


@pytest.mark.unit
class TestEmptyStrToNone:
    """empty_str_to_none 测试。"""

    def test_empty_string(self):
        assert empty_str_to_none("") is None

    def test_non_empty_string(self):
        assert empty_str_to_none("hello") == "hello"

    def test_none_value(self):
        assert empty_str_to_none(None) is None

    def test_integer_value(self):
        assert empty_str_to_none(42) == 42

    def test_whitespace_string(self):
        """空白字符串不被转为None。"""
        assert empty_str_to_none("  ") == "  "


@pytest.mark.unit
class TestEmptyStrOrZeroToNone:
    """empty_str_or_zero_to_none 测试。"""

    def test_empty_string(self):
        assert empty_str_or_zero_to_none("") is None

    def test_zero(self):
        assert empty_str_or_zero_to_none(0) is None

    def test_none_value(self):
        assert empty_str_or_zero_to_none(None) is None

    def test_string_zero(self):
        """字符串"0"转成整数0再返回。"""
        assert empty_str_or_zero_to_none("0") == 0

    def test_positive_integer(self):
        assert empty_str_or_zero_to_none(5) == 5

    def test_negative_integer(self):
        assert empty_str_or_zero_to_none(-1) == -1

    def test_string_number(self):
        assert empty_str_or_zero_to_none("42") == 42

    def test_invalid_string(self):
        assert empty_str_or_zero_to_none("abc") is None


@pytest.mark.unit
class TestParseTimeRange:
    """parse_time_range 测试。"""

    def test_valid_range(self):
        result = parse_time_range(["2024-01-01", "2024-12-31"])
        assert result == ("2024-01-01", "2024-12-31")

    def test_none(self):
        assert parse_time_range(None) == (None, None)

    def test_empty_list(self):
        assert parse_time_range([]) == (None, None)

    def test_single_element(self):
        assert parse_time_range(["2024-01-01"]) == (None, None)

    def test_three_elements(self):
        assert parse_time_range(["a", "b", "c"]) == (None, None)


@pytest.mark.unit
class TestParseStatus:
    """parse_status 测试。"""

    def test_none(self):
        assert parse_status(None) is None

    def test_empty_string(self):
        assert parse_status("") is None

    def test_integer(self):
        assert parse_status(1) == 1

    def test_string_number(self):
        assert parse_status("1") == 1

    def test_invalid_string(self):
        assert parse_status("abc") is None

    def test_zero(self):
        assert parse_status(0) == 0

    def test_string_zero(self):
        assert parse_status("0") == 0


@pytest.mark.unit
class TestNormalizeOptionalId:
    """normalize_optional_id 测试。"""

    def test_none(self):
        assert normalize_optional_id(None) is None

    def test_empty_string(self):
        assert normalize_optional_id("") is None

    def test_zero_int(self):
        assert normalize_optional_id(0) is None

    def test_string_zero(self):
        assert normalize_optional_id("0") is None

    def test_valid_string(self):
        assert normalize_optional_id("abc123") == "abc123"

    def test_integer(self):
        assert normalize_optional_id(42) == "42"

    def test_non_zero_string(self):
        assert normalize_optional_id("123") == "123"


@pytest.mark.unit
class TestValidateUsernameEdgeCases:
    """validate_username 边界输入。"""

    def test_digit_only(self):
        assert validate_username("1234567890") == "1234567890"

    def test_underscore_only(self):
        assert validate_username("___") == "___"

    def test_mixed_pattern(self):
        assert validate_username("a1_b2_c3") == "a1_b2_c3"


@pytest.mark.unit
class TestEmptyStrOrZeroToNoneEdgeCases:
    """empty_str_or_zero_to_none 边界输入。"""

    def test_boolean_false(self):
        assert empty_str_or_zero_to_none(False) is None

    def test_float_zero(self):
        assert empty_str_or_zero_to_none(0.0) is None


@pytest.mark.unit
class TestNormalizeOptionalIdEdgeCases:
    """normalize_optional_id 边界输入。"""

    def test_negative_int(self):
        assert normalize_optional_id(-1) == "-1"

    def test_float_value(self):
        assert normalize_optional_id(1.5) == 1.5
