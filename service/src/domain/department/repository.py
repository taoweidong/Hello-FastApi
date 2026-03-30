"""部门领域 - 仓库接口。"""

from abc import ABC, abstractmethod

from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.database.models import Department


class DepartmentRepositoryInterface(ABC):
    """部门的抽象仓库接口。"""

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> list[Department]:
        """获取所有部门。"""
        ...

    @abstractmethod
    async def get_by_id(self, dept_id: str, session: AsyncSession) -> Department | None:
        """根据 ID 获取部门。"""
        ...

    @abstractmethod
    async def get_by_name(self, name: str, session: AsyncSession) -> Department | None:
        """根据名称获取部门。"""
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list[Department]:
        """根据父部门 ID 获取子部门。"""
        ...

    @abstractmethod
    async def create(self, department: Department, session: AsyncSession) -> Department:
        """创建部门。"""
        ...

    @abstractmethod
    async def update(self, department: Department, session: AsyncSession) -> Department:
        """更新部门。"""
        ...

    @abstractmethod
    async def delete(self, dept_id: str, session: AsyncSession) -> bool:
        """删除部门。"""
        ...

    @abstractmethod
    async def count(
        self,
        name: str | None = None,
        status: int | None = None,
        session: AsyncSession = None,
    ) -> int:
        """获取部门总数。"""
        ...
