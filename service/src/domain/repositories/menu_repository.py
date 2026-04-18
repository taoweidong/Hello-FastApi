"""菜单领域 - 仓储接口。

定义菜单仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class MenuRepositoryInterface(ABC):
    """菜单领域的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    @abstractmethod
    async def get_all(self) -> list[MenuEntity]:
        """获取所有菜单。"""
        ...

    @abstractmethod
    async def get_by_id(self, menu_id: str) -> MenuEntity | None:
        """根据 ID 获取菜单。"""
        ...

    @abstractmethod
    async def create(self, menu: MenuEntity) -> MenuEntity:
        """创建新菜单。"""
        ...

    @abstractmethod
    async def update(self, menu: MenuEntity) -> MenuEntity:
        """更新现有菜单。"""
        ...

    @abstractmethod
    async def delete(self, menu_id: str) -> bool:
        """根据 ID 删除菜单。"""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> MenuEntity | None:
        """根据名称获取菜单。"""
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None) -> list[MenuEntity]:
        """根据父菜单 ID 获取子菜单。"""
        ...

    @abstractmethod
    async def create_meta(self, meta: MenuMetaEntity) -> MenuMetaEntity:
        """创建菜单元数据。"""
        ...

    @abstractmethod
    async def update_meta(self, meta: MenuMetaEntity) -> MenuMetaEntity:
        """更新菜单元数据。"""
        ...

    @abstractmethod
    async def get_meta_by_id(self, meta_id: str) -> MenuMetaEntity | None:
        """根据 ID 获取菜单元数据。"""
        ...

    @abstractmethod
    async def delete_meta(self, meta_id: str) -> bool:
        """根据 ID 删除菜单元数据。"""
        ...
