"""认证依赖项：当前用户、权限检查。"""

from collections.abc import Awaitable, Callable

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.domain_services import get_token_service
from src.api.dependencies.user_service import get_user_service
from src.application.services.user_service import UserService
from src.domain.entities.user import UserEntity
from src.domain.exceptions import ForbiddenError, UnauthorizedError
from src.domain.services.token_service import TokenService
from src.infrastructure.cache.cache_service import CacheService

security_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    token_service: TokenService = Depends(get_token_service),
    cache_service: CacheService = Depends(get_cache_service),
) -> str:
    """从 JWT 令牌中提取并验证当前用户 ID。"""
    token = credentials.credentials
    payload = token_service.decode_token(token)
    if payload is None:
        raise UnauthorizedError("无效或已过期的令牌")

    if not TokenService.verify_token_type(payload, "access"):
        raise UnauthorizedError("无效的令牌类型")

    # 检查 Token 黑名单
    if await cache_service.is_token_blacklisted(token):
        raise UnauthorizedError("令牌已失效")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("无效的令牌负载")
    return str(user_id)


async def get_current_active_user(
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
) -> UserEntity:
    """从缓存或数据库获取当前活跃用户实体。"""
    return await user_service.get_user_info_with_cache(user_id)


def require_permission(code: str) -> Callable[..., Awaitable[UserEntity]]:
    """依赖工厂：要求特定菜单权限（基于menu.name检查按钮权限）。

    新RBAC方案：权限不再使用独立Permission表，而是通过Menu的menu_type=2(PERMISSION)
    和name字段来实现按钮级权限控制。code参数现在对应menu.name。
    """

    async def permission_checker(
        current_user: UserEntity = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service),
    ) -> UserEntity:
        return await user_service.check_permission_cached_or_db(
            user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            code=code,
        )

    return permission_checker


def require_menu_permission(path: str, method: str) -> Callable[..., Awaitable[UserEntity]]:
    """依赖工厂：要求特定API路径和方法的菜单权限。

    基于Menu.path和Menu.method检查API级权限。
    """

    async def permission_checker(
        current_user: UserEntity = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service),
    ) -> UserEntity:
        return await user_service.check_api_permission_cached_or_db(
            user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            path=path,
            method=method,
        )

    return permission_checker


def require_superuser() -> Callable[..., Awaitable[UserEntity]]:
    """依赖项：要求超级用户角色。"""

    async def superuser_checker(current_user: UserEntity = Depends(get_current_active_user)) -> UserEntity:
        if not current_user.is_superuser_user:
            raise ForbiddenError("需要超级用户权限")
        return current_user

    return superuser_checker
