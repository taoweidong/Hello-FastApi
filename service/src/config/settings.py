"""应用配置模块。

支持多环境配置：
- development: 开发环境，加载 .env.development
- production: 生产环境，加载 .env.production
- testing: 测试环境，加载 .env.testing

使用方式：
1. 设置环境变量 APP_ENV 指定运行环境
2. 或创建 .env 文件并在其中设置 APP_ENV
3. 系统会自动加载对应的环境配置文件
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 环境类型
Environment = Literal["development", "production", "testing"]

# 项目根目录（config 在 src 目录下，需要向上两级）
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 数据库目录
SQL_DIR = BASE_DIR / "sql"
SQL_DIR.mkdir(exist_ok=True)

# 日志目录
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# 文档目录
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """应用配置类，从环境变量和 .env 文件加载配置。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True)

    # ============ 应用配置 ============
    APP_NAME: str = "Hello-FastApi"
    APP_ENV: Environment = "development"
    DEBUG: bool = False
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", min_length=32)
    API_VERSION: str = "v1"

    # ============ 服务器配置 ============
    HOST: str = "0.0.0.0"
    PORT: int = Field(default=8000, ge=1, le=65535)

    # ============ 数据库配置 ============
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql/dev.db"
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=60)  # 1 小时回收连接
    DATABASE_POOL_PRE_PING: bool = True  # 连接前检测有效性

    # ============ Redis 配置 ============
    REDIS_URL: str = "redis://localhost:6379/0"

    # ============ JWT 配置 ============
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret-key-change-in-production", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1)

    # ============ CORS 配置 ============
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> list[str]:
        """解析 CORS 源列表。"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # ============ 限流配置 ============
    RATE_LIMIT_TIMES: int = Field(default=100, ge=1)
    RATE_LIMIT_SECONDS: int = Field(default=60, ge=1)
    RATE_LIMIT_STORAGE: str = "redis"  # redis 或 memory
    RATE_LIMIT_WHITELIST_IPS: str = ""  # 逗号分隔的 IP 白名单

    # ============ 日志配置 ============
    LOG_LEVEL: str = "INFO"

    # ============ 缓存 TTL 配置 ============
    CACHE_PERMISSIONS_TTL: int = Field(default=300, ge=1)  # 5 分钟
    CACHE_USER_INFO_TTL: int = Field(default=300, ge=1)  # 5 分钟
    CACHE_MENU_ALL_TTL: int = Field(default=600, ge=1)  # 10 分钟
    CACHE_TOKEN_BLACKLIST_TTL: int = Field(default=86400, ge=1)  # 24 小时

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别。"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper

    @property
    def is_development(self) -> bool:
        """是否为开发环境。"""
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        """是否为生产环境。"""
        return self.APP_ENV == "production"

    @property
    def is_testing(self) -> bool:
        """是否为测试环境。"""
        return self.APP_ENV == "testing"


class DevelopmentSettings(Settings):
    """开发环境配置。"""

    model_config = SettingsConfigDict(
        env_file=[".env", ".env.development"], env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    """生产环境配置。"""

    model_config = SettingsConfigDict(
        env_file=[".env", ".env.production"], env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )

    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"


class QaEnvSettings(Settings):
    """测试环境配置。"""

    model_config = SettingsConfigDict(
        env_file=[".env", ".env.testing"], env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )

    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql/test.db"
    LOG_LEVEL: str = "DEBUG"


def get_settings() -> Settings:
    """根据 APP_ENV 环境变量获取对应的配置实例。

    配置加载顺序：
    1. 系统环境变量
    2. .env.{environment} 环境配置文件
    3. .env 通用配置文件
    4. 默认值

    Returns:
        Settings: 配置实例
    """
    # 首先尝试从环境变量获取 APP_ENV
    env = os.getenv("APP_ENV", "development")

    # 如果环境变量中没有，尝试从 .env 文件读取
    if env == "development":
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("APP_ENV="):
                        env = line.split("=", 1)[1].strip()
                        break

    # 验证环境值
    valid_envs = {"development", "production", "testing"}
    if env not in valid_envs:
        env = "development"

    # 返回对应环境的配置
    settings_map: dict[str, type[Settings]] = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": QaEnvSettings,
    }

    settings_class = settings_map.get(env, DevelopmentSettings)
    return settings_class()


@lru_cache
def get_cached_settings() -> Settings:
    """获取缓存的配置实例（单例模式）。

    Returns:
        Settings: 配置实例
    """
    return get_settings()


# 导出配置实例
settings = get_settings()
