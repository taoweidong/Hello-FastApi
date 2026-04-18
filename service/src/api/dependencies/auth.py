"""认证依赖项：当前用户、权限检查。"""

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.domain_services import get_token_service
from src.domain.entities.menu import MenuEntity
from src.domain.exceptions import ForbiddenError, UnauthorizedError
from src.domain.services.token_service import TokenService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository

security_scheme = HTTPBearer()


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security_scheme), token_service: TokenService = Depends(get_token_service)) -> str:
    """从 JWT 令牌中提取并验证当前用户 ID。"""
    token = credentials.credentials
    payload = token_service.decode_token(token)
    if payload is None:
        raise UnauthorizedError("无效或已过期的令牌")

    if not TokenService.verify_token_type(payload, "access"):
        raise UnauthorizedError("无效的令牌类型")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("无效的令牌负载")
    return str(user_id)


async def get_current_active_user(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)) -> dict:
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

    async def permission_checker(current_user: dict = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> dict:
        if current_user["is_superuser"]:
            return current_user

        role_repo = RoleRepository(db)
        user_roles = await role_repo.get_user_roles(current_user["id"])

        for role in user_roles:
            menus = await role_repo.get_role_menus(role.id)
            for menu in menus:
                if menu.menu_type == MenuEntity.PERMISSION and menu.name == code:
                    return current_user

        raise ForbiddenError(f"权限 '{code}' 是必需的")

    return permission_checker


def require_menu_permission(path: str, method: str):
    """依赖工厂：要求特定API路径和方法的菜单权限。

    基于Menu.path和Menu.method检查API级权限。
    """

    async def permission_checker(current_user: dict = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> dict:
        if current_user["is_superuser"]:
            return current_user

        role_repo = RoleRepository(db)
        user_roles = await role_repo.get_user_roles(current_user["id"])

        for role in user_roles:
            menus = await role_repo.get_role_menus(role.id)
            for menu in menus:
                if menu.menu_type == MenuEntity.PERMISSION and menu.path == path and menu.method == method:
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
