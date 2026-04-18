"""角色仓储实现。

使用 SQLModel 和 FastCRUD 实现角色仓储。
"""

from typing import Any

from fastcrud import FastCRUD
from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.menu import MenuEntity
from src.domain.entities.role import RoleEntity
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.infrastructure.database.models import Menu, Role, RoleMenuLink, UserRole


class RoleRepository(RoleRepositoryInterface):
    """RoleRepositoryInterface 的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(Role)

    async def get_by_id(self, role_id: str) -> RoleEntity | None:
        model = await self._crud.get(self.session, id=role_id, schema_to_select=Role, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_name(self, name: str) -> RoleEntity | None:
        model = await self._crud.get(self.session, name=name, schema_to_select=Role, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_code(self, code: str) -> RoleEntity | None:
        model = await self._crud.get(self.session, code=code, schema_to_select=Role, return_as_model=True)
        return model.to_domain() if model else None

    async def get_all(self, page_num: int = 1, page_size: int = 10, role_name: str | None = None, is_active: int | None = None) -> list[RoleEntity]:
        """获取角色列表，支持分页和筛选。"""
        filters: dict[str, Any] = {}
        if role_name:
            filters["name"] = role_name
        if is_active is not None:
            filters["is_active"] = is_active

        result = await self._crud.get_multi(self.session, offset=(page_num - 1) * page_size, limit=page_size, schema_to_select=Role, return_as_model=True, **filters)
        return [m.to_domain() for m in result.get("data", [])]

    async def count(self, role_name: str | None = None, is_active: int | None = None) -> int:
        """获取角色总数，支持筛选。"""
        filters: dict[str, Any] = {}
        if role_name:
            filters["name"] = role_name
        if is_active is not None:
            filters["is_active"] = is_active

        return await self._crud.count(self.session, **filters)

    async def create(self, role: RoleEntity) -> RoleEntity:
        model = Role.from_domain(role)
        self.session.add(model)
        await self.session.flush()
        created = await self.get_by_id(role.id)
        return created  # type: ignore[return-value]

    async def update(self, role: RoleEntity) -> RoleEntity:
        """更新角色。"""
        from sqlalchemy import update as sa_update

        model = Role.from_domain(role)
        stmt = sa_update(Role).where(Role.id == model.id).values(name=model.name, code=model.code, is_active=model.is_active, creator_id=model.creator_id, modifier_id=model.modifier_id, description=model.description)
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(role.id)
        return updated  # type: ignore[return-value]

    async def delete(self, role_id: str) -> bool:
        """删除角色（先清除关联表数据）。"""
        from sqlalchemy import delete as sa_delete

        # 先清除角色的所有关联关系
        stmt1 = sa_delete(RoleMenuLink).where(RoleMenuLink.userrole_id == role_id)
        await self.session.execute(stmt1)
        stmt2 = sa_delete(UserRole).where(UserRole.userrole_id == role_id)
        await self.session.execute(stmt2)
        await self.session.flush()

        stmt = sa_delete(Role).where(Role.id == role_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """为用户分配角色。"""
        result = await self.session.exec(select(UserRole).where(UserRole.userinfo_id == user_id, UserRole.userrole_id == role_id))
        if result.one_or_none() is not None:
            return False

        user_role = UserRole(userinfo_id=user_id, userrole_id=role_id)
        self.session.add(user_role)
        await self.session.flush()
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """移除用户的角色。"""
        stmt = delete(UserRole).where(UserRole.userinfo_id == user_id, UserRole.userrole_id == role_id)
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0) > 0)

    async def get_user_roles(self, user_id: str) -> list[RoleEntity]:
        """获取用户的所有角色。"""
        result = await self.session.exec(select(Role).join(UserRole, UserRole.userrole_id == Role.id).where(UserRole.userinfo_id == user_id))
        return [m.to_domain() for m in result.all()]

    async def assign_roles_to_user(self, user_id: str, role_ids: list[str]) -> bool:
        """为用户批量分配角色（先清除旧角色再分配新的）。"""
        stmt = delete(UserRole).where(UserRole.userinfo_id == user_id)
        await self.session.execute(stmt)

        for role_id in role_ids:
            user_role = UserRole(userinfo_id=user_id, userrole_id=role_id)
            self.session.add(user_role)

        await self.session.flush()
        return True

    async def assign_menus_to_role(self, role_id: str, menu_ids: list[str]) -> bool:
        """为角色分配菜单权限（先清除旧菜单再分配新的）。"""
        stmt = delete(RoleMenuLink).where(RoleMenuLink.userrole_id == role_id)
        await self.session.execute(stmt)

        for menu_id in menu_ids:
            link = RoleMenuLink(userrole_id=role_id, menu_id=menu_id)
            self.session.add(link)

        await self.session.flush()
        return True

    async def get_role_menus(self, role_id: str) -> list[MenuEntity]:
        """获取角色的菜单列表。"""
        from sqlalchemy.orm import selectinload

        stmt = select(Menu).join(RoleMenuLink, RoleMenuLink.menu_id == Menu.id).where(RoleMenuLink.userrole_id == role_id).options(selectinload(Menu.meta))
        result = await self.session.exec(stmt)
        return [m.to_domain() for m in result.all()]

    async def get_role_menu_ids(self, role_id: str) -> list[str]:
        """获取角色的菜单ID列表。"""
        result = await self.session.exec(select(RoleMenuLink.menu_id).where(RoleMenuLink.userrole_id == role_id))
        return [str(menu_id) for menu_id in result.all()]
