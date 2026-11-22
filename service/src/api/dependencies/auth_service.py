"""认证应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service, get_online_session_store
from src.api.dependencies.domain_services import get_password_service, get_token_service
from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.auth_service import AuthService
from src.domain.services.cache_port import MenuCachePort, TokenRevocationPort, UserCachePort
from src.domain.services.online_session_port import OnlineSessionStore
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService


async def get_auth_service(
    repos: RepoBundle = Depends(get_repositories),
    token_service: TokenService = Depends(get_token_service),
    password_service: PasswordService = Depends(get_password_service),
    token_revocation: TokenRevocationPort = Depends(get_cache_service),
    session_store: OnlineSessionStore = Depends(get_online_session_store),
    menu_cache: MenuCachePort = Depends(get_cache_service),
    user_cache: UserCachePort = Depends(get_cache_service),
) -> AuthService:
    """获取认证服务实例。

    注入所有必需的仓储与领域服务；缓存侧按用途拆成四个窄端口：
    令牌吊销（刷新/登出）、在线会话登记（登录）、菜单全表缓存（超管动态路由）、
    用户路由树缓存（动态路由读写穿透）。
    """
    return AuthService(
        user_repo=repos.user,
        role_repo=repos.role,
        menu_repo=repos.menu,
        token_service=token_service,
        password_service=password_service,
        token_revocation=token_revocation,
        session_store=session_store,
        menu_cache=menu_cache,
        log_repo=repos.log,
        user_cache=user_cache,
    )
