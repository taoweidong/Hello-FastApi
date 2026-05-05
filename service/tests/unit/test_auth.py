"""认证和令牌服务的单元测试。"""

import pytest

from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService

# 测试用 TokenService 配置
TEST_SECRET_KEY = "test-secret-key-for-testing-only"
TEST_ALGORITHM = "HS256"
TEST_ACCESS_EXPIRE_MINUTES = 30
TEST_REFRESH_EXPIRE_DAYS = 7


@pytest.fixture
def token_service() -> TokenService:
    """提供测试用的 TokenService 实例。"""
    return TokenService(secret_key=TEST_SECRET_KEY, algorithm=TEST_ALGORITHM, access_expire_minutes=TEST_ACCESS_EXPIRE_MINUTES, refresh_expire_days=TEST_REFRESH_EXPIRE_DAYS)


class TestPasswordService:
    """PasswordService 测试。"""

    def test_hash_password(self):
        password = "TestPassword123"
        hashed = PasswordService.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        password = "TestPassword123"
        hashed = PasswordService.hash_password(password)
        assert PasswordService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "TestPassword123"
        hashed = PasswordService.hash_password(password)
        assert PasswordService.verify_password("WrongPassword", hashed) is False


class TestTokenService:
    """TokenService 测试（使用实例方法）。"""

    def test_create_access_token(self, token_service: TokenService):
        data = {"sub": "test-user-id", "username": "testuser"}
        token = token_service.create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, token_service: TokenService):
        data = {"sub": "test-user-id", "username": "testuser"}
        token = token_service.create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self, token_service: TokenService):
        data = {"sub": "test-user-id", "username": "testuser"}
        token = token_service.create_access_token(data)
        payload = token_service.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user-id"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"

    def test_decode_invalid_token(self, token_service: TokenService):
        payload = token_service.decode_token("invalid-token")
        assert payload is None

    def test_verify_token_type_access(self, token_service: TokenService):
        data = {"sub": "test-user-id"}
        token = token_service.create_access_token(data)
        payload = token_service.decode_token(token)
        assert TokenService.verify_token_type(payload, "access") is True
        assert TokenService.verify_token_type(payload, "refresh") is False

    def test_verify_token_type_refresh(self, token_service: TokenService):
        data = {"sub": "test-user-id"}
        token = token_service.create_refresh_token(data)
        payload = token_service.decode_token(token)
        assert TokenService.verify_token_type(payload, "refresh") is True
        assert TokenService.verify_token_type(payload, "access") is False
