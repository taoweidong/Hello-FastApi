"""认证领域 - JWT 令牌服务。

提供 JWT 令牌创建、验证和解码功能的领域服务。
此服务通过构造函数注入配置参数，不直接依赖配置模块。
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt


class TokenService:
    """JWT 令牌操作的领域服务。

    通过构造函数注入配置参数，实现与配置层的解耦。
    支持访问令牌和刷新令牌的创建与验证。
    """

    def __init__(self, secret_key: str, algorithm: str, access_expire_minutes: int, refresh_expire_days: int):
        """初始化令牌服务。

        Args:
            secret_key: JWT 签名密钥
            algorithm: JWT 签名算法（如 HS256）
            access_expire_minutes: 访问令牌过期时间（分钟）
            refresh_expire_days: 刷新令牌过期时间（天）
        """
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_expire_minutes = access_expire_minutes
        self._refresh_expire_days = refresh_expire_days

    def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """创建 JWT 访问令牌。

        Args:
            data: 要编码到令牌中的数据
            expires_delta: 自定义过期时间间隔（可选）

        Returns:
            编码后的 JWT 令牌字符串
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=self._access_expire_minutes))
        to_encode.update({"exp": expire, "type": "access"})
        encoded: str = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return encoded

    def create_refresh_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """创建 JWT 刷新令牌。

        Args:
            data: 要编码到令牌中的数据
            expires_delta: 自定义过期时间间隔（可选）

        Returns:
            编码后的 JWT 令牌字符串
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=self._refresh_expire_days))
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded: str = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return encoded

    def decode_token(self, token: str) -> dict[str, Any] | None:
        """解码并验证 JWT 令牌。

        Args:
            token: JWT 令牌字符串

        Returns:
            解码后的载荷字典，验证失败返回 None
        """
        try:
            payload: dict[str, Any] = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return payload
        except JWTError:
            return None

    @staticmethod
    def verify_token_type(payload: dict[str, Any], expected_type: str) -> bool:
        """验证令牌类型是否匹配预期类型。

        Args:
            payload: 解码后的令牌载荷
            expected_type: 预期的令牌类型（如 "access" 或 "refresh"）

        Returns:
            令牌类型是否匹配
        """
        return payload.get("type") == expected_type
