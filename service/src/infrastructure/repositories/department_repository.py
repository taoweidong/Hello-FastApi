"""使用 SQLModel 和 FastCRUD 实现的部门仓库。"""

from typing import Any

from fastcrud import FastCRUD
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.department_repository import DepartmentRepositoryInterface
from src.infrastructure.database.models import Department


class DepartmentRepository(DepartmentRepositoryInterface):
    """部门仓储的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        """初始化部门仓储。

        Args:
            session: 数据库会话
        """
        self.session = session
        self._crud = FastCRUD(Department)

    async def get_all(self) -> list[Department]:
        """获取所有部门，按排序号排序。

        Returns:
            部门列表
        """
        result = await self._crud.get_multi(self.session, schema_to_select=Department, return_as_model=True, return_total_count=False)
        departments = result.get("data", [])
        # 按 sort 排序
        return sorted(departments, key=lambda d: d.sort)

    async def get_by_id(self, dept_id: str) -> Department | None:
        """根据 ID 获取部门。

        Args:
            dept_id: 部门ID

        Returns:
            部门对象或 None
        """
        return await self._crud.get(self.session, id=dept_id, schema_to_select=Department, return_as_model=True)

    async def get_by_name(self, name: str) -> Department | None:
        """根据名称获取部门。

        Args:
            name: 部门名称

        Returns:
            部门对象或 None
        """
        return await self._crud.get(self.session, name=name, schema_to_select=Department, return_as_model=True)

    async def get_by_parent_id(self, parent_id: str | None) -> list[Department]:
        """根据父部门 ID 获取子部门，按排序号排序。

        Args:
            parent_id: 父部门ID

        Returns:
            子部门列表
        """
        result = await self._crud.get_multi(self.session, parent_id=parent_id, schema_to_select=Department, return_as_model=True, return_total_count=False)
        departments = result.get("data", [])
        # 按 sort 排序
        return sorted(departments, key=lambda d: d.sort)

    async def create(self, department: Department) -> Department:
        """创建新部门。

        Args:
            department: 部门对象

        Returns:
            创建后的部门对象
        """
        return await self._crud.create(self.session, department)

    async def update(self, department: Department) -> Department:
        """更新现有部门。

        Args:
            department: 部门对象

        Returns:
            更新后的部门对象
        """
        return await self._crud.update(self.session, department)

    async def delete(self, dept_id: str) -> bool:
        """根据 ID 删除部门。

        Args:
            dept_id: 部门ID

        Returns:
            是否删除成功
        """
        deleted_count = await self._crud.delete(self.session, id=dept_id)
        return deleted_count > 0

    async def count(self, name: str | None = None, status: int | None = None) -> int:
        """获取部门总数（支持筛选）。

        Args:
            name: 部门名称模糊查询
            status: 部门状态

        Returns:
            部门数量
        """
        filters: dict[str, Any] = {}
        if name:
            filters["name"] = name
        if status is not None:
            filters["status"] = status

        return await self._crud.count(self.session, **filters)
