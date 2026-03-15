"""认证领域 - JWT 令牌管理和安全。"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from src.config.settings import settings


class TokenService:
    """JWT 令牌操作的领域服务。"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """创建 JWT 访问令牌。"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "type": "access"})
        encoded: str = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """创建 JWT 刷新令牌。"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded: str = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        """解码并验证 JWT 令牌。"""
        try:
            payload: dict[str, Any] = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError:
            return None

    @staticmethod
    def verify_token_type(payload: dict, expected_type: str) -> bool:
        """验证令牌类型是否匹配预期类型。"""
        return payload.get("type") == expected_type
