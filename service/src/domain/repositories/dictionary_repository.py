"""字典领域 - 仓储接口。

定义字典仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from src.infrastructure.database.models import Dictionary


class DictionaryRepositoryInterface(ABC):
    """字典的抽象仓储接口。"""

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> list["Dictionary"]:
        """获取所有字典。"""
        ...

    @abstractmethod
    async def get_by_id(self, dict_id: str, session: AsyncSession) -> "Dictionary | None":
        """根据 ID 获取字典。"""
        ...

    @abstractmethod
    async def get_by_name(self, name: str, session: AsyncSession) -> "Dictionary | None":
        """根据名称获取字典。"""
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list["Dictionary"]:
        """根据父字典 ID 获取子字典。"""
        ...

    @abstractmethod
    async def get_max_sort(self, parent_id: str | None, session: AsyncSession) -> int:
        """获取同级最大排序值。"""
        ...

    @abstractmethod
    async def create(self, dictionary: "Dictionary", session: AsyncSession) -> "Dictionary":
        """创建字典。"""
        ...

    @abstractmethod
    async def update(self, dictionary: "Dictionary", session: AsyncSession) -> "Dictionary":
        """更新字典。"""
        ...

    @abstractmethod
    async def delete(self, dict_id: str, session: AsyncSession) -> bool:
        """删除字典。"""
        ...
