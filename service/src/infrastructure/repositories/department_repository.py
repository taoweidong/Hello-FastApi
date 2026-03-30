"""使用 SQLModel 实现的部门仓库。"""

from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.department.repository import DepartmentRepositoryInterface
from src.infrastructure.database.models import Department


class DepartmentRepository(DepartmentRepositoryInterface):
    """部门仓储的 SQLModel 实现。"""

    async def get_all(self, session: AsyncSession) -> list[Department]:
        """获取所有部门，按排序号排序。"""
        result = await session.exec(select(Department).order_by(Department.sort))
        return list(result.all())

    async def get_by_id(self, dept_id: str, session: AsyncSession) -> Department | None:
        """根据 ID 获取部门。"""
        return await session.get(Department, dept_id)

    async def get_by_name(self, name: str, session: AsyncSession) -> Department | None:
        """根据名称获取部门。"""
        result = await session.exec(select(Department).where(Department.name == name))
        return result.one_or_none()

    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list[Department]:
        """根据父部门 ID 获取子部门，按排序号排序。"""
        query = select(Department).where(Department.parent_id == parent_id).order_by(Department.sort)
        result = await session.exec(query)
        return list(result.all())

    async def create(self, department: Department, session: AsyncSession) -> Department:
        """创建新部门。"""
        session.add(department)
        await session.flush()
        await session.refresh(department)
        return department

    async def update(self, department: Department, session: AsyncSession) -> Department:
        """更新现有部门。"""
        merged = await session.merge(department)
        await session.flush()
        await session.refresh(merged)
        return merged

    async def delete(self, dept_id: str, session: AsyncSession) -> bool:
        """根据 ID 删除部门。"""
        department = await self.get_by_id(dept_id, session)
        if department is None:
            return False
        await session.delete(department)
        await session.flush()
        return True

    async def count(
        self,
        name: str | None = None,
        status: int | None = None,
        session: AsyncSession = None,
    ) -> int:
        """获取部门总数（支持筛选）。"""
        query = select(sa_func.count()).select_from(Department)

        # 应用筛选条件
        if name:
            query = query.where(Department.name.contains(name))
        if status is not None:
            query = query.where(Department.status == status)

        result = await session.execute(query)
        return result.scalar_one()
