"""使用 SQLModel 和 FastCRUD 实现的用户仓库。"""

from fastcrud import FastCRUD
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.user_repository import UserRepositoryInterface
from src.infrastructure.database.models import User


class UserRepository(UserRepositoryInterface):
    """UserRepositoryInterface 的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        """初始化用户仓储。

        Args:
            session: 数据库会话
        """
        self.session = session
        self._crud = FastCRUD(User)

    async def get_by_id(self, user_id: str) -> User | None:
        """根据 ID 获取用户。

        Args:
            user_id: 用户ID

        Returns:
            用户对象或 None
        """
        return await self._crud.get(self.session, id=user_id, schema_to_select=User, return_as_model=True)

    async def get_by_username(self, username: str) -> User | None:
        """根据用户名获取用户。

        Args:
            username: 用户名

        Returns:
            用户对象或 None
        """
        return await self._crud.get(self.session, username=username, schema_to_select=User, return_as_model=True)

    async def get_by_email(self, email: str) -> User | None:
        """根据邮箱获取用户。

        Args:
            email: 电子邮箱

        Returns:
            用户对象或 None
        """
        return await self._crud.get(self.session, email=email, schema_to_select=User, return_as_model=True)

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        status: int | None = None,
        dept_id: int | None = None,
    ) -> list[User]:
        """获取用户列表（支持筛选和分页）。

        Args:
            page_num: 页码，从1开始
            page_size: 每页数量
            username: 用户名模糊查询
            phone: 手机号模糊查询
            email: 邮箱模糊查询
            status: 用户状态(0-禁用, 1-启用)
            dept_id: 部门ID

        Returns:
            用户列表
        """
        # 构建筛选条件
        filters: dict[str, any] = {}
        if username:
            filters["username"] = username
        if phone:
            filters["phone"] = phone
        if email:
            filters["email"] = email
        if status is not None:
            filters["status"] = status
        if dept_id is not None:
            filters["dept_id"] = dept_id

        # 使用 FastCRUD 的 get_multi 方法，支持分页和筛选
        result = await self._crud.get_multi(
            self.session,
            offset=(page_num - 1) * page_size,
            limit=page_size,
            schema_to_select=User,
            return_as_model=True,
            **filters,
        )
        return list(result.get("data", []))

    async def count(
        self,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        status: int | None = None,
        dept_id: int | None = None,
    ) -> int:
        """获取用户总数（支持筛选）。

        Args:
            username: 用户名模糊查询
            phone: 手机号模糊查询
            email: 邮箱模糊查询
            status: 用户状态(0-禁用, 1-启用)
            dept_id: 部门ID

        Returns:
            用户数量
        """
        filters: dict[str, any] = {}
        if username:
            filters["username"] = username
        if phone:
            filters["phone"] = phone
        if email:
            filters["email"] = email
        if status is not None:
            filters["status"] = status
        if dept_id is not None:
            filters["dept_id"] = dept_id

        return await self._crud.count(self.session, **filters)

    async def create(self, user: User) -> User:
        """创建用户。

        Args:
            user: 用户对象

        Returns:
            创建后的用户对象
        """
        return await self._crud.create(self.session, user)

    async def update(self, user: User) -> User:
        """更新用户。

        Args:
            user: 用户对象

        Returns:
            更新后的用户对象
        """
        return await self._crud.update(self.session, user)

    async def delete(self, user_id: str) -> bool:
        """删除用户。

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        deleted_count = await self._crud.delete(self.session, id=user_id)
        return deleted_count > 0

    async def batch_delete(self, user_ids: list[str]) -> int:
        """批量删除用户。

        Args:
            user_ids: 用户ID列表

        Returns:
            删除的用户数量
        """
        deleted_count = 0
        for user_id in user_ids:
            if await self.delete(user_id):
                deleted_count += 1
        return deleted_count

    async def update_status(self, user_id: str, status: int) -> bool:
        """更新用户状态。

        Args:
            user_id: 用户ID
            status: 状态(0-禁用, 1-启用)

        Returns:
            是否更新成功
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return False
        user.status = status
        await self.session.flush()
        return True

    async def reset_password(self, user_id: str, hashed_password: str) -> bool:
        """重置用户密码。

        Args:
            user_id: 用户ID
            hashed_password: 加密后的密码

        Returns:
            是否重置成功
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return False
        user.hashed_password = hashed_password
        await self.session.flush()
        return True
