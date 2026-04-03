"""菜单领域 - 仓储接口。

定义菜单仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from src.infrastructure.database.models import Menu


class MenuRepositoryInterface(ABC):
    """菜单领域的抽象仓储接口。"""

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> list["Menu"]:
        """获取所有菜单。

        Args:
            session: 数据库会话

        Returns:
            菜单列表
        """
        ...

    @abstractmethod
    async def get_by_id(self, menu_id: str, session: AsyncSession) -> "Menu | None":
        """根据 ID 获取菜单。

        Args:
            menu_id: 菜单ID
            session: 数据库会话

        Returns:
            菜单对象或 None
        """
        ...

    @abstractmethod
    async def create(self, menu: "Menu", session: AsyncSession) -> "Menu":
        """创建新菜单。

        Args:
            menu: 菜单对象
            session: 数据库会话

        Returns:
            创建后的菜单对象
        """
        ...

    @abstractmethod
    async def update(self, menu: "Menu", session: AsyncSession) -> "Menu":
        """更新现有菜单。

        Args:
            menu: 菜单对象
            session: 数据库会话

        Returns:
            更新后的菜单对象
        """
        ...

    @abstractmethod
    async def delete(self, menu_id: str, session: AsyncSession) -> bool:
        """根据 ID 删除菜单。

        Args:
            menu_id: 菜单ID
            session: 数据库会话

        Returns:
            是否删除成功
        """
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list["Menu"]:
        """根据父菜单 ID 获取子菜单。

        Args:
            parent_id: 父菜单ID，None 表示获取顶级菜单
            session: 数据库会话

        Returns:
            子菜单列表
        """
        ...
