"""领域服务工厂测试。"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestGetPasswordService:
    """get_password_service 函数测试。"""

    def test_returns_password_service(self):
        """应返回 PasswordService 实例。"""
        from src.api.dependencies.domain_services import get_password_service
        from src.domain.services.password_service import PasswordService

        service = get_password_service()
        assert isinstance(service, PasswordService)


@pytest.mark.unit
class TestGetTokenService:
    """get_token_service 函数测试。"""

    @patch("src.api.dependencies.domain_services.get_settings")
    def test_returns_token_service(self, mock_get_settings):
        """应返回使用配置参数初始化的 TokenService 实例。"""
        mock_settings = MagicMock()
        mock_settings.JWT_SECRET_KEY = "test_secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
        mock_get_settings.return_value = mock_settings

        from src.api.dependencies.domain_services import get_token_service
        from src.domain.services.token_service import TokenService

        service = get_token_service()
        assert isinstance(service, TokenService)
        assert service._secret_key == "test_secret"
        assert service._algorithm == "HS256"
        assert service._access_expire_minutes == 30
        assert service._refresh_expire_days == 7

    @patch("src.api.dependencies.domain_services.get_settings")
    def test_reads_settings_each_call(self, mock_get_settings):
        """每次调用应重新读取配置。"""
        mock_settings = MagicMock()
        mock_settings.JWT_SECRET_KEY = "secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
        mock_get_settings.return_value = mock_settings

        from src.api.dependencies.domain_services import get_token_service

        get_token_service()
        get_token_service()
        assert mock_get_settings.call_count == 2
