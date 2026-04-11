"""使用 SQLModel 和 FastCRUD 实现的菜单仓库。"""

from fastcrud import FastCRUD
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.infrastructure.database.models import Menu


class MenuRepository(MenuRepositoryInterface):
    """MenuRepositoryInterface 的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        """初始化菜单仓储。

        Args:
            session: 数据库会话
        """
        self.session = session
        self._crud = FastCRUD(Menu)

    async def get_all(self) -> list[Menu]:
        """获取所有菜单，按排序号排序。

        Returns:
            菜单列表
        """
        result = await self._crud.get_multi(self.session, schema_to_select=Menu, return_as_model=True, return_total_count=False)
        menus = result.get("data", [])
        # 按 order_num 排序
        return sorted(menus, key=lambda m: m.order_num)

    async def get_by_id(self, menu_id: str) -> Menu | None:
        """根据 ID 获取菜单。

        Args:
            menu_id: 菜单ID

        Returns:
            菜单对象或 None
        """
        return await self._crud.get(self.session, id=menu_id, schema_to_select=Menu, return_as_model=True)

    async def create(self, menu: Menu) -> Menu:
        """创建新菜单。

        Args:
            menu: 菜单对象

        Returns:
            创建后的菜单对象
        """
        return await self._crud.create(self.session, menu)

    async def update(self, menu: Menu) -> Menu:
        """更新现有菜单。

        Args:
            menu: 菜单对象

        Returns:
            更新后的菜单对象
        """
        from sqlalchemy import update as sa_update

        stmt = (
            sa_update(Menu)
            .where(Menu.id == menu.id)
            .values(
                name=menu.name,
                path=menu.path,
                component=menu.component,
                icon=menu.icon,
                title=menu.title,
                show_link=menu.show_link,
                parent_id=menu.parent_id,
                order_num=menu.order_num,
                permissions=menu.permissions,
                status=menu.status,
                menu_type=menu.menu_type,
                redirect=menu.redirect,
                extra_icon=menu.extra_icon,
                enter_transition=menu.enter_transition,
                leave_transition=menu.leave_transition,
                active_path=menu.active_path,
                frame_src=menu.frame_src,
                frame_loading=menu.frame_loading,
                keep_alive=menu.keep_alive,
                hidden_tag=menu.hidden_tag,
                fixed_tag=menu.fixed_tag,
                show_parent=menu.show_parent,
            )
        )
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(menu.id)
        return updated  # type: ignore[return-value]

    async def delete(self, menu_id: str) -> bool:
        """根据 ID 删除菜单（先清除关联的 RoleMenuLink，并将子菜单的 parent_id 置空）。

        Args:
            menu_id: 菜单ID

        Returns:
            是否删除成功
        """
        from sqlalchemy import delete as sa_delete
        from sqlalchemy import update as sa_update

        from src.infrastructure.database.models import RoleMenuLink

        # 先清除菜单的角色关联
        stmt = sa_delete(RoleMenuLink).where(RoleMenuLink.menu_id == menu_id)
        await self.session.execute(stmt)
        await self.session.flush()

        # 将子菜单的 parent_id 置空（解除自引用外键约束）
        child_update = sa_update(Menu).where(Menu.parent_id == menu_id).values(parent_id=None)
        await self.session.execute(child_update)
        await self.session.flush()

        # 使用 SQLAlchemy delete 语句替代 FastCRUD delete，避免 detached 对象问题
        stmt = sa_delete(Menu).where(Menu.id == menu_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def get_by_parent_id(self, parent_id: str | None) -> list[Menu]:
        """根据父菜单 ID 获取子菜单，按排序号排序。

        Args:
            parent_id: 父菜单ID

        Returns:
            子菜单列表
        """
        result = await self._crud.get_multi(self.session, parent_id=parent_id, schema_to_select=Menu, return_as_model=True, return_total_count=False)
        menus = result.get("data", [])
        # 按 order_num 排序
        return sorted(menus, key=lambda m: m.order_num)
