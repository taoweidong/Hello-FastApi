"""使用 SQLModel 和 FastCRUD 实现的部门仓库。"""

from typing import Any

from fastcrud import FastCRUD
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.department import DepartmentEntity
from src.domain.repositories.department_repository import DepartmentRepositoryInterface
from src.infrastructure.database.models import Department


class DepartmentRepository(DepartmentRepositoryInterface):
    """部门仓储的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(Department)

    async def get_all(self) -> list[DepartmentEntity]:
        """获取所有部门，按排序号排序。"""
        result = await self._crud.get_multi(self.session, schema_to_select=Department, return_as_model=True, return_total_count=False)
        departments = result.get("data", [])
        return sorted([d.to_domain() for d in departments], key=lambda d: d.rank)

    async def get_by_id(self, dept_id: str) -> DepartmentEntity | None:
        """根据 ID 获取部门。"""
        model = await self._crud.get(self.session, id=dept_id, schema_to_select=Department, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_name(self, name: str) -> DepartmentEntity | None:
        """根据名称获取部门。"""
        model = await self._crud.get(self.session, name=name, schema_to_select=Department, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_code(self, code: str) -> DepartmentEntity | None:
        """根据编码获取部门。"""
        model = await self._crud.get(self.session, code=code, schema_to_select=Department, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_parent_id(self, parent_id: str | None) -> list[DepartmentEntity]:
        """根据父部门 ID 获取子部门，按排序号排序。"""
        result = await self._crud.get_multi(self.session, parent_id=parent_id, schema_to_select=Department, return_as_model=True, return_total_count=False)
        departments = result.get("data", [])
        return sorted([d.to_domain() for d in departments], key=lambda d: d.rank)

    async def create(self, department: DepartmentEntity) -> DepartmentEntity:
        """创建新部门。"""
        model = Department.from_domain(department)
        self.session.add(model)
        await self.session.flush()
        # 读回以获取自动生成的字段
        loaded = await self.get_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update(self, department: DepartmentEntity) -> DepartmentEntity:
        """更新现有部门。"""
        from sqlalchemy import update as sa_update

        stmt = (
            sa_update(Department)
            .where(Department.id == department.id)
            .values(mode_type=department.mode_type, name=department.name, code=department.code, rank=department.rank, auto_bind=department.auto_bind, is_active=department.is_active, creator_id=department.creator_id, modifier_id=department.modifier_id, parent_id=department.parent_id, description=department.description)
        )
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(department.id)
        return updated  # type: ignore[return-value]

    async def delete(self, dept_id: str) -> bool:
        """根据 ID 删除部门。"""
        from sqlalchemy import delete as sa_delete
        from sqlalchemy import update as sa_update

        from src.infrastructure.database.models import User

        # 先将引用该部门的用户 dept_id 设为 NULL
        user_update = sa_update(User).where(User.dept_id == dept_id).values(dept_id=None)
        await self.session.execute(user_update)
        await self.session.flush()

        stmt = sa_delete(Department).where(Department.id == dept_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def count(self, name: str | None = None, is_active: int | None = None) -> int:
        """获取部门总数（支持筛选）。"""
        filters: dict[str, Any] = {}
        if name:
            filters["name"] = name
        if is_active is not None:
            filters["is_active"] = is_active

        return await self._crud.count(self.session, **filters)
