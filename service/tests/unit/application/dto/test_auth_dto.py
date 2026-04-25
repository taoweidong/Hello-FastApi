"""认证 DTO 的单元测试。"""

import pytest
from pydantic import ValidationError

from src.application.dto.auth_dto import (
    LoginDTO,
    LoginResponseDTO,
    RefreshTokenDTO,
    RegisterDTO,
    TokenResponseDTO,
    UserInfoDTO,
)


@pytest.mark.unit
class TestLoginDTO:
    """LoginDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的登录数据。"""
        dto = LoginDTO(username="admin", password="TestPass123")
        assert dto.username == "admin"
        assert dto.password == "TestPass123"

    def test_missing_username(self):
        """测试缺少用户名。"""
        with pytest.raises(ValidationError):
            LoginDTO(password="TestPass123")


@pytest.mark.unit
class TestRegisterDTO:
    """RegisterDTO 验证测试。"""

    def test_valid_input_required_only(self):
        """测试仅必填字段。"""
        dto = RegisterDTO(username="newuser", password="TestPass123")
        assert dto.username == "newuser"
        assert dto.password == "TestPass123"
        assert dto.nickname is None
        assert dto.email is None
        assert dto.phone is None

    def test_valid_input_all_fields(self):
        """测试所有字段。"""
        dto = RegisterDTO(username="newuser", password="TestPass123", nickname="昵称", email="user@example.com", phone="13800138000")
        assert dto.nickname == "昵称"
        assert dto.email == "user@example.com"
        assert dto.phone == "13800138000"

    def test_missing_username(self):
        """测试缺少用户名。"""
        with pytest.raises(ValidationError):
            RegisterDTO(password="TestPass123")


@pytest.mark.unit
class TestRefreshTokenDTO:
    """RefreshTokenDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的刷新令牌数据。"""
        dto = RefreshTokenDTO(refreshToken="some-refresh-token")
        assert dto.refreshToken == "some-refresh-token"

    def test_missing_refresh_token(self):
        """测试缺少刷新令牌。"""
        with pytest.raises(ValidationError):
            RefreshTokenDTO()


@pytest.mark.unit
class TestUserInfoDTO:
    """UserInfoDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的用户信息数据。"""
        dto = UserInfoDTO(id="1", username="admin")
        assert dto.id == "1"
        assert dto.username == "admin"
        assert dto.isActive == 1
        assert dto.nickname is None
        assert dto.gender is None

    def test_valid_input_all_fields(self):
        """测试所有字段。"""
        dto = UserInfoDTO(id="1", username="admin", nickname="管理员", firstName="张", lastName="三", avatar="https://example.com/avatar.png", email="admin@example.com", phone="13800138000", gender=1, isActive=1)
        assert dto.nickname == "管理员"
        assert dto.gender == 1

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            UserInfoDTO(username="admin")

    def test_missing_username(self):
        """测试缺少用户名。"""
        with pytest.raises(ValidationError):
            UserInfoDTO(id="1")


@pytest.mark.unit
class TestTokenResponseDTO:
    """TokenResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的令牌响应数据。"""
        dto = TokenResponseDTO(accessToken="token", expires=3600, refreshToken="refresh")
        assert dto.accessToken == "token"
        assert dto.expires == 3600
        assert dto.refreshToken == "refresh"

    def test_missing_access_token(self):
        """测试缺少访问令牌。"""
        with pytest.raises(ValidationError):
            TokenResponseDTO(expires=3600, refreshToken="refresh")


@pytest.mark.unit
class TestLoginResponseDTO:
    """LoginResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的登录响应数据。"""
        dto = LoginResponseDTO(accessToken="token", expires=3600, refreshToken="refresh")
        assert dto.accessToken == "token"
        assert dto.expires == 3600
        assert dto.userInfo is None
        assert dto.roles == []

    def test_with_user_info(self):
        """测试包含用户信息的登录响应。"""
        dto = LoginResponseDTO(
            accessToken="token",
            expires=3600,
            refreshToken="refresh",
            userInfo=UserInfoDTO(id="1", username="admin"),
            roles=["admin"],
        )
        assert dto.userInfo is not None
        assert dto.userInfo.id == "1"
        assert dto.roles == ["admin"]

    def test_missing_expires(self):
        """测试缺少过期时间。"""
        with pytest.raises(ValidationError):
            LoginResponseDTO(accessToken="token", refreshToken="refresh")
