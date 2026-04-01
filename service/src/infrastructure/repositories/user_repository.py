"""使用 SQLModel 实现的用户仓库。"""

from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.user_repository import UserRepositoryInterface
from src.infrastructure.database.models import User


class UserRepository(UserRepositoryInterface):
    """UserRepositoryInterface 的 SQLModel 实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        """根据 ID 获取用户。"""
        result = await self.session.exec(select(User).where(User.id == user_id))
        return result.one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """根据用户名获取用户。"""
        result = await self.session.exec(select(User).where(User.username == username))
        return result.one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """根据邮箱获取用户。"""
        result = await self.session.exec(select(User).where(User.email == email))
        return result.one_or_none()

    async def get_all(self, page_num: int = 1, page_size: int = 10, username: str | None = None, phone: str | None = None, email: str | None = None, status: int | None = None, dept_id: int | None = None) -> list[User]:
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
        query = select(User)

        # 应用筛选条件
        if username:
            query = query.where(User.username.contains(username))
        if phone:
            query = query.where(User.phone.contains(phone))
        if email:
            query = query.where(User.email.contains(email))
        if status is not None:
            query = query.where(User.status == status)
        if dept_id is not None:
            query = query.where(User.dept_id == dept_id)

        # 分页
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.exec(query)
        return list(result.all())

    async def count(self, username: str | None = None, phone: str | None = None, email: str | None = None, status: int | None = None, dept_id: int | None = None) -> int:
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
        query = select(sa_func.count()).select_from(User)

        # 应用筛选条件
        if username:
            query = query.where(User.username.contains(username))
        if phone:
            query = query.where(User.phone.contains(phone))
        if email:
            query = query.where(User.email.contains(email))
        if status is not None:
            query = query.where(User.status == status)
        if dept_id is not None:
            query = query.where(User.dept_id == dept_id)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, user: User) -> User:
        """创建用户。"""
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """更新用户。"""
        merged = await self.session.merge(user)
        await self.session.flush()
        await self.session.refresh(merged)
        return merged

    async def delete(self, user_id: str) -> bool:
        """删除用户。"""
        user = await self.get_by_id(user_id)
        if user is None:
            return False
        await self.session.delete(user)
        await self.session.flush()
        return True

    async def batch_delete(self, user_ids: list[str]) -> int:
        """批量删除用户。

        Args:
            user_ids: 用户ID列表

        Returns:
            删除的用户数量
        """
        count = 0
        for user_id in user_ids:
            if await self.delete(user_id):
                count += 1
        return count

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
