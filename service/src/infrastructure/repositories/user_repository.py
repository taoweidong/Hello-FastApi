"""使用 SQLModel 和 FastCRUD 实现的用户仓库。"""

from typing import Any

from fastcrud import FastCRUD
from sqlalchemy import delete as sa_delete
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.user import UserEntity
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.infrastructure.database.models import User


class UserRepository(UserRepositoryInterface):
    """UserRepositoryInterface 的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(User)

    async def get_by_id(self, user_id: str) -> UserEntity | None:
        model = await self._crud.get(self.session, id=user_id, schema_to_select=User, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_username(self, username: str) -> UserEntity | None:
        model = await self._crud.get(self.session, username=username, schema_to_select=User, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_email(self, email: str) -> UserEntity | None:
        model = await self._crud.get(self.session, email=email, schema_to_select=User, return_as_model=True)
        return model.to_domain() if model else None

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
    ) -> list[UserEntity]:
        """获取用户列表（支持筛选和分页）。"""
        filters: dict[str, Any] = {}
        if username:
            filters["username"] = username
        if phone:
            filters["phone"] = phone
        if email:
            filters["email"] = email
        if is_active is not None:
            filters["is_active"] = is_active
        if dept_id is not None:
            filters["dept_id"] = dept_id

        result = await self._crud.get_multi(
            self.session,
            offset=(page_num - 1) * page_size,
            limit=page_size,
            schema_to_select=User,
            return_as_model=True,
            **filters,
        )
        models = list(result.get("data", []))
        return [m.to_domain() for m in models]

    async def count(
        self,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
    ) -> int:
        """获取用户总数（支持筛选）。"""
        filters: dict[str, Any] = {}
        if username:
            filters["username"] = username
        if phone:
            filters["phone"] = phone
        if email:
            filters["email"] = email
        if is_active is not None:
            filters["is_active"] = is_active
        if dept_id is not None:
            filters["dept_id"] = dept_id

        return await self._crud.count(self.session, **filters)

    async def create(self, user: UserEntity) -> UserEntity:
        model = User.from_domain(user)
        result = await self._crud.create(self.session, model)
        if isinstance(result, User):
            return result.to_domain()
        await self.session.flush()
        loaded = await self.get_by_id(user.id)
        if loaded is not None:
            return loaded
        loaded = await self.get_by_username(user.username)
        if loaded is not None:
            return loaded
        raise RuntimeError("用户写入后无法按主键或用户名加载")

    async def update(self, user: UserEntity) -> UserEntity:
        model = User.from_domain(user)
        merged = await self.session.merge(model)
        await self.session.flush()
        loaded = await self.get_by_id(merged.id)
        if loaded is None:
            raise RuntimeError("用户更新后无法加载")
        return loaded

    async def delete(self, user_id: str) -> bool:
        result = await self.session.execute(sa_delete(User).where(User.id == user_id))
        await self.session.flush()
        return (result.rowcount or 0) > 0

    async def batch_delete(self, user_ids: list[str]) -> int:
        """批量删除用户。"""
        if not user_ids:
            return 0
        stmt = sa_delete(User).where(User.id.in_(user_ids))
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0

    async def update_status(self, user_id: str, is_active: int) -> bool:
        """更新用户启用状态。"""
        user = await self._crud.get(self.session, id=user_id, schema_to_select=User, return_as_model=True)
        if user is None:
            return False
        user.is_active = is_active
        await self.session.flush()
        return True

    async def reset_password(self, user_id: str, hashed_password: str) -> bool:
        """重置用户密码。"""
        user = await self._crud.get(self.session, id=user_id, schema_to_select=User, return_as_model=True)
        if user is None:
            return False
        user.password = hashed_password
        await self.session.flush()
        return True
