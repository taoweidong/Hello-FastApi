"""字典领域 - 仓储接口。

定义字典仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.entities.dictionary import DictionaryEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class DictionaryRepositoryInterface(ABC):
    """字典的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    @abstractmethod
    async def get_all(self) -> list[DictionaryEntity]:
        """获取所有字典。"""
        ...

    @abstractmethod
    async def get_by_id(self, dict_id: str) -> DictionaryEntity | None:
        """根据 ID 获取字典。"""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> DictionaryEntity | None:
        """根据名称获取字典。"""
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None) -> list[DictionaryEntity]:
        """根据父字典 ID 获取子字典。"""
        ...

    @abstractmethod
    async def get_max_sort(self, parent_id: str | None) -> int:
        """获取同级最大排序值。"""
        ...

    @abstractmethod
    async def create(self, dictionary: DictionaryEntity) -> DictionaryEntity:
        """创建字典。"""
        ...

    @abstractmethod
    async def update(self, dictionary: DictionaryEntity) -> DictionaryEntity:
        """更新字典。"""
        ...

    @abstractmethod
    async def delete(self, dict_id: str) -> bool:
        """删除字典。"""
        ...

    @abstractmethod
    async def get_filtered(self, name: str | None = None, is_active: int | None = None) -> list[DictionaryEntity]:
        """获取过滤后的字典列表，按排序号升序排列。

        Args:
            name: 名称模糊匹配（包含即命中）
            is_active: 是否启用（0/1）

        Returns:
            过滤后的字典实体列表
        """
        ...
