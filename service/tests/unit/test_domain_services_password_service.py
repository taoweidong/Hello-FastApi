"""密码服务的单元测试。

测试 PasswordService 的密码哈希和验证功能。
"""

import pytest

from src.domain.services.password_service import PasswordService


@pytest.mark.unit
class TestPasswordService:
    """PasswordService 测试类。"""

    def test_hash_password(self):
        """测试密码哈希。"""
        hashed = PasswordService.hash_password("TestPass123")
        assert hashed is not None
        assert hashed != "TestPass123"
        assert len(hashed) > 0

    def test_hash_password_consistency(self):
        """测试同一密码哈希后结果一致（bcrypt 自动生成 salt）。"""
        hashed1 = PasswordService.hash_password("TestPass123")
        hashed2 = PasswordService.hash_password("TestPass123")
        # bcrypt 每次生成不同的 salt，所以哈希值不同
        assert hashed1 != hashed2

    def test_verify_password_correct(self):
        """测试验证正确密码。"""
        hashed = PasswordService.hash_password("TestPass123")
        result = PasswordService.verify_password("TestPass123", hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """测试验证错误密码。"""
        hashed = PasswordService.hash_password("CorrectPass123")
        result = PasswordService.verify_password("WrongPass123", hashed)
        assert result is False

    def test_verify_password_empty_correct(self):
        """测试空密码验证。"""
        hashed = PasswordService.hash_password("")
        result = PasswordService.verify_password("", hashed)
        assert result is True

    def test_verify_password_empty_wrong(self):
        """测试空密码验证错误。"""
        hashed = PasswordService.hash_password("password")
        result = PasswordService.verify_password("", hashed)
        assert result is False

    def test_hash_password_unicode(self):
        """测试 Unicode 密码哈希。"""
        hashed = PasswordService.hash_password("测试密码123")
        result = PasswordService.verify_password("测试密码123", hashed)
        assert result is True

    def test_verify_password_long(self):
        """测试长密码。"""
        long_password = "A" * 1000
        hashed = PasswordService.hash_password(long_password)
        result = PasswordService.verify_password(long_password, hashed)
        assert result is True
