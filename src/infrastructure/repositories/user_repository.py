"""使用 SQLAlchemy 实现的用户仓库。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.user.entities import User
from src.domain.user.repository import UserRepositoryInterface


class UserRepository(UserRepositoryInterface):
    """UserRepositoryInterface 的 SQLAlchemy 实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).options(selectinload(User.roles)).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).options(selectinload(User.roles)).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        stmt = select(User).options(selectinload(User.roles)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        merged = await self.session.merge(user)
        await self.session.flush()
        await self.session.refresh(merged)
        return merged

    async def delete(self, user_id: str) -> bool:
        user = await self.get_by_id(user_id)
        if user is None:
            return False
        await self.session.delete(user)
        await self.session.flush()
        return True

    async def count(self) -> int:
        stmt = select(func.count()).select_from(User)
        result = await self.session.execute(stmt)
        return result.scalar_one()
