"""使用 SQLModel 实现的用户仓库。"""

from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.user.repository import UserRepositoryInterface
from src.infrastructure.database.models import User


class UserRepository(UserRepositoryInterface):
    """UserRepositoryInterface 的 SQLModel 实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.session.exec(select(User).where(User.id == user_id))
        return result.one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.exec(select(User).where(User.username == username))
        return result.one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.exec(select(User).where(User.email == email))
        return result.one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.session.exec(select(User).offset(skip).limit(limit))
        return list(result.all())

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
        # 聚合查询使用 session.execute 而非 session.exec
        result = await self.session.execute(select(sa_func.count()).select_from(User))
        return result.scalar_one()
