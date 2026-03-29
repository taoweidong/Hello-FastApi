"""认证和令牌服务的单元测试。"""

from src.domain.auth.password_service import PasswordService
from src.domain.auth.token_service import TokenService


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
    """TokenService 测试。"""

    def test_create_access_token(self):
        data = {"sub": "test-user-id", "username": "testuser"}
        token = TokenService.create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        data = {"sub": "test-user-id", "username": "testuser"}
        token = TokenService.create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        data = {"sub": "test-user-id", "username": "testuser"}
        token = TokenService.create_access_token(data)
        payload = TokenService.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user-id"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"

    def test_decode_invalid_token(self):
        payload = TokenService.decode_token("invalid-token")
        assert payload is None

    def test_verify_token_type_access(self):
        data = {"sub": "test-user-id"}
        token = TokenService.create_access_token(data)
        payload = TokenService.decode_token(token)
        assert TokenService.verify_token_type(payload, "access") is True
        assert TokenService.verify_token_type(payload, "refresh") is False

    def test_verify_token_type_refresh(self):
        data = {"sub": "test-user-id"}
        token = TokenService.create_refresh_token(data)
        payload = TokenService.decode_token(token)
        assert TokenService.verify_token_type(payload, "refresh") is True
        assert TokenService.verify_token_type(payload, "access") is False
