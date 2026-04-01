"""使用 SQLModel 实现的 RBAC 仓库。"""

from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.rbac.repository import PermissionRepositoryInterface, RoleRepositoryInterface
from src.infrastructure.database.models import Menu, Permission, Role, RoleMenuLink, RolePermissionLink, UserRole


class RoleRepository(RoleRepositoryInterface):
    """RoleRepositoryInterface 的 SQLModel 实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, role_id: str) -> Role | None:
        """根据ID获取角色。"""
        result = await self.session.exec(select(Role).where(Role.id == role_id))
        return result.one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        """根据名称获取角色。"""
        result = await self.session.exec(select(Role).where(Role.name == name))
        return result.one_or_none()

    async def get_by_code(self, code: str) -> Role | None:
        """根据编码获取角色。"""
        result = await self.session.exec(select(Role).where(Role.code == code))
        return result.one_or_none()

    async def get_all(self, page_num: int = 1, page_size: int = 10, role_name: str = None, status: int = None) -> list[Role]:
        """获取角色列表，支持分页和筛选。"""
        query = select(Role)

        # 应用筛选条件
        if role_name:
            query = query.where(Role.name.contains(role_name))
        if status is not None:
            query = query.where(Role.status == status)

        # 分页
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.exec(query)
        return list(result.all())

    async def count(self, role_name: str = None, status: int = None) -> int:
        """获取角色总数，支持筛选。"""
        query = select(Role)

        # 应用筛选条件
        if role_name:
            query = query.where(Role.name.contains(role_name))
        if status is not None:
            query = query.where(Role.status == status)

        result = await self.session.exec(query)
        return len(result.all())

    async def create(self, role: Role) -> Role:
        """创建角色。"""
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def update(self, role: Role) -> Role:
        """更新角色。"""
        await self.session.merge(role)
        await self.session.flush()
        return role

    async def delete(self, role_id: str) -> bool:
        """删除角色。"""
        role = await self.get_by_id(role_id)
        if role is None:
            return False
        await self.session.delete(role)
        await self.session.flush()
        return True

    async def assign_permissions_to_role(self, role_id: str, permission_ids: list[str]) -> bool:
        """为角色分配权限（先清除旧权限再分配新的）。"""
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
        """获取角色的权限列表。"""
        result = await self.session.exec(select(Permission).join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id).where(RolePermissionLink.role_id == role_id))
        return list(result.all())

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """为用户分配角色。"""
        # 检查是否已分配
        result = await self.session.exec(select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id))
        if result.one_or_none() is not None:
            return False

        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.session.add(user_role)
        await self.session.flush()
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """移除用户的角色。"""
        stmt = delete(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        result = await self.session.execute(stmt)
        # DML 语句返回的 CursorResult 具有 rowcount 属性
        return bool(getattr(result, "rowcount", 0) > 0)

    async def get_user_roles(self, user_id: str) -> list[Role]:
        """获取用户的所有角色。"""
        result = await self.session.exec(select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id))
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

    # ============ 角色-菜单关联 ============

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
        result = await self.session.exec(select(Menu).join(RoleMenuLink, RoleMenuLink.menu_id == Menu.id).where(RoleMenuLink.role_id == role_id))
        return list(result.all())

    async def get_role_menu_ids(self, role_id: str) -> list[str]:
        """获取角色的菜单ID列表。

        Args:
            role_id: 角色ID

        Returns:
            菜单ID列表
        """
        result = await self.session.exec(select(RoleMenuLink.menu_id).where(RoleMenuLink.role_id == role_id))
        return [str(menu_id) for menu_id in result.all()]


class PermissionRepository(PermissionRepositoryInterface):
    """PermissionRepositoryInterface 的 SQLModel 实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, permission_id: str) -> Permission | None:
        """根据ID获取权限。"""
        result = await self.session.exec(select(Permission).where(Permission.id == permission_id))
        return result.one_or_none()

    async def get_by_code(self, code: str) -> Permission | None:
        """根据编码获取权限。"""
        result = await self.session.exec(select(Permission).where(Permission.code == code))
        return result.one_or_none()

    async def get_all(self, page_num: int = 1, page_size: int = 10, permission_name: str = None) -> list[Permission]:
        """获取权限列表，支持分页和筛选。"""
        query = select(Permission)

        # 应用筛选条件
        if permission_name:
            query = query.where(Permission.name.contains(permission_name))

        # 分页
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.exec(query)
        return list(result.all())

    async def count(self, permission_name: str = None) -> int:
        """获取权限总数，支持筛选。"""
        query = select(Permission)

        # 应用筛选条件
        if permission_name:
            query = query.where(Permission.name.contains(permission_name))

        result = await self.session.exec(query)
        return len(result.all())

    async def create(self, permission: Permission) -> Permission:
        """创建权限。"""
        self.session.add(permission)
        await self.session.flush()
        await self.session.refresh(permission)
        return permission

    async def delete(self, permission_id: str) -> bool:
        """删除权限。"""
        perm = await self.get_by_id(permission_id)
        if perm is None:
            return False
        await self.session.delete(perm)
        await self.session.flush()
        return True

    async def get_permissions_by_role(self, role_id: str) -> list[Permission]:
        """获取角色的权限列表。"""
        result = await self.session.exec(select(Permission).join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id).where(RolePermissionLink.role_id == role_id))
        return list(result.all())

    async def get_user_permissions(self, user_id: str) -> list[Permission]:
        """获取用户的所有权限（通过其角色）。"""
        result = await self.session.exec(select(Permission).join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id).join(UserRole, UserRole.role_id == RolePermissionLink.role_id).where(UserRole.user_id == user_id).distinct())
        return list(result.all())
