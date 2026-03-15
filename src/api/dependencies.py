"""API 路由的认证依赖项。"""

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ForbiddenError, UnauthorizedError
from src.domain.auth.token_service import TokenService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.rbac_repository import PermissionRepository
from src.infrastructure.repositories.user_repository import UserRepository

security_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> str:
    """从 JWT 令牌中提取并验证当前用户 ID。"""
    token = credentials.credentials
    payload = TokenService.decode_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")

    if not TokenService.verify_token_type(payload, "access"):
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")
    return user_id


async def get_current_active_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """从数据库获取当前活跃用户。"""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("User account is disabled")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_superuser": user.is_superuser,
    }


def require_permission(codename: str):
    """依赖工厂：要求特定权限。"""

    async def permission_checker(
        current_user: dict = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        if current_user["is_superuser"]:
            return current_user

        perm_repo = PermissionRepository(db)
        perms = await perm_repo.get_user_permissions(current_user["id"])
        if not any(p.codename == codename for p in perms):
            raise ForbiddenError(f"Permission '{codename}' required")
        return current_user

    return permission_checker


def require_superuser():
    """依赖项：要求超级用户角色。"""

    async def superuser_checker(
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        if not current_user["is_superuser"]:
            raise ForbiddenError("Superuser access required")
        return current_user

    return superuser_checker
