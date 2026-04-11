"""应用层 - 用户服务。"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.user_dto import ChangePasswordDTO, UserCreateDTO, UserListQueryDTO, UserResponseDTO, UserUpdateDTO
from src.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.password_service import PasswordService
from src.infrastructure.database.models import User


class UserService:
    """用户领域操作的应用服务。"""

    def __init__(self, session: AsyncSession, repo: UserRepositoryInterface, password_service: PasswordService, role_repo: RoleRepositoryInterface):
        """初始化用户服务。

        Args:
            session: 数据库会话，用于事务控制
            repo: 用户仓储接口实例
            password_service: 密码服务实例
            role_repo: 角色仓储接口实例
        """
        self.session = session
        self.repo = repo
        self.password_service = password_service
        self.role_repo = role_repo

    async def create_user(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建新用户。

        Args:
            dto: 用户创建数据传输对象

        Returns:
            用户响应数据传输对象

        Raises:
            ConflictError: 用户名或邮箱已存在
        """
        # 检查唯一性
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(f"用户名 '{dto.username}' 已存在")
        if dto.email and await self.repo.get_by_email(dto.email):
            raise ConflictError(f"邮箱 '{dto.email}' 已存在")

        # 创建用户实体，映射所有新字段
        user = User(username=dto.username, email=dto.email, hashed_password=self.password_service.hash_password(dto.password), nickname=dto.nickname, phone=dto.phone, sex=dto.sex, avatar=dto.avatar, status=dto.status, dept_id=dto.dept_id, remark=dto.remark)
        await self.repo.create(user)
        await self.session.flush()
        # 重新从数据库获取以加载 roles 关系
        created_user = await self.repo.get_by_id(user.id)
        return await self._to_response(created_user)

    async def get_user(self, user_id: str) -> UserResponseDTO:
        """根据 ID 获取用户。

        Args:
            user_id: 用户ID

        Returns:
            用户响应数据传输对象

        Raises:
            NotFoundError: 用户不存在
        """
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        return await self._to_response(user)

    async def get_user_by_username(self, username: str) -> User | None:
        """根据用户名获取用户实体（供内部使用）。"""
        return await self.repo.get_by_username(username)

    async def get_users(self, query: UserListQueryDTO) -> tuple[list[UserResponseDTO], int]:
        """获取用户列表（支持筛选和分页）。

        Args:
            query: 用户列表查询数据传输对象

        Returns:
            (用户响应列表, 总数) 元组
        """
        # 获取筛选后的用户列表
        users = await self.repo.get_all(page_num=query.pageNum, page_size=query.pageSize, username=query.username, phone=query.phone, email=query.email, status=query.status, dept_id=query.deptId)

        # 获取总数
        total = await self.repo.count(username=query.username, phone=query.phone, email=query.email, status=query.status, dept_id=query.deptId)

        # 转换为响应DTO
        user_responses = [await self._to_response(u) for u in users]
        return user_responses, total

    async def update_user(self, user_id: str, dto: UserUpdateDTO) -> UserResponseDTO:
        """更新用户信息。

        Args:
            user_id: 用户ID
            dto: 用户更新数据传输对象

        Returns:
            用户响应数据传输对象

        Raises:
            NotFoundError: 用户不存在
            ConflictError: 邮箱已存在
        """
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        # 选择性更新：只更新 DTO 中非 None 的字段
        if dto.email is not None:
            existing = await self.repo.get_by_email(dto.email)
            if existing and existing.id != user_id:
                raise ConflictError(f"邮箱 '{dto.email}' 已存在")
            user.email = dto.email

        if dto.nickname is not None:
            user.nickname = dto.nickname
        if dto.phone is not None:
            user.phone = dto.phone
        if dto.sex is not None:
            user.sex = dto.sex
        if dto.avatar is not None:
            user.avatar = dto.avatar
        if dto.status is not None:
            user.status = dto.status
        if dto.dept_id is not None:
            user.dept_id = dto.dept_id
        if dto.remark is not None:
            user.remark = dto.remark

        user = await self.repo.update(user)
        await self.session.flush()
        # 重新从数据库获取以加载 roles 关系
        updated_user = await self.repo.get_by_id(user_id)
        return await self._to_response(updated_user)

    async def delete_user(self, user_id: str) -> bool:
        """删除用户。

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 用户不存在
        """
        if not await self.repo.delete(user_id):
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        return True

    async def batch_delete_users(self, user_ids: list[str]) -> dict:
        """批量删除用户。

        Args:
            user_ids: 用户ID列表

        Returns:
            包含删除结果的字典
        """
        deleted_count = await self.repo.batch_delete(user_ids)
        return {"deleted_count": deleted_count, "total_requested": len(user_ids)}

    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """管理员重置用户密码。

        Args:
            user_id: 用户ID
            new_password: 新密码

        Returns:
            是否重置成功

        Raises:
            NotFoundError: 用户不存在
        """
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        hashed_password = self.password_service.hash_password(new_password)
        await self.repo.reset_password(user_id, hashed_password)
        return True

    async def update_status(self, user_id: str, status: int) -> bool:
        """更改用户状态。

        Args:
            user_id: 用户ID
            status: 状态(0-禁用, 1-启用)

        Returns:
            是否更新成功

        Raises:
            NotFoundError: 用户不存在
        """
        if not await self.repo.update_status(user_id, status):
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")
        return True

    async def change_password(self, user_id: str, dto: ChangePasswordDTO) -> bool:
        """修改用户密码。

        Args:
            user_id: 用户ID
            dto: 密码修改数据传输对象

        Returns:
            是否修改成功

        Raises:
            NotFoundError: 用户不存在
            UnauthorizedError: 旧密码不正确
        """
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        # DTO 字段名已改为 oldPassword 和 newPassword
        if not self.password_service.verify_password(dto.oldPassword, user.hashed_password):
            raise UnauthorizedError("旧密码不正确")

        user.hashed_password = self.password_service.hash_password(dto.newPassword)
        await self.repo.update(user)
        return True

    async def create_superuser(self, dto: UserCreateDTO) -> UserResponseDTO:
        """创建超级用户。

        Args:
            dto: 用户创建数据传输对象

        Returns:
            用户响应数据传输对象
        """
        if await self.repo.get_by_username(dto.username):
            raise ConflictError(f"用户名 '{dto.username}' 已存在")
        if dto.email and await self.repo.get_by_email(dto.email):
            raise ConflictError(f"邮箱 '{dto.email}' 已存在")

        user = User(username=dto.username, email=dto.email, hashed_password=self.password_service.hash_password(dto.password), nickname=dto.nickname, phone=dto.phone, sex=dto.sex, avatar=dto.avatar, status=dto.status, dept_id=dto.dept_id, remark=dto.remark, is_superuser=True)
        user = await self.repo.create(user)
        return await self._to_response(user)

    async def assign_roles(self, user_id: str, role_ids: list[str]) -> bool:
        """为用户分配角色。

        Args:
            user_id: 用户ID
            role_ids: 角色ID列表

        Returns:
            是否分配成功

        Raises:
            NotFoundError: 用户不存在
        """
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"用户 ID '{user_id}' 不存在")

        # 使用注入的角色仓储分配角色
        await self.role_repo.assign_roles_to_user(user_id, role_ids)
        return True

    async def _to_response(self, user: User) -> UserResponseDTO:
        """将用户实体转换为响应 DTO。

        Args:
            user: 用户实体

        Returns:
            用户响应数据传输对象
        """
        # 构建角色列表（包含 id 和 name）
        roles: list[dict] = []
        if user.roles:
            for ur in user.roles:
                if ur.role:
                    roles.append({"id": ur.role.id, "name": ur.role.name})

        # 构建权限列表
        permissions: list[str] = []
        if user.roles:
            for ur in user.roles:
                if ur.role and ur.role.permissions:
                    for perm in ur.role.permissions:
                        if perm.code and perm.code not in permissions:
                            permissions.append(perm.code)

        return UserResponseDTO(id=user.id, username=user.username, nickname=user.nickname, avatar=user.avatar, email=user.email, phone=user.phone, sex=user.sex, status=user.status, roles=roles, permissions=permissions, createTime=user.created_at, updateTime=user.updated_at)
