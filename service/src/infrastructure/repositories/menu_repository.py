"""使用 SQLModel 和 FastCRUD 实现的菜单仓库。"""

from fastcrud import FastCRUD
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.infrastructure.database.models import Menu, MenuMeta


class MenuRepository(MenuRepositoryInterface):
    """MenuRepositoryInterface 的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(Menu)
        self._meta_crud = FastCRUD(MenuMeta)

    # ============ 菜单 CRUD ============

    async def get_all(self) -> list[MenuEntity]:
        """获取所有菜单，按排序号排序。"""
        result = await self.session.exec(select(Menu).options(selectinload(Menu.meta)))
        menus = result.all()
        return sorted([m.to_domain() for m in menus], key=lambda m: m.rank)

    async def get_by_id(self, menu_id: str) -> MenuEntity | None:
        """根据 ID 获取菜单。"""
        result = await self.session.exec(select(Menu).where(Menu.id == menu_id).options(selectinload(Menu.meta)))
        menu = result.first()
        return menu.to_domain() if menu else None

    async def create(self, menu: MenuEntity) -> MenuEntity:
        """创建新菜单。"""
        model = Menu.from_domain(menu)
        self.session.add(model)
        await self.session.flush()
        # 读回以获取自动生成的字段和关联的 meta
        loaded = await self.get_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update(self, menu: MenuEntity) -> MenuEntity:
        """更新现有菜单。"""
        from sqlalchemy import update as sa_update

        stmt = (
            sa_update(Menu)
            .where(Menu.id == menu.id)
            .values(
                menu_type=menu.menu_type,
                name=menu.name,
                rank=menu.rank,
                path=menu.path,
                component=menu.component,
                is_active=menu.is_active,
                method=menu.method,
                creator_id=menu.creator_id,
                modifier_id=menu.modifier_id,
                parent_id=menu.parent_id,
                meta_id=menu.meta_id,
                description=menu.description,
            )
        )
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(menu.id)
        return updated  # type: ignore[return-value]

    async def delete(self, menu_id: str) -> bool:
        """根据 ID 删除菜单（先清除关联的 RoleMenuLink，并将子菜单的 parent_id 置空，删除关联的 MenuMeta）。"""
        from sqlalchemy import delete as sa_delete
        from sqlalchemy import update as sa_update

        from src.infrastructure.database.models import RoleMenuLink

        # 先获取菜单（用于删除关联的MenuMeta）
        menu = await self.get_by_id(menu_id)
        meta_id = menu.meta_id if menu else None

        # 清除菜单的角色关联
        stmt = sa_delete(RoleMenuLink).where(RoleMenuLink.menu_id == menu_id)
        await self.session.execute(stmt)
        await self.session.flush()

        # 将子菜单的 parent_id 置空
        child_update = sa_update(Menu).where(Menu.parent_id == menu_id).values(parent_id=None)
        await self.session.execute(child_update)
        await self.session.flush()

        # 删除菜单
        stmt = sa_delete(Menu).where(Menu.id == menu_id)
        result = await self.session.execute(stmt)
        await self.session.flush()

        # 删除关联的MenuMeta
        if meta_id:
            await self.delete_meta(meta_id)

        return result.rowcount > 0  # type: ignore[union-attr]

    async def get_by_name(self, name: str) -> MenuEntity | None:
        """根据名称获取菜单。"""
        model = await self._crud.get(self.session, name=name, schema_to_select=Menu, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_parent_id(self, parent_id: str | None) -> list[MenuEntity]:
        """根据父菜单 ID 获取子菜单，按排序号排序。"""
        result = await self._crud.get_multi(
            self.session, parent_id=parent_id, schema_to_select=Menu, return_as_model=True, return_total_count=False
        )
        menus = result.get("data", [])
        return sorted([m.to_domain() for m in menus], key=lambda m: m.rank)

    # ============ MenuMeta CRUD ============

    async def create_meta(self, meta: MenuMetaEntity) -> MenuMetaEntity:
        """创建菜单元数据。"""
        model = MenuMeta.from_domain(meta)
        self.session.add(model)
        await self.session.flush()
        # 读回以获取自动生成的字段
        loaded = await self.get_meta_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update_meta(self, meta: MenuMetaEntity) -> MenuMetaEntity:
        """更新菜单元数据。"""
        from sqlalchemy import update as sa_update

        stmt = (
            sa_update(MenuMeta)
            .where(MenuMeta.id == meta.id)
            .values(
                title=meta.title,
                icon=meta.icon,
                r_svg_name=meta.r_svg_name,
                is_show_menu=meta.is_show_menu,
                is_show_parent=meta.is_show_parent,
                is_keepalive=meta.is_keepalive,
                frame_url=meta.frame_url,
                frame_loading=meta.frame_loading,
                transition_enter=meta.transition_enter,
                transition_leave=meta.transition_leave,
                is_hidden_tag=meta.is_hidden_tag,
                fixed_tag=meta.fixed_tag,
                dynamic_level=meta.dynamic_level,
                creator_id=meta.creator_id,
                modifier_id=meta.modifier_id,
                description=meta.description,
            )
        )
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_meta_by_id(meta.id)
        return updated  # type: ignore[return-value]

    async def get_meta_by_id(self, meta_id: str) -> MenuMetaEntity | None:
        """根据 ID 获取菜单元数据。"""
        model = await self._meta_crud.get(self.session, id=meta_id, schema_to_select=MenuMeta, return_as_model=True)
        return model.to_domain() if model else None

    async def delete_meta(self, meta_id: str) -> bool:
        """根据 ID 删除菜单元数据。"""
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(MenuMeta).where(MenuMeta.id == meta_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
