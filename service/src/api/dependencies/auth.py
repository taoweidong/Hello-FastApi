"""认证依赖项：当前用户、权限检查。"""

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.domain_services import get_token_service
from src.domain.entities.menu import MenuEntity
from src.domain.exceptions import ForbiddenError, UnauthorizedError
from src.domain.services.token_service import TokenService
from src.infrastructure.cache.cache_service import CacheService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository

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


async def get_current_active_user(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db), cache_service: CacheService = Depends(get_cache_service)) -> dict:
    """从数据库获取当前活跃用户。"""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("用户不存在")
    if not user.is_active_user:
        raise UnauthorizedError("用户账号已被禁用")
    return {"id": user.id, "username": user.username, "email": user.email, "is_superuser": user.is_superuser}


def require_permission(code: str):
    """依赖工厂：要求特定菜单权限（基于menu.name检查按钮权限）。

    新RBAC方案：权限不再使用独立Permission表，而是通过Menu的menu_type=2(PERMISSION)
    和name字段来实现按钮级权限控制。code参数现在对应menu.name。
    """

    async def permission_checker(current_user: dict = Depends(get_current_active_user), db: AsyncSession = Depends(get_db), cache_service: CacheService = Depends(get_cache_service)) -> dict:
        if current_user["is_superuser"]:
            return current_user

        # 尝试从缓存获取权限
        cached_perms = await cache_service.get_user_permissions(current_user["id"])
        if cached_perms is not None:
            # 缓存命中：检查权限
            for perm in cached_perms:
                if perm.get("type") == "permission" and perm.get("name") == code:
                    return current_user
            raise ForbiddenError(f"权限 '{code}' 是必需的")

        # 缓存未命中：一次查询获取用户所有菜单，消除 N+1
        role_repo = RoleRepository(db)
        user_menus = await role_repo.get_user_all_menus(current_user["id"])

        # 构建权限列表并写入缓存
        all_perms = []
        has_permission = False
        for menu in user_menus:
            if menu.menu_type == MenuEntity.PERMISSION:
                all_perms.append({"type": "permission", "name": menu.name})
                if menu.name == code:
                    has_permission = True

        # 写入缓存
        await cache_service.set_user_permissions(current_user["id"], all_perms)

        if has_permission:
            return current_user

        raise ForbiddenError(f"权限 '{code}' 是必需的")

    return permission_checker


def require_menu_permission(path: str, method: str):
    """依赖工厂：要求特定API路径和方法的菜单权限。

    基于Menu.path和Menu.method检查API级权限。
    """

    async def permission_checker(current_user: dict = Depends(get_current_active_user), db: AsyncSession = Depends(get_db), cache_service: CacheService = Depends(get_cache_service)) -> dict:
        if current_user["is_superuser"]:
            return current_user

        # 尝试从缓存获取权限
        cached_perms = await cache_service.get_user_permissions(current_user["id"])
        if cached_perms is not None:
            for perm in cached_perms:
                if perm.get("type") == "api" and perm.get("path") == path and perm.get("method") == method:
                    return current_user
            raise ForbiddenError(f"API权限 '{method} {path}' 是必需的")

        # 缓存未命中：一次查询获取用户所有菜单，消除 N+1
        role_repo = RoleRepository(db)
        user_menus = await role_repo.get_user_all_menus(current_user["id"])

        all_perms = []
        has_permission = False
        for menu in user_menus:
            if menu.menu_type == MenuEntity.PERMISSION:
                perm_entry = {"type": "permission", "name": menu.name}
                if menu.path and menu.method:
                    perm_entry = {"type": "api", "path": menu.path, "method": menu.method, "name": menu.name}
                    if menu.path == path and menu.method == method:
                        has_permission = True
                all_perms.append(perm_entry)

        await cache_service.set_user_permissions(current_user["id"], all_perms)

        if has_permission:
            return current_user

        raise ForbiddenError(f"API权限 '{method} {path}' 是必需的")

    return permission_checker


def require_superuser():
    """依赖项：要求超级用户角色。"""

    async def superuser_checker(current_user: dict = Depends(get_current_active_user)) -> dict:
        if not current_user["is_superuser"]:
            raise ForbiddenError("需要超级用户权限")
        return current_user

    return superuser_checker
