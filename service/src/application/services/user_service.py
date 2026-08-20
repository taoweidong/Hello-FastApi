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
from src.domain.enums import DataScope, SystemRole, UserRole, UserStatus
from src.domain.error_messages import ErrorMessages as EM
from src.domain.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from src.domain.repositories.department_repository import DepartmentRepositoryInterface
from src.domain.repositories.post_repository import PostRepositoryInterface
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
        dept_repo: DepartmentRepositoryInterface | None = None,
        post_repo: PostRepositoryInterface | None = None,
    ):
        self.repo = repo
        self.password_service = password_service
        self.role_repo = role_repo
        self.cache_service = cache_service
        self.dept_repo = dept_repo
        self.post_repo = post_repo

    async def create_user(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建新用户。"""
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(EM.username_exists(dto.username))
        if dto.email and await self.repo.get_by_email(dto.email):
            raise ConflictError(EM.email_exists(dto.email))

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
        # 岗位分配（postIds 传入时同步写入关联）
        if dto.postIds is not None and self.post_repo is not None:
            await self.post_repo.assign_posts_to_user(created_user.id, dto.postIds)
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

    async def get_users(
        self, query: UserListQueryDTO, operator_id: str | None = None
    ) -> tuple[list[UserResponseDTO], int]:
        """获取用户列表（支持筛选、分页和数据权限过滤），批量获取角色消除 N+1。

        Args:
            query: 列表查询条件
            operator_id: 当前操作人用户ID，用于数据权限范围过滤（None 表示不过滤）
        """
        dept_id = query.deptId
        if dept_id == "" or dept_id == "0":
            dept_id = None

        # 解析操作人的数据权限范围
        scope_dept_ids, scope_user_id = await self._resolve_data_scope(operator_id)

        users = await self.repo.get_all(
            page_num=query.pageNum,
            page_size=query.pageSize,
            username=query.username,
            phone=query.phone,
            email=query.email,
            is_active=query.isActive,
            dept_id=dept_id,
            scope_dept_ids=scope_dept_ids,
            scope_user_id=scope_user_id,
        )

        total = await self.repo.count(
            username=query.username,
            phone=query.phone,
            email=query.email,
            is_active=query.isActive,
            dept_id=dept_id,
            scope_dept_ids=scope_dept_ids,
            scope_user_id=scope_user_id,
        )

        # 批量获取所有用户的角色
        user_ids = [u.id for u in users]
        roles_map = await self.role_repo.get_users_roles_batch(user_ids)

        user_responses = [UserMapper.to_response_with_roles(u, roles_map.get(u.id, [])) for u in users]
        return user_responses, total

    async def _resolve_data_scope(self, operator_id: str | None) -> tuple[list[str] | None, str | None]:
        """解析操作人的数据权限范围。

        Returns:
            (scope_dept_ids, scope_user_id) 元组：
            - (None, None) 表示不限制（超级管理员或全部数据权限）
            - (部门ID列表, None) 表示限定部门范围（空列表表示无可见数据）
            - (None, 用户ID) 表示仅本人可见
        """
        if operator_id is None:
            return None, None

        operator = await self.repo.get_by_id(operator_id)
        if operator is None or operator.is_superuser_user:
            return None, None

        scope = await self.role_repo.get_user_data_scope(operator_id)
        if scope == DataScope.ALL:
            return None, None
        if scope == DataScope.SELF:
            return None, operator_id
        if scope == DataScope.DEPT:
            if not operator.dept_id:
                return [], None
            return [operator.dept_id], None
        if scope == DataScope.DEPT_AND_CHILD:
            if not operator.dept_id:
                return [], None
            child_ids = await self.dept_repo.get_child_dept_ids(operator.dept_id) if self.dept_repo else []
            return [operator.dept_id, *child_ids], None
        if scope == DataScope.CUSTOM:
            return await self.role_repo.get_user_custom_dept_ids(operator_id), None
        return None, None

    async def update_user(self, user_id: str, dto: UserUpdateDTO) -> UserResponseDTO:
        """更新用户信息。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(EM.user_not_found_by_id(user_id))

        if dto.email is not None:
            existing = await self.repo.get_by_email(dto.email)
            if existing and existing.id != user_id:
                raise ConflictError(EM.email_exists(dto.email))

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
        # 岗位分配（postIds 传入时同步更新关联，空列表表示清空）
        if dto.postIds is not None and self.post_repo is not None:
            await self.post_repo.assign_posts_to_user(updated_user.id, dto.postIds)
        await self._invalidate_user_cache(user_id)
        user_roles = await self.role_repo.get_user_roles(updated_user.id)
        return UserMapper.to_response(updated_user, user_roles)

    async def update_own_profile(self, user_id: str, dto: UserUpdateDTO) -> UserResponseDTO:
        """更新当前用户个人资料（仅允许档案字段，不含状态/职员/权限模式等管理字段）。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(EM.user_not_found_by_id(user_id))

        if dto.email is not None:
            existing = await self.repo.get_by_email(dto.email)
            if existing and existing.id != user_id:
                raise ConflictError(EM.email_exists(dto.email))

        user.update_profile(
            email=dto.email,
            nickname=dto.nickname,
            first_name=dto.firstName,
            last_name=dto.lastName,
            phone=dto.phone,
            gender=dto.gender,
            description=dto.description,
        )
        updated_user = await self.repo.update(user)
        await self._invalidate_user_cache(user_id)
        user_roles = await self.role_repo.get_user_roles(updated_user.id)
        return UserMapper.to_response(updated_user, user_roles)

    async def update_avatar(self, user_id: str, avatar: str) -> str:
        """更新用户头像 URL 并返回新地址。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(EM.user_not_found_by_id(user_id))

        user.update_profile(avatar=avatar)
        await self.repo.update(user)
        await self._invalidate_user_cache(user_id)
        return avatar

    async def delete_user(self, user_id: str) -> bool:
        """删除用户。"""
        if not await self.repo.delete(user_id):
            raise NotFoundError(EM.user_not_found_by_id(user_id))
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
            raise NotFoundError(EM.user_not_found_by_id(user_id))

        user.change_password(self.password_service.hash_password(new_password))
        await self.repo.update(user)
        await self._invalidate_user_cache(user_id)
        return True

    async def update_status(self, user_id: str, is_active: int) -> bool:
        """更改用户状态（通过领域实体的 activate/deactivate 方法）。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(EM.user_not_found_by_id(user_id))

        if is_active == UserStatus.ACTIVE:
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
            raise NotFoundError(EM.user_not_found_by_id(user_id))

        if not self.password_service.verify_password(dto.oldPassword, user.password):
            raise UnauthorizedError(EM.INCORRECT_OLD_PASSWORD)

        user.change_password(self.password_service.hash_password(dto.newPassword))
        await self.repo.update(user)
        await self._invalidate_user_cache(user_id)
        return True

    async def create_superuser(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建超级用户，自动分配 admin 角色（拥有所有菜单权限）。"""
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(EM.username_exists(dto.username))
        if dto.email and await self.repo.get_by_email(dto.email):
            raise ConflictError(EM.email_exists(dto.email))

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

        admin_role = await self.role_repo.get_by_name(SystemRole.ADMIN)
        if admin_role:
            await self.role_repo.assign_role_to_user(created_user.id, admin_role.id)

        user_roles = await self.role_repo.get_user_roles(created_user.id)
        return UserMapper.to_response(created_user, user_roles)

    async def assign_roles(self, user_id: str, role_ids: list[str]) -> bool:
        """为用户分配角色。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(EM.user_not_found_by_id(user_id))
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
                    raise UnauthorizedError(EM.USER_ACCOUNT_DISABLED)
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

        复用了原 api/dependencies/auth.py 中 require_permission 的逻辑。
        """
        if is_superuser == UserRole.SUPERUSER:
            return UserEntity(id=user_id, username="", password="", is_superuser=UserRole.SUPERUSER)

        if self.cache_service is not None:
            cached_perms = await self.cache_service.get_user_permissions(user_id)
            if cached_perms is not None:
                for perm in cached_perms:
                    if perm.get("type") == "permission" and perm.get("name") == code:
                        return UserEntity(id=user_id, username="", password="", is_superuser=UserRole.USER)
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
            return UserEntity(id=user_id, username="", password="", is_superuser=UserRole.USER)

        raise ForbiddenError(f"权限 '{code}' 是必需的")

    async def check_api_permission_cached_or_db(
        self, user_id: str, is_superuser: UserRole, path: str, method: str
    ) -> UserEntity:
        """检查用户是否具有指定 API 路径权限（缓存优先）。

        复用了原 api/dependencies/auth.py 中 require_menu_permission 的逻辑。
        """
        if is_superuser == UserRole.SUPERUSER:
            return UserEntity(id=user_id, username="", password="", is_superuser=UserRole.SUPERUSER)

        if self.cache_service is not None:
            cached_perms = await self.cache_service.get_user_permissions(user_id)
            if cached_perms is not None:
                for perm in cached_perms:
                    if perm.get("type") == "api" and perm.get("path") == path and perm.get("method") == method:
                        return UserEntity(id=user_id, username="", password="", is_superuser=UserRole.USER)
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
            return UserEntity(id=user_id, username="", password="", is_superuser=UserRole.USER)

        raise ForbiddenError(f"API权限 '{method} {path}' 是必需的")

    async def get_cached_or_active_user(self, user_id: str) -> UserEntity:
        """从缓存或数据库获取当前活跃用户实体，供 auth.py 依赖注入使用。"""
        return await self.get_user_info_with_cache(user_id)

    @staticmethod
    def _to_response_with_roles(user: UserEntity, roles: list) -> UserResponseDTO:
        """将用户实体和预加载的角色列表转换为响应 DTO（保持向后兼容）。"""
        return UserMapper.to_response_with_roles(user, roles)
