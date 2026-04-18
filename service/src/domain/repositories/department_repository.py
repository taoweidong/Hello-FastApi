"""部门领域 - 仓储接口。

定义部门仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.entities.department import DepartmentEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class DepartmentRepositoryInterface(ABC):
    """部门的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    @abstractmethod
    async def get_all(self) -> list[DepartmentEntity]:
        """获取所有部门。"""
        ...

    @abstractmethod
    async def get_by_id(self, dept_id: str) -> DepartmentEntity | None:
        """根据 ID 获取部门。"""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> DepartmentEntity | None:
        """根据名称获取部门。"""
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> DepartmentEntity | None:
        """根据编码获取部门。"""
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None) -> list[DepartmentEntity]:
        """根据父部门 ID 获取子部门。"""
        ...

    @abstractmethod
    async def create(self, department: DepartmentEntity) -> DepartmentEntity:
        """创建部门。"""
        ...

    @abstractmethod
    async def update(self, department: DepartmentEntity) -> DepartmentEntity:
        """更新部门。"""
        ...

    @abstractmethod
    async def delete(self, dept_id: str) -> bool:
        """删除部门。"""
        ...

    @abstractmethod
    async def count(self, name: str | None = None, is_active: int | None = None) -> int:
        """获取部门总数。"""
        ...
