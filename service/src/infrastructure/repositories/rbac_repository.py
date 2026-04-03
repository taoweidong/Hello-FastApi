"""使用 SQLModel 和 FastCRUD 实现的 RBAC 仓库。"""

from sqlalchemy import delete
from fastcrud import FastCRUD
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.rbac_repository import PermissionRepositoryInterface, RoleRepositoryInterface
from src.infrastructure.database.models import Menu, Permission, Role, RoleMenuLink, RolePermissionLink, UserRole


class RoleRepository(RoleRepositoryInterface):
    """RoleRepositoryInterface 的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        """初始化角色仓储。

        Args:
            session: 数据库会话
        """
        self.session = session
        self._crud = FastCRUD(Role)

    async def get_by_id(self, role_id: str) -> Role | None:
        """根据ID获取角色。

        Args:
            role_id: 角色ID

        Returns:
            角色对象或 None
        """
        return await self._crud.get(self.session, id=role_id)

    async def get_by_name(self, name: str) -> Role | None:
        """根据名称获取角色。

        Args:
            name: 角色名称

        Returns:
            角色对象或 None
        """
        return await self._crud.get_one(self.session, name=name)

    async def get_by_code(self, code: str) -> Role | None:
        """根据编码获取角色。

        Args:
            code: 角色编码

        Returns:
            角色对象或 None
        """
        return await self._crud.get_one(self.session, code=code)

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        role_name: str | None = None,
        status: int | None = None,
    ) -> list[Role]:
        """获取角色列表，支持分页和筛选。

        Args:
            page_num: 页码，从1开始
            page_size: 每页数量
            role_name: 角色名称模糊查询
            status: 角色状态

        Returns:
            角色列表
        """
        filters: dict[str, any] = {}
        if role_name:
            filters["name"] = role_name
        if status is not None:
            filters["status"] = status

        result = await self._crud.get_multi(
            self.session,
            offset=(page_num - 1) * page_size,
            limit=page_size,
            **filters,
        )
        return list(result.get("data", []))

    async def count(
        self,
        role_name: str | None = None,
        status: int | None = None,
    ) -> int:
        """获取角色总数，支持筛选。

        Args:
            role_name: 角色名称模糊查询
            status: 角色状态

        Returns:
            角色数量
        """
        filters: dict[str, any] = {}
        if role_name:
            filters["name"] = role_name
        if status is not None:
            filters["status"] = status

        return await self._crud.count(self.session, **filters)

    async def create(self, role: Role) -> Role:
        """创建角色。

        Args:
            role: 角色对象

        Returns:
            创建后的角色对象
        """
        return await self._crud.create(self.session, role)

    async def update(self, role: Role) -> Role:
        """更新角色。

        Args:
            role: 角色对象

        Returns:
            更新后的角色对象
        """
        return await self._crud.update(self.session, role)

    async def delete(self, role_id: str) -> bool:
        """删除角色。

        Args:
            role_id: 角色ID

        Returns:
            是否删除成功
        """
        deleted_count = await self._crud.delete(self.session, id=role_id)
        return deleted_count > 0

    async def assign_permissions_to_role(self, role_id: str, permission_ids: list[str]) -> bool:
        """为角色分配权限（先清除旧权限再分配新的）。

        Args:
            role_id: 角色ID
            permission_ids: 权限ID列表

        Returns:
            是否分配成功
        """
        # 先清除角色的所有旧权限关联
        stmt = delete(RolePermissionLink).where(RolePermissionLink.role_id == role_id)
        await self.session.execute(stmt)

        # 创建新的权限关联
        for perm_id in permission_ids:
            link = RolePermissionLink(role_id=role_id, permission_id=perm_id)
            self.session.add(link)

        await self.session.flush()
        return True

    async def get_role_permissions(self, role_id: str) -> list[Permission]:
        """获取角色的权限列表。

        Args:
            role_id: 角色ID

        Returns:
            权限列表
        """
        result = await self.session.exec(
            select(Permission)
            .join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id)
            .where(RolePermissionLink.role_id == role_id)
        )
        return list(result.all())

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """为用户分配角色。

        Args:
            user_id: 用户ID
            role_id: 角色ID

        Returns:
            是否分配成功
        """
        # 检查是否已分配
        result = await self.session.exec(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        )
        if result.one_or_none() is not None:
            return False

        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.session.add(user_role)
        await self.session.flush()
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """移除用户的角色。

        Args:
            user_id: 用户ID
            role_id: 角色ID

        Returns:
            是否移除成功
        """
        stmt = delete(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0) > 0)

    async def get_user_roles(self, user_id: str) -> list[Role]:
        """获取用户的所有角色。

        Args:
            user_id: 用户ID

        Returns:
            角色列表
        """
        result = await self.session.exec(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return list(result.all())

    async def assign_roles_to_user(self, user_id: str, role_ids: list[str]) -> bool:
        """为用户批量分配角色（先清除旧角色再分配新的）。

        Args:
            user_id: 用户ID
            role_ids: 角色ID列表

        Returns:
            是否分配成功
        """
        # 先清除用户的所有旧角色关联
        stmt = delete(UserRole).where(UserRole.user_id == user_id)
        await self.session.execute(stmt)

        # 创建新的角色关联
        for role_id in role_ids:
            user_role = UserRole(user_id=user_id, role_id=role_id)
            self.session.add(user_role)

        await self.session.flush()
        return True

    async def assign_menus_to_role(self, role_id: str, menu_ids: list[str]) -> bool:
        """为角色分配菜单权限（先清除旧菜单再分配新的）。

        Args:
            role_id: 角色ID
            menu_ids: 菜单ID列表

        Returns:
            是否分配成功
        """
        # 先清除角色的所有旧菜单关联
        stmt = delete(RoleMenuLink).where(RoleMenuLink.role_id == role_id)
        await self.session.execute(stmt)

        # 创建新的菜单关联
        for menu_id in menu_ids:
            link = RoleMenuLink(role_id=role_id, menu_id=menu_id)
            self.session.add(link)

        await self.session.flush()
        return True

    async def get_role_menus(self, role_id: str) -> list[Menu]:
        """获取角色的菜单列表。

        Args:
            role_id: 角色ID

        Returns:
            菜单列表
        """
        result = await self.session.exec(
            select(Menu)
            .join(RoleMenuLink, RoleMenuLink.menu_id == Menu.id)
            .where(RoleMenuLink.role_id == role_id)
        )
        return list(result.all())

    async def get_role_menu_ids(self, role_id: str) -> list[str]:
        """获取角色的菜单ID列表。

        Args:
            role_id: 角色ID

        Returns:
            菜单ID列表
        """
        result = await self.session.exec(
            select(RoleMenuLink.menu_id).where(RoleMenuLink.role_id == role_id)
        )
        return [str(menu_id) for menu_id in result.all()]


class PermissionRepository(PermissionRepositoryInterface):
    """PermissionRepositoryInterface 的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        """初始化权限仓储。

        Args:
            session: 数据库会话
        """
        self.session = session
        self._crud = FastCRUD(Permission)

    async def get_by_id(self, permission_id: str) -> Permission | None:
        """根据ID获取权限。

        Args:
            permission_id: 权限ID

        Returns:
            权限对象或 None
        """
        return await self._crud.get(self.session, id=permission_id)

    async def get_by_code(self, code: str) -> Permission | None:
        """根据编码获取权限。

        Args:
            code: 权限编码

        Returns:
            权限对象或 None
        """
        return await self._crud.get_one(self.session, code=code)

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        permission_name: str | None = None,
    ) -> list[Permission]:
        """获取权限列表，支持分页和筛选。

        Args:
            page_num: 页码，从1开始
            page_size: 每页数量
            permission_name: 权限名称模糊查询

        Returns:
            权限列表
        """
        filters: dict[str, any] = {}
        if permission_name:
            filters["name"] = permission_name

        result = await self._crud.get_multi(
            self.session,
            offset=(page_num - 1) * page_size,
            limit=page_size,
            **filters,
        )
        return list(result.get("data", []))

    async def count(self, permission_name: str | None = None) -> int:
        """获取权限总数，支持筛选。

        Args:
            permission_name: 权限名称模糊查询

        Returns:
            权限数量
        """
        filters: dict[str, any] = {}
        if permission_name:
            filters["name"] = permission_name

        return await self._crud.count(self.session, **filters)

    async def create(self, permission: Permission) -> Permission:
        """创建权限。

        Args:
            permission: 权限对象

        Returns:
            创建后的权限对象
        """
        return await self._crud.create(self.session, permission)

    async def delete(self, permission_id: str) -> bool:
        """删除权限。

        Args:
            permission_id: 权限ID

        Returns:
            是否删除成功
        """
        deleted_count = await self._crud.delete(self.session, id=permission_id)
        return deleted_count > 0

    async def get_permissions_by_role(self, role_id: str) -> list[Permission]:
        """获取角色的权限列表。

        Args:
            role_id: 角色ID

        Returns:
            权限列表
        """
        result = await self.session.exec(
            select(Permission)
            .join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id)
            .where(RolePermissionLink.role_id == role_id)
        )
        return list(result.all())

    async def get_user_permissions(self, user_id: str) -> list[Permission]:
        """获取用户的所有权限（通过其角色）。

        Args:
            user_id: 用户ID

        Returns:
            权限列表
        """
        result = await self.session.exec(
            select(Permission)
            .join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermissionLink.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        return list(result.all())
