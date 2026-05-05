"""配置 Settings 的单元测试。"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config.settings import DevelopmentSettings, ProductionSettings, Settings, QaEnvSettings, get_settings


@pytest.mark.unit
class TestSettings:
    """Settings 基础配置验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        settings = Settings(_env_file=None, APP_ENV="development")
        assert settings.APP_NAME == "Hello-FastApi"
        assert settings.APP_ENV == "development"
        assert settings.DEBUG is False
        assert settings.API_VERSION == "v1"
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.LOG_LEVEL == "INFO"

    def test_cors_origins_list_property(self):
        """测试 cors_origins_list 属性。"""
        settings = Settings(_env_file=None, CORS_ORIGINS="http://localhost:3000,http://localhost:8080", APP_ENV="development")
        assert settings.cors_origins_list == ["http://localhost:3000", "http://localhost:8080"]

    def test_cors_origins_list_empty(self):
        """测试空的 CORS 源列表。"""
        settings = Settings(_env_file=None, CORS_ORIGINS="", APP_ENV="development")
        assert settings.cors_origins_list == []

    def test_is_development_true(self):
        """测试 is_development 为 True。"""
        settings = Settings(_env_file=None, APP_ENV="development")
        assert settings.is_development is True
        assert settings.is_production is False
        assert settings.is_testing is False

    def test_is_production_true(self):
        """测试 is_production 为 True。"""
        settings = Settings(_env_file=None, APP_ENV="production")
        assert settings.is_production is True
        assert settings.is_development is False

    def test_is_testing_true(self):
        """测试 is_testing 为 True。"""
        settings = Settings(_env_file=None, APP_ENV="testing")
        assert settings.is_testing is True
        assert settings.is_development is False

    def test_valid_log_level_debug(self):
        """测试有效的 DEBUG 日志级别。"""
        settings = Settings(_env_file=None, LOG_LEVEL="DEBUG", APP_ENV="development")
        assert settings.LOG_LEVEL == "DEBUG"

    def test_valid_log_level_lowercase(self):
        """测试小写日志级别转换为大写。"""
        settings = Settings(_env_file=None, LOG_LEVEL="info", APP_ENV="development")
        assert settings.LOG_LEVEL == "INFO"

    def test_invalid_log_level(self):
        """测试无效的日志级别。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, LOG_LEVEL="TRACE", APP_ENV="development")

    def test_port_ge_limit(self):
        """测试端口最小值。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, PORT=0, APP_ENV="development")

    def test_port_le_limit(self):
        """测试端口最大值。"""
        settings = Settings(_env_file=None, PORT=65535, APP_ENV="development")
        assert settings.PORT == 65535

    def test_port_exceeds_limit(self):
        """测试端口超出最大值。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, PORT=65536, APP_ENV="development")

    def test_secret_key_too_short(self):
        """测试密钥过短。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, SECRET_KEY="short", APP_ENV="development")

    def test_jwt_secret_key_too_short(self):
        """测试 JWT 密钥过短。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, JWT_SECRET_KEY="short", APP_ENV="development")

    def test_access_token_expire_minutes_ge_limit(self):
        """测试访问令牌过期时间最小值。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, ACCESS_TOKEN_EXPIRE_MINUTES=0, APP_ENV="development")

    def test_refresh_token_expire_days_ge_limit(self):
        """测试刷新令牌过期天数最小值。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, REFRESH_TOKEN_EXPIRE_DAYS=0, APP_ENV="development")

    def test_rate_limit_times_ge_limit(self):
        """测试限流次数最小值。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, RATE_LIMIT_TIMES=0, APP_ENV="development")

    def test_rate_limit_seconds_ge_limit(self):
        """测试限流秒数最小值。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, RATE_LIMIT_SECONDS=0, APP_ENV="development")

    def test_invalid_app_env(self):
        """测试无效的环境值应报错。"""
        with pytest.raises(ValidationError):
            Settings(_env_file=None, APP_ENV="invalid_env")


@pytest.mark.unit
class TestDevelopmentSettings:
    """DevelopmentSettings 验证测试。"""

    def test_default_values(self):
        """测试开发环境默认值。"""
        settings = DevelopmentSettings(_env_file=None, APP_ENV="development")
        assert settings.DEBUG is True
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.APP_ENV == "development"


@pytest.mark.unit
class TestProductionSettings:
    """ProductionSettings 验证测试。"""

    def test_default_values(self):
        """测试生产环境默认值。"""
        settings = ProductionSettings(_env_file=None, APP_ENV="development")
        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "WARNING"
        assert settings.APP_ENV == "development"


@pytest.mark.unit
class TestQaEnvSettings:
    """QaEnvSettings 验证测试。"""

    def test_default_values(self):
        """测试测试环境默认值。"""
        settings = QaEnvSettings(_env_file=None, APP_ENV="development")
        assert settings.DEBUG is True
        assert settings.DATABASE_URL == "sqlite+aiosqlite:///./sql/test.db"
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.APP_ENV == "development"


@pytest.mark.unit
class TestGetSettings:
    """get_settings 函数验证测试。"""

    def test_default_env_development(self):
        """测试默认环境为 development。"""
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings()
            assert settings.APP_ENV == "development"
            assert isinstance(settings, DevelopmentSettings)

    def test_env_production(self):
        """测试生产环境。"""
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            settings = get_settings()
            assert isinstance(settings, ProductionSettings)

    def test_env_testing(self):
        """测试测试环境。"""
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            settings = get_settings()
            assert isinstance(settings, QaEnvSettings)

    def test_env_development(self):
        """测试开发环境。"""
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=True):
            settings = get_settings()
            assert isinstance(settings, DevelopmentSettings)

    def test_invalid_env_selection_falls_back_to_development(self):
        """测试 get_settings 中 env 选择逻辑回退到 development（构造函数层面受 env 源限制）。"""
        with patch.dict(os.environ, {"APP_ENV": "invalid"}, clear=True), pytest.raises(ValidationError):
            get_settings()
