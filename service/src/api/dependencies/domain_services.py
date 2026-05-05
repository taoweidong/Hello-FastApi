"""领域服务工厂：密码服务和令牌服务。"""

from src.config.settings import get_settings
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService


def get_password_service() -> PasswordService:
    """获取密码服务实例。"""
    return PasswordService()


def get_token_service() -> TokenService:
    """获取令牌服务实例。

    从配置中读取 JWT 参数并创建令牌服务。
    """
    settings = get_settings()
    return TokenService(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
