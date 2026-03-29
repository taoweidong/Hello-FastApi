"""菜单领域 - 仓储接口。

定义菜单仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod

from src.infrastructure.database.models import Menu


class MenuRepositoryInterface(ABC):
    """菜单领域的抽象仓储接口。"""

    @abstractmethod
    async def get_all(self, session) -> list[Menu]:
        """获取所有菜单。"""
        ...

    @abstractmethod
    async def get_by_id(self, menu_id: str, session) -> Menu | None:
        """根据 ID 获取菜单。"""
        ...

    @abstractmethod
    async def create(self, menu: Menu, session) -> Menu:
        """创建新菜单。"""
        ...

    @abstractmethod
    async def update(self, menu: Menu, session) -> Menu:
        """更新现有菜单。"""
        ...

    @abstractmethod
    async def delete(self, menu_id: str, session) -> bool:
        """根据 ID 删除菜单。"""
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None, session) -> list[Menu]:
        """根据父菜单 ID 获取子菜单。"""
        ...
