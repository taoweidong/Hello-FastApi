"""使用 SQLModel 原生 API 实现的菜单仓库。

设计原则：
- 基础 CRUD 使用基类实现
- 按字段查询（name, parent_id）使用通用方法
- 菜单树形结构、层级操作保留在仓储层
- 元数据（MenuMeta）操作内聚在此层
"""

from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.infrastructure.database.models import Menu, MenuMeta, RoleMenuLink
from src.infrastructure.repositories.base import GenericRepository


class MenuRepository(GenericRepository[Menu, MenuEntity], MenuRepositoryInterface):
    """MenuRepositoryInterface 的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[Menu]:
        return Menu

    def _to_domain(self, model: Menu) -> MenuEntity:
        return model.to_domain()

    def _from_domain(self, entity: MenuEntity) -> Menu:
        return Menu.from_domain(entity)

    # ========== 自定义查询（仓库层）==========

    async def get_all(self) -> list[MenuEntity]:
        """获取所有菜单，按排序号排序。"""
        stmt = select(Menu).options(selectinload(Menu.meta)).order_by(Menu.rank)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return sorted([self._to_domain(m) for m in items], key=lambda m: m.rank)

    async def get_by_id(self, menu_id: str) -> MenuEntity | None:
        """根据 ID 获取菜单（包含元数据）。"""
        stmt = select(Menu).where(Menu.id == menu_id).options(selectinload(Menu.meta))
        result = await self.session.exec(stmt)
        model = result.first()
        return model.to_domain() if model else None

    async def get_by_name(self, name: str) -> MenuEntity | None:
        """根据名称获取菜单。"""
        return await self.get_one_by("name", name)

    async def get_by_parent_id(self, parent_id: str | None) -> list[MenuEntity]:
        """根据父菜单 ID 获取子菜单，按排序号排序。"""
        stmt = select(Menu).where(Menu.parent_id == parent_id).order_by(Menu.rank)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return sorted([self._to_domain(m) for m in items], key=lambda m: m.rank)

    async def count(self, parent_id: str | None = None, is_active: int | None = None) -> int:
        """获取菜单总数（支持筛选）。"""
        filters: dict[str, Any] = {}
        if parent_id is not None:
            filters["parent_id"] = parent_id
        if is_active is not None:
            filters["is_active"] = is_active
        return await super().count(**filters)

    # ========== 树形结构操作（仓库层职责）==========

    async def delete(self, menu_id: str) -> bool:
        """根据 ID 删除菜单。

        包含复杂的关联清理：
        1. 清除菜单的角色关联
        2. 将子菜单的 parent_id 置空
        3. 删除菜单本身
        4. 删除关联的 MenuMeta
        """
        menu = await self.get_by_id(menu_id)
        meta_id = menu.meta_id if menu else None

        # 1. 清除菜单的角色关联
        stmt1 = sa_delete(RoleMenuLink).where(RoleMenuLink.menu_id == menu_id)
        await self.session.exec(stmt1)  # type: ignore[arg-type]
        await self.session.flush()

        # 2. 将子菜单的 parent_id 置空
        stmt2 = sa_update(Menu).where(Menu.parent_id == menu_id).values(parent_id=None)
        await self.session.exec(stmt2)  # type: ignore[arg-type]
        await self.session.flush()

        # 3. 删除菜单
        stmt3 = sa_delete(Menu).where(Menu.id == menu_id)
        result = await self.session.exec(stmt3)  # type: ignore[arg-type]
        await self.session.flush()

        # 4. 删除关联的 MenuMeta
        if meta_id:
            await self.delete_meta(meta_id)

        return result.rowcount > 0  # type: ignore[union-attr]

    # ========== MenuMeta 操作（内聚在此层）==========

    async def create_meta(self, meta: MenuMetaEntity) -> MenuMetaEntity:
        """创建菜单元数据。"""
        model = MenuMeta.from_domain(meta)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return await self.get_meta_by_id(model.id)  # type: ignore[return-value]

    async def update_meta(self, meta: MenuMetaEntity) -> MenuMetaEntity:
        """更新菜单元数据。"""
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
        return await self.get_meta_by_id(meta.id)  # type: ignore[return-value]

    async def get_meta_by_id(self, meta_id: str) -> MenuMetaEntity | None:
        """根据 ID 获取菜单元数据。"""
        stmt = select(MenuMeta).where(MenuMeta.id == meta_id)
        result = await self.session.exec(stmt)
        model = result.first()
        return model.to_domain() if model else None

    async def delete_meta(self, meta_id: str) -> bool:
        """根据 ID 删除菜单元数据。"""
        stmt = sa_delete(MenuMeta).where(MenuMeta.id == meta_id)
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
