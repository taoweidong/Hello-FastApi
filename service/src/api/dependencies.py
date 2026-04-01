"""API 路由的依赖注入模块。

提供认证依赖项和服务工厂函数，实现依赖倒置原则。
所有服务通过工厂函数创建，路由层通过 Depends() 注入。
"""

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.auth_service import AuthService
from src.application.services.department_service import DepartmentService
from src.application.services.log_service import LogService
from src.application.services.menu_service import MenuService
from src.application.services.rbac_service import RBACService
from src.application.services.user_service import UserService
from src.config.settings import get_settings
from src.core.exceptions import ForbiddenError, UnauthorizedError
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.department_repository import DepartmentRepository
from src.infrastructure.repositories.log_repository import LogRepository
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.rbac_repository import PermissionRepository, RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository

security_scheme = HTTPBearer()


# =============================================================================
# 领域服务工厂
# =============================================================================


def get_password_service() -> PasswordService:
    """获取密码服务实例。"""
    return PasswordService()


def get_token_service() -> TokenService:
    """获取令牌服务实例。

    从配置中读取 JWT 参数并创建令牌服务。
    """
    settings = get_settings()
    return TokenService(secret_key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM, access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES, refresh_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


# =============================================================================
# 认证依赖项
# =============================================================================


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
    if not user.is_active:
        raise UnauthorizedError("用户账号已被禁用")
    return {"id": user.id, "username": user.username, "email": user.email, "is_superuser": user.is_superuser}


def require_permission(code: str):
    """依赖工厂：要求特定权限。"""

    async def permission_checker(current_user: dict = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> dict:
        if current_user["is_superuser"]:
            return current_user

        perm_repo = PermissionRepository(db)
        perms = await perm_repo.get_user_permissions(current_user["id"])
        if not any(p.code == code for p in perms):
            raise ForbiddenError(f"权限 '{code}' 是必需的")
        return current_user

    return permission_checker


def require_superuser():
    """依赖项：要求超级用户角色。"""

    async def superuser_checker(current_user: dict = Depends(get_current_active_user)) -> dict:
        if not current_user["is_superuser"]:
            raise ForbiddenError("需要超级用户权限")
        return current_user

    return superuser_checker


# =============================================================================
# 应用服务工厂
# =============================================================================


async def get_auth_service(db: AsyncSession = Depends(get_db), token_service: TokenService = Depends(get_token_service), password_service: PasswordService = Depends(get_password_service)) -> AuthService:
    """获取认证服务实例。

    注入所有必需的仓储和领域服务依赖。
    """
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    perm_repo = PermissionRepository(db)
    return AuthService(session=db, user_repo=user_repo, role_repo=role_repo, perm_repo=perm_repo, token_service=token_service, password_service=password_service)


async def get_user_service(db: AsyncSession = Depends(get_db), password_service: PasswordService = Depends(get_password_service)) -> UserService:
    """获取用户服务实例。

    注入用户仓储、角色仓储和密码服务依赖。
    """
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    return UserService(session=db, repo=user_repo, password_service=password_service, role_repo=role_repo)


async def get_menu_service(db: AsyncSession = Depends(get_db)) -> MenuService:
    """获取菜单服务实例。

    注入菜单仓储和权限仓储依赖。
    """
    menu_repo = MenuRepository()
    perm_repo = PermissionRepository(db)
    return MenuService(session=db, menu_repo=menu_repo, perm_repo=perm_repo)


async def get_rbac_service(db: AsyncSession = Depends(get_db)) -> RBACService:
    """获取 RBAC 服务实例。

    注入角色仓储和权限仓储依赖。
    """
    role_repo = RoleRepository(db)
    perm_repo = PermissionRepository(db)
    return RBACService(session=db, role_repo=role_repo, perm_repo=perm_repo)


async def get_department_service(db: AsyncSession = Depends(get_db)) -> DepartmentService:
    """获取部门服务实例。

    注入部门仓储依赖。
    """
    dept_repo = DepartmentRepository()
    return DepartmentService(session=db, dept_repo=dept_repo)


async def get_log_service(db: AsyncSession = Depends(get_db)) -> LogService:
    """获取日志服务实例。

    注入日志仓储依赖。
    """
    log_repo = LogRepository()
    return LogService(session=db, log_repo=log_repo)


# =============================================================================
# 仓储工厂（供路由层直接使用仓储时调用）
# =============================================================================


def get_menu_repository() -> MenuRepository:
    """获取菜单仓储实例。"""
    return MenuRepository()


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """获取用户仓储实例。"""
    return UserRepository(db)


async def get_role_repository(db: AsyncSession = Depends(get_db)) -> RoleRepository:
    """获取角色仓储实例。"""
    return RoleRepository(db)
