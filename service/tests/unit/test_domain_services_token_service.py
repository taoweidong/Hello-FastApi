"""令牌服务的单元测试。

测试 TokenService 的访问令牌和刷新令牌创建、验证和解码功能。
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from src.domain.services.token_service import TokenService

TEST_SECRET_KEY = "test-secret-key"
TEST_ALGORITHM = "HS256"


@pytest.mark.unit
class TestTokenService:
    """TokenService 测试类。"""

    @pytest.fixture
    def token_service(self):
        """创建令牌服务实例。"""
        return TokenService(
            secret_key=TEST_SECRET_KEY,
            algorithm=TEST_ALGORITHM,
            access_expire_minutes=30,
            refresh_expire_days=7,
        )

    # ---- 创建访问令牌测试 ----

    def test_create_access_token(self, token_service):
        """测试创建访问令牌。"""
        token = token_service.create_access_token({"sub": "user-1", "username": "testuser"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_data(self, token_service):
        """测试访问令牌包含数据。"""
        token = token_service.create_access_token({"sub": "user-1", "username": "testuser"})
        payload = token_service.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-1"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"

    def test_create_access_token_default_expiration(self, token_service):
        """测试访问令牌默认过期时间（30分钟）。"""
        token = token_service.create_access_token({"sub": "user-1"})
        payload = token_service.decode_token(token)
        exp = payload["exp"]
        now = datetime.now(timezone.utc).timestamp()
        # 允许1分钟误差
        assert exp <= (now + 30 * 60 + 60)
        assert exp >= (now - 60)  # 至少是当前时间之后

    def test_create_access_token_custom_expiration(self, token_service):
        """测试访问令牌自定义过期时间。"""
        custom_delta = timedelta(minutes=60)
        token = token_service.create_access_token({"sub": "user-1"}, expires_delta=custom_delta)
        payload = token_service.decode_token(token)
        exp = payload["exp"]
        now = datetime.now(timezone.utc).timestamp()
        # 允许1分钟误差
        assert exp <= (now + 60 * 60 + 60)
        assert exp >= (now - 60)

    # ---- 创建刷新令牌测试 ----

    def test_create_refresh_token(self, token_service):
        """测试创建刷新令牌。"""
        token = token_service.create_refresh_token({"sub": "user-1", "username": "testuser"})
        assert token is not None
        assert isinstance(token, str)

    def test_create_refresh_token_contains_data(self, token_service):
        """测试刷新令牌包含数据。"""
        token = token_service.create_refresh_token({"sub": "user-1", "username": "testuser"})
        payload = token_service.decode_token(token)
        assert payload["sub"] == "user-1"
        assert payload["username"] == "testuser"
        assert payload["type"] == "refresh"

    def test_create_refresh_token_default_expiration(self, token_service):
        """测试刷新令牌默认过期时间（7天）。"""
        token = token_service.create_refresh_token({"sub": "user-1"})
        payload = token_service.decode_token(token)
        exp = payload["exp"]
        now = datetime.now(timezone.utc).timestamp()
        # 允许1分钟误差
        assert exp <= (now + 7 * 24 * 60 * 60 + 60)
        assert exp >= (now - 60)

    def test_create_refresh_token_custom_expiration(self, token_service):
        """测试刷新令牌自定义过期时间。"""
        custom_delta = timedelta(days=30)
        token = token_service.create_refresh_token({"sub": "user-1"}, expires_delta=custom_delta)
        payload = token_service.decode_token(token)
        exp = payload["exp"]
        now = datetime.now(timezone.utc).timestamp()
        # 允许1分钟误差
        assert exp <= (now + 30 * 24 * 60 * 60 + 60)
        assert exp >= (now - 60)

    # ---- 解码令牌测试 ----

    def test_decode_token_valid(self, token_service):
        """测试解码有效令牌。"""
        token = token_service.create_access_token({"sub": "user-1"})
        payload = token_service.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-1"

    def test_decode_token_invalid(self, token_service):
        """测试解码无效令牌。"""
        payload = token_service.decode_token("invalid-token")
        assert payload is None

    def test_decode_token_tampered(self, token_service):
        """测试解码被篡改的令牌。"""
        token = token_service.create_access_token({"sub": "user-1"})
        tampered = token[:-5] + "xxxxx"
        payload = token_service.decode_token(tampered)
        assert payload is None

    def test_decode_token_wrong_secret(self, token_service):
        """测试使用错误密钥解码。"""
        token = token_service.create_access_token({"sub": "user-1"})
        # 使用不同密钥的服务解码
        other_service = TokenService(
            secret_key="wrong-secret",
            algorithm=TEST_ALGORITHM,
            access_expire_minutes=30,
            refresh_expire_days=7,
        )
        payload = other_service.decode_token(token)
        assert payload is None

    # ---- 验证令牌类型测试 ----

    def test_verify_token_type_access(self, token_service):
        """测试验证访问令牌类型。"""
        token = token_service.create_access_token({"sub": "user-1"})
        payload = token_service.decode_token(token)
        result = TokenService.verify_token_type(payload, "access")
        assert result is True

    def test_verify_token_type_refresh(self, token_service):
        """测试验证刷新令牌类型。"""
        token = token_service.create_refresh_token({"sub": "user-1"})
        payload = token_service.decode_token(token)
        result = TokenService.verify_token_type(payload, "refresh")
        assert result is True

    def test_verify_token_type_mismatch(self, token_service):
        """测试令牌类型不匹配。"""
        token = token_service.create_access_token({"sub": "user-1"})
        payload = token_service.decode_token(token)
        result = TokenService.verify_token_type(payload, "refresh")
        assert result is False

    def test_verify_token_type_missing(self, token_service):
        """测试令牌类型缺失。"""
        payload = {"sub": "user-1"}  # 无 type 字段
        result = TokenService.verify_token_type(payload, "access")
        assert result is False

    # ---- 边界情况测试 ----

    def test_create_token_with_empty_data(self, token_service):
        """测试创建令��（空数据）。"""
        token = token_service.create_access_token({})
        payload = token_service.decode_token(token)
        assert payload is not None

    def test_decode_token_expired(self, token_service):
        """测试解码过期令牌。"""
        # 创建一个非常短的过期时间（1秒）
        with patch("src.domain.services.token_service.datetime") as mock_datetime:
            mock_now = datetime(2020, 1, 1, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            # 过期时间是 -1 秒前（已过期）
            with patch("time.time") as mock_time:
                # 当前时间设为 2020-01-01
                base_time = datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp()
                mock_time.return_value = base_time
                # 创建 1 秒后过期的令牌（实际已过期1秒）
                token = token_service.create_access_token({"sub": "user-1"}, expires_delta=timedelta(seconds=-1))

        # jose 库会验证过期时间
        payload = token_service.decode_token(token)
        assert payload is None or "exp" not in payload
