"""示例数据仓储接口。

单表 CRUD 示例模块；查询语义：name 等值过滤、category 等值过滤、is_active 状态过滤。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.entities.example_data import ExampleDataEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class ExampleDataRepositoryInterface(ABC):
    """示例数据仓储接口。"""

    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    @abstractmethod
    async def get_by_id(self, row_id: str) -> ExampleDataEntity | None:
        """按 ID 获取。"""
        ...

    @abstractmethod
    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        name: str | None = None,
        category: str | None = None,
        is_active: int | None = None,
    ) -> list[ExampleDataEntity]:
        """分页 + 过滤列表。"""
        ...

    @abstractmethod
    async def count(self, name: str | None = None, category: str | None = None, is_active: int | None = None) -> int:
        """按同条件统计总数。"""
        ...

    @abstractmethod
    async def create(self, entity: ExampleDataEntity) -> ExampleDataEntity:
        """创建。"""
        ...

    @abstractmethod
    async def update(self, entity: ExampleDataEntity) -> ExampleDataEntity:
        """更新。"""
        ...

    @abstractmethod
    async def delete(self, row_id: str) -> bool:
        """删除。"""
        ...

    @abstractmethod
    async def batch_delete(self, row_ids: list[str]) -> int:
        """批量删除，返回删除数量。"""
        ...
