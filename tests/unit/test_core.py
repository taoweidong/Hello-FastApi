"""核心工具和验证器的单元测试。"""

from src.core.utils import is_strong_password, is_valid_email


class TestEmailValidation:
    """邮箱验证测试。"""

    def test_valid_email(self):
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user.name@domain.org") is True

    def test_invalid_email(self):
        assert is_valid_email("invalid") is False
        assert is_valid_email("@domain.com") is False
        assert is_valid_email("user@") is False


class TestPasswordStrength:
    """密码强度验证测试。"""

    def test_strong_password(self):
        assert is_strong_password("Test1234") is True
        assert is_strong_password("MyP@ssw0rd") is True

    def test_weak_password_short(self):
        assert is_strong_password("Te1") is False

    def test_weak_password_no_upper(self):
        assert is_strong_password("test1234") is False

    def test_weak_password_no_lower(self):
        assert is_strong_password("TEST1234") is False

    def test_weak_password_no_digit(self):
        assert is_strong_password("TestPassword") is False
