"""应用层 - 用户服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.user_dto import (
    ChangePasswordDTO,
    UserCreateDTO,
    UserResponseDTO,
    UserUpdateDTO,
)
from src.application.interfaces.base_service import BaseService
from src.core.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)
from src.domain.auth.password_service import PasswordService
from src.domain.user.entities import User
from src.infrastructure.repositories.user_repository import UserRepository


class UserService(BaseService):
    """用户领域操作的应用服务。"""

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)
        self.password_service = PasswordService()

    async def create_user(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建新用户。"""
        # 检查唯一性
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(f"Username '{dto.username}' already exists")
        if await self.repo.get_by_email(dto.email):
            raise ConflictError(f"Email '{dto.email}' already exists")

        user = User(
            username=dto.username,
            email=dto.email,
            hashed_password=self.password_service.hash_password(dto.password),
            full_name=dto.full_name,
        )
        user = await self.repo.create(user)
        return self._to_response(user)

    async def get_user(self, user_id: str) -> UserResponseDTO:
        """根据 ID 获取用户。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User with id '{user_id}' not found")
        return self._to_response(user)

    async def get_user_by_username(self, username: str) -> User | None:
        """根据用户名获取用户实体（供内部使用）。"""
        return await self.repo.get_by_username(username)

    async def get_users(self, skip: int = 0, limit: int = 100) -> list[UserResponseDTO]:
        """获取所有用户（分页）。"""
        users = await self.repo.get_all(skip=skip, limit=limit)
        return [self._to_response(u) for u in users]

    async def get_users_count(self) -> int:
        """获取用户总数。"""
        return await self.repo.count()

    async def update_user(self, user_id: str, dto: UserUpdateDTO) -> UserResponseDTO:
        """更新用户信息。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User with id '{user_id}' not found")

        if dto.email is not None:
            existing = await self.repo.get_by_email(dto.email)
            if existing and existing.id != user_id:
                raise ConflictError(f"Email '{dto.email}' already exists")
            user.email = dto.email
        if dto.full_name is not None:
            user.full_name = dto.full_name
        if dto.is_active is not None:
            user.is_active = dto.is_active

        user = await self.repo.update(user)
        return self._to_response(user)

    async def delete_user(self, user_id: str) -> bool:
        """删除用户。"""
        if not await self.repo.delete(user_id):
            raise NotFoundError(f"User with id '{user_id}' not found")
        return True

    async def change_password(self, user_id: str, dto: ChangePasswordDTO) -> bool:
        """修改用户密码。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User with id '{user_id}' not found")

        if not self.password_service.verify_password(dto.old_password, user.hashed_password):
            raise UnauthorizedError("Invalid old password")

        user.hashed_password = self.password_service.hash_password(dto.new_password)
        await self.repo.update(user)
        return True

    async def create_superuser(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建超级用户。"""
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(f"Username '{dto.username}' already exists")
        if await self.repo.get_by_email(dto.email):
            raise ConflictError(f"Email '{dto.email}' already exists")

        user = User(
            username=dto.username,
            email=dto.email,
            hashed_password=self.password_service.hash_password(dto.password),
            full_name=dto.full_name,
            is_superuser=True,
        )
        user = await self.repo.create(user)
        return self._to_response(user)

    @staticmethod
    def _to_response(user: User) -> UserResponseDTO:
        """将用户实体转换为响应 DTO。"""
        roles: list[str] = []
        # 检查 roles 关系是否已加载，以避免在异步上下文中延迟加载
        from sqlalchemy import inspect as sa_inspect

        user_state = sa_inspect(user)
        if "roles" not in user_state.unloaded:
            roles = [ur.role.name for ur in user.roles if ur.role]
        return UserResponseDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=roles,
        )
