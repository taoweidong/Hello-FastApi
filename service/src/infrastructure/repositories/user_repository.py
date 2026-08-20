"""使用 SQLModel 原生 API 实现的用户仓库。

设计原则：
- 基础 CRUD 使用基类实现
- 按字段查询（username, email）在此层实现
- 复杂业务逻辑（创建验证、状态更新）移至服务层
"""

from typing import Any

from sqlalchemy import false as sa_false
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.user import UserEntity
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.infrastructure.database.models import User
from src.infrastructure.repositories.base import GenericRepository


class UserRepository(GenericRepository[User, UserEntity], UserRepositoryInterface):
    """UserRepositoryInterface 的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[User]:
        return User

    def _to_domain(self, model: User) -> UserEntity:
        return model.to_domain()

    def _from_domain(self, entity: UserEntity) -> User:
        return User.from_domain(entity)

    # ========== 自定义查询 ==========

    async def get_by_username(self, username: str) -> UserEntity | None:
        """根据用户名获取用户。"""
        return await self.get_one_by("username", username)

    async def get_by_email(self, email: str) -> UserEntity | None:
        """根据邮箱获取用户。"""
        return await self.get_one_by("email", email)

    # ========== 覆盖基类方法（支持类型化参数）==========

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
        scope_dept_ids: list[str] | None = None,
        scope_user_id: str | None = None,
    ) -> list[UserEntity]:
        """获取用户列表（支持筛选、分页及数据权限范围过滤）。"""
        filters = self._build_user_filters(username, phone, email, is_active, dept_id)
        stmt = select(User)
        stmt = self._apply_filters(stmt, filters)
        stmt = self._apply_scope_filters(stmt, scope_dept_ids, scope_user_id)
        offset = (page_num - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return [self._to_domain(m) for m in items]

    async def count(
        self,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
        scope_dept_ids: list[str] | None = None,
        scope_user_id: str | None = None,
    ) -> int:
        """获取用户总数（支持筛选与数据权限范围过滤）。"""
        filters = self._build_user_filters(username, phone, email, is_active, dept_id)
        stmt = select(sa_func.count()).select_from(User)
        stmt = self._apply_filters(stmt, filters)
        stmt = self._apply_scope_filters(stmt, scope_dept_ids, scope_user_id)
        result = await self.session.exec(stmt)
        return result.one()

    # ========== 批量操作 ==========

    async def batch_delete(self, user_ids: list[str]) -> int:
        """批量删除用户。"""
        return await super().batch_delete(user_ids)

    # ========== 内部辅助方法 ==========

    def _build_user_filters(
        self, username: str | None, phone: str | None, email: str | None, is_active: int | None, dept_id: str | None
    ) -> dict[str, Any]:
        """构建用户筛选条件。"""
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
        return filters

    def _apply_scope_filters(self, stmt: Any, scope_dept_ids: list[str] | None, scope_user_id: str | None) -> Any:
        """应用数据权限范围过滤条件。

        Args:
            stmt: 查询语句
            scope_dept_ids: 可见部门ID列表（None 表示不限；空列表表示无可见数据）
            scope_user_id: 仅本人可见时限定当前用户ID（优先级高于部门范围）
        """
        if scope_user_id is not None:
            return stmt.where(User.id == scope_user_id)
        if scope_dept_ids is not None:
            if not scope_dept_ids:
                # 空部门范围：强制无结果
                return stmt.where(sa_false())
            return stmt.where(User.dept_id.in_(scope_dept_ids))
        return stmt
