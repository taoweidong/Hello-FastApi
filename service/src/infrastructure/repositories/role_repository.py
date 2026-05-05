"""使用 SQLModel 原生 API 实现的角色仓储。

设计原则：
- 基础 CRUD 使用基类实现
- 按字段查询（name, code）使用 get_one_by
- 角色-用户、角色-菜单关联操作保留（属于数据层关联）
- 复杂业务逻辑（权限验证、继承计算）移至服务层
"""

from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.menu import MenuEntity
from src.domain.entities.role import RoleEntity
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.infrastructure.database.models import Menu, Role, RoleMenuLink, UserRole
from src.infrastructure.repositories.base import GenericRepository


class RoleRepository(GenericRepository[Role, RoleEntity], RoleRepositoryInterface):
    """RoleRepositoryInterface 的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[Role]:
        return Role

    def _to_domain(self, model: Role) -> RoleEntity:
        return model.to_domain()

    def _from_domain(self, entity: RoleEntity) -> Role:
        return Role.from_domain(entity)

    # ========== 覆盖基类方法（类型化参数）==========

    async def get_all(
        self, page_num: int = 1, page_size: int = 10, role_name: str | None = None, is_active: int | None = None
    ) -> list[RoleEntity]:
        """获取角色列表，支持分页和筛选。"""
        filters: dict[str, Any] = {}
        if role_name:
            filters["name"] = role_name
        if is_active is not None:
            filters["is_active"] = is_active
        return await super().get_all(page_num, page_size, **filters)

    async def count(self, role_name: str | None = None, is_active: int | None = None) -> int:
        """获取角色总数，支持筛选。"""
        filters: dict[str, Any] = {}
        if role_name:
            filters["name"] = role_name
        if is_active is not None:
            filters["is_active"] = is_active
        return await super().count(**filters)

    # ========== 自定义查询（使用基类方法）==========

    async def get_by_name(self, name: str) -> RoleEntity | None:
        """根据名称获取角色。"""
        return await self.get_one_by("name", name)

    async def get_by_code(self, code: str) -> RoleEntity | None:
        """根据编码获取角色。"""
        return await self.get_one_by("code", code)

    # ========== 角色-用户关联操作（数据层关联逻辑）==========

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """为用户分配角色。"""
        stmt = select(UserRole).where(UserRole.userinfo_id == user_id, UserRole.userrole_id == role_id)
        result = await self.session.exec(stmt)
        if result.one_or_none() is not None:
            return False
        user_role = UserRole(userinfo_id=user_id, userrole_id=role_id)
        self.session.add(user_role)
        await self.session.flush()
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """移除用户的角色。"""
        stmt = sa_delete(UserRole).where(UserRole.userinfo_id == user_id, UserRole.userrole_id == role_id)
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        return bool(getattr(result, "rowcount", 0) > 0)

    async def get_user_roles(self, user_id: str) -> list[RoleEntity]:
        """获取用户的所有角色。"""
        stmt = select(Role).join(UserRole, UserRole.userrole_id == Role.id).where(UserRole.userinfo_id == user_id)
        result = await self.session.exec(stmt)
        return [self._to_domain(m) for m in result.all()]

    async def assign_roles_to_user(self, user_id: str, role_ids: list[str]) -> bool:
        """为用户批量分配角色（先清除旧角色再分配新的）。"""
        stmt = sa_delete(UserRole).where(UserRole.userinfo_id == user_id)
        await self.session.exec(stmt)  # type: ignore[arg-type]
        for role_id in role_ids:
            user_role = UserRole(userinfo_id=user_id, userrole_id=role_id)
            self.session.add(user_role)
        await self.session.flush()
        return True

    # ========== 角色-菜单关联操作（数据层关联逻辑）==========

    async def assign_menus_to_role(self, role_id: str, menu_ids: list[str]) -> bool:
        """为角色分配菜单权限（先清除旧菜单再分配新的）。"""
        stmt = sa_delete(RoleMenuLink).where(RoleMenuLink.userrole_id == role_id)
        await self.session.exec(stmt)  # type: ignore[arg-type]
        for menu_id in menu_ids:
            link = RoleMenuLink(userrole_id=role_id, menu_id=menu_id)
            self.session.add(link)
        await self.session.flush()
        return True

    async def get_role_menus(self, role_id: str) -> list[MenuEntity]:
        """获取角色的菜单列表。"""
        stmt = (
            select(Menu)
            .join(RoleMenuLink, RoleMenuLink.menu_id == Menu.id)
            .where(RoleMenuLink.userrole_id == role_id)
            .options(selectinload(Menu.meta))
        )
        result = await self.session.exec(stmt)
        return [m.to_domain() for m in result.all()]

    async def get_role_menu_ids(self, role_id: str) -> list[str]:
        """获取角色的菜单ID列表。"""
        stmt = select(RoleMenuLink.menu_id).where(RoleMenuLink.userrole_id == role_id)
        result = await self.session.exec(stmt)
        return [str(menu_id) for menu_id in result.all()]

    async def get_user_all_menus(self, user_id: str) -> list[MenuEntity]:
        """一次查询获取用户所有角色关联的菜单（去重），消除 N+1 问题。"""
        stmt = (
            select(Menu)
            .join(RoleMenuLink, RoleMenuLink.menu_id == Menu.id)
            .join(UserRole, UserRole.userrole_id == RoleMenuLink.userrole_id)
            .where(UserRole.userinfo_id == user_id)
            .options(selectinload(Menu.meta))
        )
        result = await self.session.exec(stmt)
        seen_ids: set[str] = set()
        menus: list[MenuEntity] = []
        for model in result.all():
            if model.id not in seen_ids:
                seen_ids.add(model.id)
                menus.append(model.to_domain())
        return menus

    async def get_users_roles_batch(self, user_ids: list[str]) -> dict[str, list[RoleEntity]]:
        """批量获取多个用户的角色列表。"""
        if not user_ids:
            return {}
        from collections import defaultdict

        stmt = (
            select(Role, UserRole.userinfo_id)
            .join(UserRole, UserRole.userrole_id == Role.id)
            .where(UserRole.userinfo_id.in_(user_ids))
        )
        result = await self.session.exec(stmt)
        rows = result.all()
        roles_map: dict[str, list[RoleEntity]] = defaultdict(list)
        for role_model, userinfo_id in rows:
            roles_map[str(userinfo_id)].append(role_model.to_domain())
        for uid in user_ids:
            if uid not in roles_map:
                roles_map[uid] = []
        return dict(roles_map)

    async def get_roles_menu_ids_batch(self, role_ids: list[str]) -> dict[str, list[str]]:
        """批量获取多个角色的菜单ID列表。"""
        if not role_ids:
            return {}
        from collections import defaultdict

        stmt = select(RoleMenuLink).where(RoleMenuLink.userrole_id.in_(role_ids))
        result = await self.session.exec(stmt)
        links = result.all()
        menu_ids_map: dict[str, list[str]] = defaultdict(list)
        for link in links:
            menu_ids_map[str(link.userrole_id)].append(str(link.menu_id))
        for rid in role_ids:
            if rid not in menu_ids_map:
                menu_ids_map[rid] = []
        return dict(menu_ids_map)
