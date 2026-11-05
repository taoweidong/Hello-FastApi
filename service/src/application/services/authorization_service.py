"""应用层 - 授权服务。

从 UserService 拆出的"谁能访问什么"领域：每请求热路径的权限校验
（缓存优先）与当前用户解析。与用户管理 CRUD（UserService）按变更轴分离——
改权限模型不再碰用户档案代码，反之亦然。
"""

from collections.abc import Callable
from typing import Any

from src.domain.entities.menu import MenuEntity
from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole, UserStatus
from src.domain.error_messages import ErrorMessages as EM
from src.domain.exceptions import ForbiddenError, UnauthorizedError
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.cache_port import CachePort


class AuthorizationService:
    """授权校验与当前用户解析（缓存优先）。"""

    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        role_repo: RoleRepositoryInterface,
        cache_service: CachePort | None = None,
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.cache_service = cache_service

    async def get_user_info_with_cache(self, user_id: str) -> UserEntity:
        """从缓存或数据库获取当前活跃用户实体，供 auth.py 依赖注入使用。"""
        if self.cache_service is not None:
            cached_info = await self.cache_service.get_user_info(user_id)
            if cached_info is not None:
                if not cached_info.get("is_active", 0):
                    raise UnauthorizedError(EM.USER_ACCOUNT_DISABLED)
                return UserEntity(
                    id=str(cached_info["id"]),
                    username=cached_info.get("username", ""),
                    password="",
                    is_superuser=cached_info.get("is_superuser", UserRole.USER),
                    is_active=cached_info.get("is_active", UserStatus.ACTIVE),
                    email=cached_info.get("email", ""),
                )

        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError(EM.USER_NOT_FOUND)
        if not user.is_active_user:
            raise UnauthorizedError(EM.USER_ACCOUNT_DISABLED)

        user_info: dict[str, Any] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
        }
        if self.cache_service is not None:
            await self.cache_service.set_user_info(user_id, user_info)
        return user

    async def check_permission_cached_or_db(self, user_id: str, is_superuser: UserRole, code: str) -> UserEntity:
        """检查用户是否具有指定权限（缓存优先）。

        Args:
            user_id: 用户 ID
            is_superuser: 用户角色（超级用户直接放行）
            code: 按钮级权限码（对应 PERMISSION 菜单的 name）

        Returns:
            通过校验的用户实体

        Raises:
            ForbiddenError: 缓存与数据库均未匹配到所需权限时抛出。
        """
        return await self._check_permission_cached_or_db(
            user_id,
            is_superuser,
            required_label=f"权限 '{code}'",
            entry_builder=lambda menu: {"type": "permission", "name": menu.name},
            entry_matcher=lambda perm: perm.get("type") == "permission" and perm.get("name") == code,
        )

    async def check_api_permission_cached_or_db(
        self, user_id: str, is_superuser: UserRole, path: str, method: str
    ) -> UserEntity:
        """检查用户是否具有指定 API 路径权限（缓存优先）。

        Args:
            user_id: 用户 ID
            is_superuser: 用户角色（超级用户直接放行）
            path: API 路径
            method: HTTP 方法

        Returns:
            通过校验的用户实体

        Raises:
            ForbiddenError: 缓存与数据库均未匹配到所需权限时抛出。
        """
        return await self._check_permission_cached_or_db(
            user_id,
            is_superuser,
            required_label=f"API权限 '{method} {path}'",
            entry_builder=self._build_menu_perm_entry,
            entry_matcher=lambda perm: (
                perm.get("type") == "api" and perm.get("path") == path and perm.get("method") == method
            ),
        )

    @staticmethod
    def _build_menu_perm_entry(menu: MenuEntity) -> dict[str, Any]:
        """将权限型菜单转换为可缓存的权限条目。

        同时配置了 path 和 method 的菜单生成 API 级条目，
        否则退化为按钮级权限条目。
        """
        if menu.path and menu.method:
            return {"type": "api", "path": menu.path, "method": menu.method, "name": menu.name}
        return {"type": "permission", "name": menu.name}

    async def _check_permission_cached_or_db(
        self,
        user_id: str,
        is_superuser: UserRole,
        *,
        required_label: str,
        entry_builder: Callable[[MenuEntity], dict[str, Any]],
        entry_matcher: Callable[[dict[str, Any]], bool],
    ) -> UserEntity:
        """权限校验统一核心：缓存优先，未命中回源数据库并回填缓存。

        Args:
            user_id: 用户 ID
            is_superuser: 用户角色（超级用户直接放行）
            required_label: 拒绝时提示的权限描述
            entry_builder: 菜单实体 -> 权限条目的转换函数
            entry_matcher: 权限条目 -> 是否满足本次校验的判定函数

        Returns:
            通过校验的用户实体（轻量构造，不含完整档案）

        Raises:
            ForbiddenError: 缓存与数据库均未匹配到所需权限时抛出。
        """
        if is_superuser == UserRole.SUPERUSER:
            return UserEntity(id=user_id, username="", password="", is_superuser=UserRole.SUPERUSER)

        if self.cache_service is not None:
            cached_perms = await self.cache_service.get_user_permissions(user_id)
            if cached_perms is not None:
                if not any(entry_matcher(perm) for perm in cached_perms):
                    raise ForbiddenError(EM.permission_required(required_label))
                return UserEntity(id=user_id, username="", password="", is_superuser=UserRole.USER)

        user_menus = await self.role_repo.get_user_all_menus(user_id)
        all_perms = [entry_builder(menu) for menu in user_menus if menu.menu_type == MenuEntity.PERMISSION]
        has_permission = any(entry_matcher(entry) for entry in all_perms)

        if self.cache_service is not None:
            await self.cache_service.set_user_permissions(user_id, all_perms)

        if has_permission:
            return UserEntity(id=user_id, username="", password="", is_superuser=UserRole.USER)

        raise ForbiddenError(EM.permission_required(required_label))
