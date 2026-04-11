"""使用 SQLModel 和 FastCRUD 实现的菜单仓库。"""

from fastcrud import FastCRUD
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.infrastructure.database.models import Menu


class MenuRepository(MenuRepositoryInterface):
    """MenuRepositoryInterface 的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self) -> None:
        """初始化菜单仓储。"""
        self._crud = FastCRUD(Menu)

    async def get_all(self, session: AsyncSession) -> list[Menu]:
        """获取所有菜单，按排序号排序。

        Args:
            session: 数据库会话

        Returns:
            菜单列表
        """
        result = await self._crud.get_multi(session, schema_to_select=Menu, return_as_model=True, return_total_count=False)
        menus = result.get("data", [])
        # 按 order_num 排序
        return sorted(menus, key=lambda m: m.order_num)

    async def get_by_id(self, menu_id: str, session: AsyncSession) -> Menu | None:
        """根据 ID 获取菜单。

        Args:
            menu_id: 菜单ID
            session: 数据库会话

        Returns:
            菜单对象或 None
        """
        return await self._crud.get(session, id=menu_id, schema_to_select=Menu, return_as_model=True)

    async def create(self, menu: Menu, session: AsyncSession) -> Menu:
        """创建新菜单。

        Args:
            menu: 菜单对象
            session: 数据库会话

        Returns:
            创建后的菜单对象
        """
        return await self._crud.create(session, menu)

    async def update(self, menu: Menu, session: AsyncSession) -> Menu:
        """更新现有菜单。

        Args:
            menu: 菜单对象
            session: 数据库会话

        Returns:
            更新后的菜单对象
        """
        return await self._crud.update(session, menu)

    async def delete(self, menu_id: str, session: AsyncSession) -> bool:
        """根据 ID 删除菜单。

        Args:
            menu_id: 菜单ID
            session: 数据库会话

        Returns:
            是否删除成功
        """
        deleted_count = await self._crud.delete(session, id=menu_id)
        return deleted_count > 0

    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list[Menu]:
        """根据父菜单 ID 获取子菜单，按排序号排序。

        Args:
            parent_id: 父菜单ID
            session: 数据库会话

        Returns:
            子菜单列表
        """
        result = await self._crud.get_multi(session, parent_id=parent_id, schema_to_select=Menu, return_as_model=True, return_total_count=False)
        menus = result.get("data", [])
        # 按 order_num 排序
        return sorted(menus, key=lambda m: m.order_num)
