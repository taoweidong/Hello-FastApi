"""菜单领域 - 仓储接口。

定义菜单仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from src.infrastructure.database.models import Menu, MenuMeta


class MenuRepositoryInterface(ABC):
    """菜单领域的抽象仓储接口。"""

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> list["Menu"]:
        """获取所有菜单。"""
        ...

    @abstractmethod
    async def get_by_id(self, menu_id: str, session: AsyncSession) -> "Menu | None":
        """根据 ID 获取菜单。"""
        ...

    @abstractmethod
    async def create(self, menu: "Menu", session: AsyncSession) -> "Menu":
        """创建新菜单。"""
        ...

    @abstractmethod
    async def update(self, menu: "Menu", session: AsyncSession) -> "Menu":
        """更新现有菜单。"""
        ...

    @abstractmethod
    async def delete(self, menu_id: str, session: AsyncSession) -> bool:
        """根据 ID 删除菜单。"""
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list["Menu"]:
        """根据父菜单 ID 获取子菜单。"""
        ...

    @abstractmethod
    async def create_meta(self, meta: "MenuMeta", session: AsyncSession) -> "MenuMeta":
        """创建菜单元数据。"""
        ...

    @abstractmethod
    async def update_meta(self, meta: "MenuMeta", session: AsyncSession) -> "MenuMeta":
        """更新菜单元数据。"""
        ...

    @abstractmethod
    async def get_meta_by_id(self, meta_id: str, session: AsyncSession) -> "MenuMeta | None":
        """根据 ID 获取菜单元数据。"""
        ...

    @abstractmethod
    async def delete_meta(self, meta_id: str, session: AsyncSession) -> bool:
        """根据 ID 删除菜单元数据。"""
        ...
