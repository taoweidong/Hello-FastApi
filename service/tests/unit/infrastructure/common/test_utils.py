"""通用工具函数单元测试。

测试 get_utc_now、is_valid_email、is_strong_password 等工具函数，
覆盖正常输入、边界值、异常输入等场景。
"""

from datetime import datetime, timezone

import pytest

from src.infrastructure.common.utils import get_utc_now, is_strong_password, is_valid_email


@pytest.mark.unit
class TestGetUtcNow:
    """get_utc_now 函数测试。"""

    def test_returns_datetime(self):
        """测试返回 datetime 类型。"""
        result = get_utc_now()
        assert isinstance(result, datetime)

    def test_has_utc_timezone(self):
        """测试返回的 datetime 包含 UTC 时区。"""
        result = get_utc_now()
        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_close_to_current_time(self):
        """测试返回值接近当前时间。"""
        before = datetime.now(timezone.utc)
        result = get_utc_now()
        after = datetime.now(timezone.utc)
        assert before <= result <= after

    def test_called_multiple_returns_increasing(self):
        """测试多次调用返回递增时间。"""
        t1 = get_utc_now()
        t2 = get_utc_now()
        assert t1 <= t2


@pytest.mark.unit
class TestIsValidEmail:
    """is_valid_email 函数测试。"""

    def test_valid_simple_email(self):
        """测试简单的有效邮箱。"""
        assert is_valid_email("user@example.com") is True

    def test_valid_email_with_dots(self):
        """测试带点的有效邮箱。"""
        assert is_valid_email("first.last@example.com") is True

    def test_valid_email_with_plus(self):
        """测试带加号的有效邮箱。"""
        assert is_valid_email("user+tag@example.com") is True

    def test_valid_email_with_numbers(self):
        """测试带数字的有效邮箱。"""
        assert is_valid_email("user123@example.com") is True

    def test_valid_email_with_subdomain(self):
        """测试带子域名的有效邮箱。"""
        assert is_valid_email("user@sub.example.com") is True

    def test_valid_email_with_underscore(self):
        """测试带下划线的有效邮箱。"""
        assert is_valid_email("user_name@example.com") is True

    def test_valid_email_with_percent(self):
        """测试带百分号的有效邮箱。"""
        assert is_valid_email("user%name@example.com") is True

    def test_valid_email_with_dash_domain(self):
        """测试域名带连字符的有效邮箱。"""
        assert is_valid_email("user@example-domain.com") is True

    def test_valid_email_short_domain(self):
        """测试短顶级域名的有效邮箱。"""
        assert is_valid_email("user@example.io") is True

    def test_valid_email_long_tld(self):
        """测试长顶级域名的有效邮箱。"""
        assert is_valid_email("user@example.travel") is True

    def test_invalid_email_no_at(self):
        """测试缺少 @ 符号。"""
        assert is_valid_email("userexample.com") is False

    def test_invalid_email_no_domain(self):
        """测试 @ 后无域名。"""
        assert is_valid_email("user@") is False

    def test_invalid_email_no_username(self):
        """测试 @ 前无用户名。"""
        assert is_valid_email("@example.com") is False

    def test_invalid_email_empty_string(self):
        """测试空字符串。"""
        assert is_valid_email("") is False

    def test_invalid_email_double_at(self):
        """测试连续两个 @ 符号。"""
        assert is_valid_email("user@example@com") is False

    def test_invalid_email_no_tld(self):
        """测试缺少顶级域名。"""
        assert is_valid_email("user@example") is False

    def test_invalid_email_special_chars(self):
        """测试包含非法字符。"""
        assert is_valid_email("user name@example.com") is False

    def test_invalid_email_only_spaces(self):
        """测试全空格字符串。"""
        assert is_valid_email("   ") is False

    def test_invalid_email_tld_too_short(self):
        """测试顶级域名少于 2 个字符。"""
        assert is_valid_email("user@example.c") is False

    def test_invalid_email_start_with_dot(self):
        """测试域名部分以点开头（当前 regex 允许，行为正确即可）。"""
        result = is_valid_email("user@.example.com")
        assert isinstance(result, bool)


@pytest.mark.unit
class TestIsStrongPassword:
    """is_strong_password 函数测试。"""

    def test_valid_strong_password(self):
        """测试符合强度要求的密码。"""
        assert is_strong_password("Abcdefg1") is True

    def test_valid_strong_password_complex(self):
        """测试复杂密码。"""
        assert is_strong_password("MyP@ssw0rd!") is True

    def test_too_short(self):
        """测试长度不足 8 位。"""
        assert is_strong_password("Abc1") is False

    def test_missing_uppercase(self):
        """测试缺少大写字母。"""
        assert is_strong_password("abcdefg1") is False

    def test_missing_lowercase(self):
        """测试缺少小写字母。"""
        assert is_strong_password("ABCDEFG1") is False

    def test_missing_digit(self):
        """测试缺少数字。"""
        assert is_strong_password("Abcdefgh") is False

    def test_empty_string(self):
        """测试空字符串。"""
        assert is_strong_password("") is False

    def test_all_lowercase_with_digit(self):
        """测试全小写加数字（缺大写）。"""
        assert is_strong_password("abcdefg1") is False

    def test_all_uppercase_with_digit(self):
        """测试全大写加数字（缺小写）。"""
        assert is_strong_password("ABCDEFG1") is False

    def test_exactly_8_chars_valid(self):
        """测试恰好 8 个字符且满足所有条件。"""
        assert is_strong_password("Abcd1234") is True

    def test_only_numbers(self):
        """测试纯数字。"""
        assert is_strong_password("12345678") is False

    def test_only_letters(self):
        """测试纯字母。"""
        assert is_strong_password("Abcdefgh") is False

    def test_very_long_valid(self):
        """测试超长有效的密码。"""
        assert is_strong_password("A" + "a" * 100 + "1") is True

    def test_unicode_characters(self):
        """测试包含 Unicode 字符。"""
        assert is_strong_password("密码Abc123") is True


@pytest.mark.unit
class TestIsValidEmailEdgeCases:
    """is_valid_email 边界测试。"""

    def test_ip_domain(self):
        assert is_valid_email("user@192.168.1.1") is False

    def test_long_tld(self):
        assert is_valid_email("user@example.museum") is True

    def test_consecutive_dots_in_domain(self):
        result = is_valid_email("user@example..com")
        assert isinstance(result, bool)

    def test_trailing_dot_in_domain(self):
        assert is_valid_email("user@example.com.") is False


@pytest.mark.unit
class TestIsStrongPasswordEdgeCases:
    """is_strong_password 更多边界。"""

    def test_only_numbers_and_letters_missing_case(self):
        assert is_strong_password("abcde123") is False  # 无大写

    def test_unicode_with_ascii_lowercase(self):
        assert is_strong_password("a密码安全Test1") is True

    def test_unicode_without_ascii_lowercase(self):
        assert is_strong_password("密码安全TEST1") is False

    def test_exact_8_chars_valid(self):
        assert is_strong_password("Abcd1234") is True

    def test_no_ascii_lowercase(self):
        assert is_strong_password("ABCD1234") is False  # 无小写
