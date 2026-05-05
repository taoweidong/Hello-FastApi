"""使用 SQLModel 原生 API 实现的部门仓库。

设计原则：
- 基础 CRUD 使用基类实现
- 按字段查询（name, code, parent_id）在此层实现
- 复杂业务逻辑（层级验证、树形操作）移至服务层
"""

from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.department import DepartmentEntity
from src.domain.repositories.department_repository import DepartmentRepositoryInterface
from src.infrastructure.database.models import Department
from src.infrastructure.repositories.base import GenericRepository


class DepartmentRepository(GenericRepository[Department, DepartmentEntity], DepartmentRepositoryInterface):
    """部门仓储的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[Department]:
        return Department

    def _to_domain(self, model: Department) -> DepartmentEntity:
        return model.to_domain()

    def _from_domain(self, entity: DepartmentEntity) -> Department:
        return Department.from_domain(entity)

    # ========== 自定义查询（仓库层）==========

    async def get_all(self) -> list[DepartmentEntity]:
        """获取所有部门，按排序号排序。"""
        stmt = select(Department).order_by(Department.rank)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return [self._to_domain(m) for m in items]

    async def get_by_name(self, name: str) -> DepartmentEntity | None:
        """根据名称获取部门。"""
        return await self.get_one_by("name", name)

    async def get_by_code(self, code: str) -> DepartmentEntity | None:
        """根据编码获取部门。"""
        return await self.get_one_by("code", code)

    async def get_by_parent_id(self, parent_id: str | None) -> list[DepartmentEntity]:
        """根据父部门 ID 获取子部门，按排序号排序。"""
        stmt = select(Department).where(Department.parent_id == parent_id).order_by(Department.rank)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return [self._to_domain(m) for m in items]

    # ========== 覆盖基类方法（类型化参数）==========

    async def count(self, name: str | None = None, is_active: int | None = None) -> int:
        """获取部门总数（支持筛选）。"""
        filters: dict[str, Any] = {}
        if name:
            filters["name"] = name
        if is_active is not None:
            filters["is_active"] = is_active
        return await super().count(**filters)

    async def get_filtered(self, name: str | None = None, is_active: int | None = None) -> list[DepartmentEntity]:
        """获取过滤后的部门列表，按排序号排序。

        Args:
            name: 名称模糊匹配（包含即命中）
            is_active: 是否启用（0/1）

        Returns:
            过滤后的部门实体列表
        """
        from sqlmodel import select

        stmt = select(Department).order_by(Department.rank)
        if name:
            stmt = stmt.where(Department.name.contains(name))
        if is_active is not None:
            stmt = stmt.where(Department.is_active == is_active)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return [self._to_domain(m) for m in items]
