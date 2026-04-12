"""应用层 - 用户服务。"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.user_dto import ChangePasswordDTO, UserCreateDTO, UserListQueryDTO, UserResponseDTO, UserUpdateDTO
from src.domain.exceptions import ConflictError, NotFoundError, UnauthorizedError
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.password_service import PasswordService
from src.infrastructure.database.models import User


class UserService:
    """用户领域操作的应用服务。"""

    def __init__(self, session: AsyncSession, repo: UserRepositoryInterface, password_service: PasswordService, role_repo: RoleRepositoryInterface):
        self.session = session
        self.repo = repo
        self.password_service = password_service
        self.role_repo = role_repo

    async def create_user(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建新用户。"""
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(f"用户名 '{dto.username}' 已存在")
        if dto.email and await self.repo.get_by_email(dto.email):
            raise ConflictError(f"邮箱 '{dto.email}' 已存在")

        user = User(
            username=dto.username,
            email=dto.email or "",
            password=self.password_service.hash_password(dto.password),
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
        await self.repo.create(user)
        await self.session.flush()
        created_user = await self.repo.get_by_id(user.id)
        if created_user is None:
            raise NotFoundError("用户创建后无法加载")
        return await self._to_response(created_user)

    async def get_user(self, user_id: str) -> UserResponseDTO:
        """根据 ID 获取用户。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        return await self._to_response(user)

    async def get_user_by_username(self, username: str) -> User | None:
        """根据用户名获取用户实体。"""
        return await self.repo.get_by_username(username)

    async def get_users(self, query: UserListQueryDTO) -> tuple[list[UserResponseDTO], int]:
        """获取用户列表（支持筛选和分页）。"""
        dept_id = query.deptId
        if dept_id == "" or dept_id == "0":
            dept_id = None

        users = await self.repo.get_all(page_num=query.pageNum, page_size=query.pageSize, username=query.username, phone=query.phone, email=query.email, is_active=query.isActive, dept_id=dept_id)

        total = await self.repo.count(username=query.username, phone=query.phone, email=query.email, is_active=query.isActive, dept_id=dept_id)

        user_responses = [await self._to_response(u) for u in users]
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
            user.email = dto.email
        if dto.nickname is not None:
            user.nickname = dto.nickname
        if dto.firstName is not None:
            user.first_name = dto.firstName
        if dto.lastName is not None:
            user.last_name = dto.lastName
        if dto.phone is not None:
            user.phone = dto.phone
        if dto.gender is not None:
            user.gender = dto.gender
        if dto.avatar is not None:
            user.avatar = dto.avatar
        if dto.isActive is not None:
            user.is_active = dto.isActive
        if dto.isStaff is not None:
            user.is_staff = dto.isStaff
        if dto.modeType is not None:
            user.mode_type = dto.modeType
        if dto.dept_id is not None:
            user.dept_id = dto.dept_id
        if dto.description is not None:
            user.description = dto.description

        user = await self.repo.update(user)
        await self.session.flush()
        updated_user = await self.repo.get_by_id(user_id)
        if updated_user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        return await self._to_response(updated_user)

    async def delete_user(self, user_id: str) -> bool:
        """删除用户。"""
        if not await self.repo.delete(user_id):
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        return True

    async def batch_delete_users(self, user_ids: list[str]) -> dict:
        """批量删除用户。"""
        deleted_count = await self.repo.batch_delete(user_ids)
        return {"deleted_count": deleted_count, "total_requested": len(user_ids)}

    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """管理员重置用户密码。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        hashed_password = self.password_service.hash_password(new_password)
        await self.repo.reset_password(user_id, hashed_password)
        return True

    async def update_status(self, user_id: str, is_active: int) -> bool:
        """更改用户状态。"""
        if not await self.repo.update_status(user_id, is_active):
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        return True

    async def change_password(self, user_id: str, dto: ChangePasswordDTO) -> bool:
        """修改用户密码。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        if not self.password_service.verify_password(dto.oldPassword, user.password):
            raise UnauthorizedError("旧密码不正确")

        user.password = self.password_service.hash_password(dto.newPassword)
        await self.repo.update(user)
        return True

    async def create_superuser(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建超级用户，自动分配 admin 角色（拥有所有菜单权限）。"""
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(f"用户名 '{dto.username}' 已存在")
        if dto.email and await self.repo.get_by_email(dto.email):
            raise ConflictError(f"邮箱 '{dto.email}' 已存在")

        user = User(
            username=dto.username,
            email=dto.email or "",
            password=self.password_service.hash_password(dto.password),
            nickname=dto.nickname or "",
            first_name=dto.firstName or "",
            last_name=dto.lastName or "",
            phone=dto.phone or "",
            gender=dto.gender if dto.gender is not None else 0,
            avatar=dto.avatar,
            is_active=dto.isActive if dto.isActive is not None else 1,
            is_staff=1,
            is_superuser=1,
            mode_type=dto.modeType if dto.modeType is not None else 0,
            dept_id=dto.dept_id,
            description=dto.description,
        )
        await self.repo.create(user)
        await self.session.flush()

        # 自动分配 admin 角色，确保拥有所有菜单权限
        admin_role = await self.role_repo.get_by_name("admin")
        if admin_role:
            await self.role_repo.assign_role_to_user(user.id, admin_role.id)

        created = await self.repo.get_by_id(user.id)
        if created is None:
            raise NotFoundError("超级用户创建后无法加载")
        return await self._to_response(created)

    async def assign_roles(self, user_id: str, role_ids: list[str]) -> bool:
        """为用户分配角色。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        await self.role_repo.assign_roles_to_user(user_id, role_ids)
        return True

    async def _to_response(self, user: User) -> UserResponseDTO:
        """将用户实体转换为响应 DTO。"""
        # 构建角色列表
        roles: list[dict] = []
        if user.roles:
            for ur in user.roles:
                if ur.role:
                    roles.append({"id": ur.role.id, "name": ur.role.name})

        return UserResponseDTO(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            firstName=user.first_name,
            lastName=user.last_name,
            avatar=user.avatar,
            email=user.email,
            phone=user.phone,
            gender=user.gender,
            isActive=user.is_active,
            isStaff=user.is_staff,
            modeType=user.mode_type,
            roles=roles,
            creatorId=user.creator_id,
            modifierId=user.modifier_id,
            createdTime=user.created_time,
            updatedTime=user.updated_time,
            description=user.description,
        )
