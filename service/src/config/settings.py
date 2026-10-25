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
from typing import Any, Literal

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

# 上传目录（头像等静态资源，通过 /media 挂载对外提供）
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 头像存储子目录
AVATAR_DIR = UPLOAD_DIR / "avatars"
AVATAR_DIR.mkdir(exist_ok=True)


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
    REDIS_CONNECT_TIMEOUT: float = Field(default=1.0, gt=0)  # 连接超时秒数，Redis 不可用时避免长时间阻塞
    REDIS_SOCKET_TIMEOUT: float = Field(default=1.0, gt=0)  # 读写超时秒数

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
    CACHE_DICT_TTL: int = Field(default=3600, ge=1)  # 1 小时（字典数据缓存）

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


# 已知的不安全密钥特征：占位符/示例值的前缀。生产环境命中任一特征即拒绝启动。
_INSECURE_SECRET_MARKERS: tuple[str, ...] = ("your-", "change-this-", "dev-secret", "test-secret")


def _ensure_production_secrets(s: Settings) -> None:
    """生产环境下校验密钥未使用占位默认值，命中则 fail-fast 拒绝启动。

    防止使用仓库内的示例密钥（模型默认值、.env.production 占位符、
    docker-compose 默认值）部署生产，导致 JWT 可被任意伪造。
    """
    if not s.is_production:
        return
    for field_name in ("SECRET_KEY", "JWT_SECRET_KEY"):
        value = getattr(s, field_name).lower()
        if any(marker in value for marker in _INSECURE_SECRET_MARKERS):
            raise ValueError(
                f"生产环境检测到不安全的 {field_name} 占位值，"
                f"请通过环境变量或 .env.production 设置强随机密钥（如 openssl rand -hex 32）"
            )


# 各环境的覆盖配置
_ENV_OVERRIDES: dict[str, dict[str, Any]] = {
    "development": {},
    "production": {"DEBUG": False, "LOG_LEVEL": "WARNING"},
    "testing": {"DEBUG": True, "DATABASE_URL": "sqlite+aiosqlite:///./sql/test.db", "LOG_LEVEL": "DEBUG"},
}

_ENV_FILES: dict[str, list[str]] = {
    "development": [".env", ".env.development"],
    "production": [".env", ".env.production"],
    "testing": [".env", ".env.testing"],
}


def _detect_env() -> str:
    """从环境变量或 .env 文件中检测运行环境。

    Returns:
        str: detection environment name (development/production/testing)
    """
    env = os.getenv("APP_ENV")
    if env in ("development", "production", "testing"):
        return env

    env_file_path = BASE_DIR / ".env"
    if env_file_path.exists():
        try:
            with open(env_file_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("APP_ENV="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val in ("development", "production", "testing"):
                            return val
                        break
        except OSError:
            pass

    return "development"


def get_settings(env: str | None = None) -> Settings:
    """根据运行环境获取配置实例。

    When *env* is ``None`` the function auto-detects the environment via
    :func:`_detect_env` and loads the matching overrides + env-file chain.

    Args:
        env: explicit environment name (development/production/testing).
             When ``None`` auto-detection kicks in.

    Configuration value precedence (highest to lowest)::

        constructor kwargs  >  .env.{environment}  >  .env  >  model defaults

    Returns:
        Settings: configuration instance
    """
    if env is None:
        env = _detect_env()

    valid_envs = ("development", "production", "testing")
    if env not in valid_envs:
        env = "development"

    # 显式指定 env 时以参数为准（进程环境变量中的 APP_ENV 可能指向其他环境）
    #
    # 注意：pydantic-settings v2 在 __init__ 中接收的是 `_env_file`（带下划线前缀），
    # 写成 `env_file` 会被当作未知字段并在 extra="ignore" 下**静默丢弃**，
    # 导致 .env / .env.{environment} 从未被加载、整站一直跑在模型默认值上。
    # 修复前表现为：开发环境 REDIS_URL 取默认的 redis://localhost:6379/0，
    # Windows 下 localhost 优先解析到 IPv6 ::1，而本机 Redis 只监听 IPv4，
    # 异步连接必然超时 → 缓存永久降级，单次请求被拖慢到 3s 量级。
    s = Settings(_env_file=_ENV_FILES[env], APP_ENV=env, **_ENV_OVERRIDES[env])  # type: ignore[call-arg]
    _ensure_production_secrets(s)
    return s


@lru_cache
def get_cached_settings() -> Settings:
    """获取缓存的配置实例（单例模式）。

    Returns:
        Settings: 配置实例
    """
    return get_settings()


# 导出配置实例
settings = get_settings()
