"""认证应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.domain_services import get_password_service, get_token_service
from src.application.services.auth_service import AuthService
from src.domain.services.cache_port import CachePort
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository


async def get_auth_service(db: AsyncSession = Depends(get_db), token_service: TokenService = Depends(get_token_service), password_service: PasswordService = Depends(get_password_service), cache_service: CachePort = Depends(get_cache_service)) -> AuthService:
    """获取认证服务实例。

    注入所有必需的仓储、领域服务和缓存服务依赖。
    """
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    menu_repo = MenuRepository(db)
    return AuthService(user_repo=user_repo, role_repo=role_repo, menu_repo=menu_repo, token_service=token_service, password_service=password_service, cache_service=cache_service)
