"""应用层 - 用户服务。"""

from typing import Any

from src.application.dto.user_dto import (
    ChangePasswordDTO,
    UserCreateDTO,
    UserListQueryDTO,
    UserResponseDTO,
    UserUpdateDTO,
)
from src.application.mappers.user_mapper import UserMapper
from src.domain.entities.menu import MenuEntity
from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole, UserStatus
from src.domain.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.cache_port import CachePort
from src.domain.services.password_service import PasswordService


class UserService:
    """用户领域操作的应用服务。"""

    def __init__(
        self,
        repo: UserRepositoryInterface,
        password_service: PasswordService,
        role_repo: RoleRepositoryInterface,
        cache_service: CachePort | None = None,
    ):
        self.repo = repo
        self.password_service = password_service
        self.role_repo = role_repo
        self.cache_service = cache_service

    async def create_user(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建新用户。"""
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(f"用户名 '{dto.username}' 已存在")
        if dto.email and await self.repo.get_by_email(dto.email):
            raise ConflictError(f"邮箱 '{dto.email}' 已存在")

        user_entity = UserEntity.create_new(
            username=dto.username,
            hashed_password=self.password_service.hash_password(dto.password),
            email=dto.email or "",
            nickname=dto.nickname or "",
            first_name=dto.firstName or "",
            last_name=dto.lastName or "",
            phone=dto.phone or "",
            gender=dto.gender if dto.gender is not None else 0,
            avatar=dto.avatar,
            is_active=dto.isActive if dto.isActive is not None else 1,
            is_staff=dto.isStaff if dto.isStaff is not None else 0,
            mode_type=dto.modeType if dto.modeType is not None else 0,
            dept_id=dto.dept_id,
            description=dto.description,
        )
        created_user = await self.repo.create(user_entity)
        return UserMapper.to_response(created_user)

    async def get_user(self, user_id: str) -> UserResponseDTO:
        """根据 ID 获取用户。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        # 获取用户角色
        user_roles = await self.role_repo.get_user_roles(user.id)
        return UserMapper.to_response(user, user_roles)

    async def get_user_by_username(self, username: str) -> UserEntity | None:
        """根据用户名获取用户实体。"""
        return await self.repo.get_by_username(username)

    async def get_users(self, query: UserListQueryDTO) -> tuple[list[UserResponseDTO], int]:
        """获取用户列表（支持筛选和分页），批量获取角色消除 N+1。"""
        dept_id = query.deptId
        if dept_id == "" or dept_id == "0":
            dept_id = None

        users = await self.repo.get_all(
            page_num=query.pageNum,
            page_size=query.pageSize,
            username=query.username,
            phone=query.phone,
            email=query.email,
            is_active=query.isActive,
            dept_id=dept_id,
        )

        total = await self.repo.count(
            username=query.username, phone=query.phone, email=query.email, is_active=query.isActive, dept_id=dept_id
        )

        # 批量获取所有用户的角色
        user_ids = [u.id for u in users]
        roles_map = await self.role_repo.get_users_roles_batch(user_ids)

        user_responses = [UserMapper.to_response_with_roles(u, roles_map.get(u.id, [])) for u in users]
        return user_responses, total

    async def update_user(self, user_id: str, dto: UserUpdateDTO) -> UserResponseDTO:
        """更新用户信息。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        if dto.email is not None:
            existing = await self.repo.get_by_email(dto.email)
            if existing and existing.id != user_id:
                raise ConflictError(f"邮箱 '{dto.email}' 已存在")

        user.update_profile(
            email=dto.email,
            nickname=dto.nickname,
            first_name=dto.firstName,
            last_name=dto.lastName,
            phone=dto.phone,
            gender=dto.gender,
            avatar=dto.avatar,
            is_active=dto.isActive,
            is_staff=dto.isStaff,
            mode_type=dto.modeType,
            dept_id=dto.dept_id,
            description=dto.description,
        )
        updated_user = await self.repo.update(user)
        await self._invalidate_user_cache(user_id)
        user_roles = await self.role_repo.get_user_roles(updated_user.id)
        return UserMapper.to_response(updated_user, user_roles)

    async def delete_user(self, user_id: str) -> bool:
        """删除用户。"""
        if not await self.repo.delete(user_id):
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        await self._invalidate_user_cache(user_id)
        return True

    async def batch_delete_users(self, user_ids: list[str]) -> dict:
        """批量删除用户。"""
        deleted_count = await self.repo.batch_delete(user_ids)
        for uid in user_ids:
            await self._invalidate_user_cache(uid)
        return {"deleted_count": deleted_count, "total_requested": len(user_ids)}

    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """管理员重置用户密码。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        user.change_password(self.password_service.hash_password(new_password))
        await self.repo.update(user)
        await self._invalidate_user_cache(user_id)
        return True

    async def update_status(self, user_id: str, is_active: int) -> bool:
        """更改用户状态（通过领域实体的 activate/deactivate 方法）。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        if is_active == 1:
            user.activate()
        else:
            user.deactivate()
        await self.repo.update(user)
        await self._invalidate_user_cache(user_id)
        return True

    async def change_password(self, user_id: str, dto: ChangePasswordDTO) -> bool:
        """修改用户密码。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        if not self.password_service.verify_password(dto.oldPassword, user.password):
            raise UnauthorizedError("旧密码不正确")

        user.change_password(self.password_service.hash_password(dto.newPassword))
        await self.repo.update(user)
        await self._invalidate_user_cache(user_id)
        return True

    async def create_superuser(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建超级用户，自动分配 admin 角色（拥有所有菜单权限）。"""
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(f"用户名 '{dto.username}' 已存在")
        if dto.email and await self.repo.get_by_email(dto.email):
            raise ConflictError(f"邮箱 '{dto.email}' 已存在")

        user_entity = UserEntity.create_superuser_entity(
            username=dto.username,
            hashed_password=self.password_service.hash_password(dto.password),
            email=dto.email or "",
            nickname=dto.nickname or "",
            first_name=dto.firstName or "",
            last_name=dto.lastName or "",
            phone=dto.phone or "",
            gender=dto.gender if dto.gender is not None else 0,
            avatar=dto.avatar,
            mode_type=dto.modeType if dto.modeType is not None else 0,
            dept_id=dto.dept_id,
            description=dto.description,
        )

        # 创建用户和分配角色（事务由外部 session 管理）
        created_user = await self.repo.create(user_entity)

        admin_role = await self.role_repo.get_by_name("admin")
        if admin_role:
            await self.role_repo.assign_role_to_user(created_user.id, admin_role.id)

        user_roles = await self.role_repo.get_user_roles(created_user.id)
        return UserMapper.to_response(created_user, user_roles)

    async def assign_roles(self, user_id: str, role_ids: list[str]) -> bool:
        """为用户分配角色。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        await self.role_repo.assign_roles_to_user(user_id, role_ids)
        await self._invalidate_user_cache(user_id)
        return True

    async def _invalidate_user_cache(self, user_id: str) -> None:
        """使用户信息缓存和权限缓存失效。"""
        if self.cache_service is not None:
            await self.cache_service.invalidate_user_info(user_id)
            await self.cache_service.invalidate_user_permissions(user_id)

    async def get_user_by_id(self, user_id: str) -> UserEntity | None:
        """根据 ID 获取用户实体（不抛异常，返回 None）。"""
        return await self.repo.get_by_id(user_id)

    async def get_user_info_with_cache(self, user_id: str) -> UserEntity:
        """从缓存或数据库获取当前活跃用户实体，供 auth.py 依赖注入使用。

        复用了原 api/dependencies/auth.py 中 get_current_active_user 的逻辑。
        """
        if self.cache_service is not None:
            cached_info = await self.cache_service.get_user_info(user_id)
            if cached_info is not None:
                if not cached_info.get("is_active", 0):
                    raise UnauthorizedError("用户账号已被禁用")
                return UserEntity(
                    id=str(cached_info["id"]),
                    username=cached_info.get("username", ""),
                    password="",
                    is_superuser=cached_info.get("is_superuser", UserRole.USER),
                    is_active=cached_info.get("is_active", UserStatus.ACTIVE),
                    email=cached_info.get("email", ""),
                )

        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("用户不存在")
        if not user.is_active_user:
            raise UnauthorizedError("用户账号已被禁用")

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

    async def check_permission_cached_or_db(
        self, user_id: str, is_superuser: UserRole, code: str
    ) -> UserEntity:
        """检查用户是否具有指定权限（缓存优先）。

        复用了原 api/dependencies/auth.py 中 require_permission 的逻辑。
        """
        if is_superuser == UserRole.SUPERUSER:
            return UserEntity(
                id=user_id, username="", password="", is_superuser=UserRole.SUPERUSER
            )

        if self.cache_service is not None:
            cached_perms = await self.cache_service.get_user_permissions(user_id)
            if cached_perms is not None:
                for perm in cached_perms:
                    if perm.get("type") == "permission" and perm.get("name") == code:
                        return UserEntity(
                            id=user_id, username="", password="", is_superuser=UserRole.USER
                        )
                raise ForbiddenError(f"权限 '{code}' 是必需的")

        user_menus = await self.role_repo.get_user_all_menus(user_id)

        all_perms: list[dict[str, Any]] = []
        has_permission = False
        for menu in user_menus:
            if menu.menu_type == MenuEntity.PERMISSION:
                all_perms.append({"type": "permission", "name": menu.name})
                if menu.name == code:
                    has_permission = True

        if self.cache_service is not None:
            await self.cache_service.set_user_permissions(user_id, all_perms)

        if has_permission:
            return UserEntity(
                id=user_id, username="", password="", is_superuser=UserRole.USER
            )

        raise ForbiddenError(f"权限 '{code}' 是必需的")

    async def check_api_permission_cached_or_db(
        self, user_id: str, is_superuser: UserRole, path: str, method: str
    ) -> UserEntity:
        """检查用户是否具有指定 API 路径权限（缓存优先）。

        复用了原 api/dependencies/auth.py 中 require_menu_permission 的逻辑。
        """
        if is_superuser == UserRole.SUPERUSER:
            return UserEntity(
                id=user_id, username="", password="", is_superuser=UserRole.SUPERUSER
            )

        if self.cache_service is not None:
            cached_perms = await self.cache_service.get_user_permissions(user_id)
            if cached_perms is not None:
                for perm in cached_perms:
                    if perm.get("type") == "api" and perm.get("path") == path and perm.get("method") == method:
                        return UserEntity(
                            id=user_id, username="", password="", is_superuser=UserRole.USER
                        )
                raise ForbiddenError(f"API权限 '{method} {path}' 是必需的")

        user_menus = await self.role_repo.get_user_all_menus(user_id)

        all_perms: list[dict[str, Any]] = []
        has_permission = False
        for menu in user_menus:
            if menu.menu_type == MenuEntity.PERMISSION:
                perm_entry: dict[str, Any] = {"type": "permission", "name": menu.name}
                if menu.path and menu.method:
                    perm_entry = {"type": "api", "path": menu.path, "method": menu.method, "name": menu.name}
                    if menu.path == path and menu.method == method:
                        has_permission = True
                all_perms.append(perm_entry)

        if self.cache_service is not None:
            await self.cache_service.set_user_permissions(user_id, all_perms)

        if has_permission:
            return UserEntity(
                id=user_id, username="", password="", is_superuser=UserRole.USER
            )

        raise ForbiddenError(f"API权限 '{method} {path}' 是必需的")

    async def get_cached_or_active_user(self, user_id: str) -> UserEntity:
        """从缓存或数据库获取当前活跃用户实体，供 auth.py 依赖注入使用。"""
        return await self.get_user_info_with_cache(user_id)

    @staticmethod
    def _to_response_with_roles(user: UserEntity, roles: list) -> UserResponseDTO:
        """将用户实体和预加载的角色列表转换为响应 DTO（保持向后兼容）。"""
        return UserMapper.to_response_with_roles(user, roles)
