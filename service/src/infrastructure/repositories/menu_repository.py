"""使用 SQLModel 实现的菜单仓库。"""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.menu.repository import MenuRepositoryInterface
from src.infrastructure.database.models import Menu


class MenuRepository(MenuRepositoryInterface):
    """MenuRepositoryInterface 的 SQLModel 实现。"""

    async def get_all(self, session: AsyncSession) -> list[Menu]:
        """获取所有菜单，按排序号排序。"""
        result = await session.exec(select(Menu).order_by(Menu.order_num))
        return list(result.all())

    async def get_by_id(self, menu_id: str, session: AsyncSession) -> Menu | None:
        """根据 ID 获取菜单。"""
        return await session.get(Menu, menu_id)

    async def create(self, menu: Menu, session: AsyncSession) -> Menu:
        """创建新菜单。"""
        session.add(menu)
        await session.flush()
        await session.refresh(menu)
        return menu

    async def update(self, menu: Menu, session: AsyncSession) -> Menu:
        """更新现有菜单。"""
        merged = await session.merge(menu)
        await session.flush()
        await session.refresh(merged)
        return merged

    async def delete(self, menu_id: str, session: AsyncSession) -> bool:
        """根据 ID 删除菜单。"""
        menu = await self.get_by_id(menu_id, session)
        if menu is None:
            return False
        await session.delete(menu)
        await session.flush()
        return True

    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list[Menu]:
        """根据父菜单 ID 获取子菜单，按排序号排序。"""
        query = select(Menu).where(Menu.parent_id == parent_id).order_by(Menu.order_num)
        result = await session.exec(query)
        return list(result.all())
