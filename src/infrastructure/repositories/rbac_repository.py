"""使用 SQLModel 实现的 RBAC 仓库。"""

from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.rbac.repository import PermissionRepositoryInterface, RoleRepositoryInterface
from src.infrastructure.database.models import Permission, Role, RolePermissionLink, UserRole


class RoleRepository(RoleRepositoryInterface):
    """RoleRepositoryInterface 的 SQLModel 实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, role_id: str) -> Role | None:
        result = await self.session.exec(select(Role).where(Role.id == role_id))
        return result.one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.exec(select(Role).where(Role.name == name))
        return result.one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Role]:
        result = await self.session.exec(select(Role).offset(skip).limit(limit))
        return list(result.all())

    async def create(self, role: Role) -> Role:
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def update(self, role: Role) -> Role:
        await self.session.merge(role)
        await self.session.flush()
        return role

    async def delete(self, role_id: str) -> bool:
        role = await self.get_by_id(role_id)
        if role is None:
            return False
        await self.session.delete(role)
        await self.session.flush()
        return True

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
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
        stmt = delete(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        result = await self.session.execute(stmt)
        # DML 语句返回的 CursorResult 具有 rowcount 属性
        return bool(getattr(result, "rowcount", 0) > 0)

    async def get_user_roles(self, user_id: str) -> list[Role]:
        result = await self.session.exec(
            select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        )
        return list(result.all())


class PermissionRepository(PermissionRepositoryInterface):
    """PermissionRepositoryInterface 的 SQLModel 实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, permission_id: str) -> Permission | None:
        result = await self.session.exec(select(Permission).where(Permission.id == permission_id))
        return result.one_or_none()

    async def get_by_codename(self, codename: str) -> Permission | None:
        result = await self.session.exec(select(Permission).where(Permission.codename == codename))
        return result.one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Permission]:
        result = await self.session.exec(select(Permission).offset(skip).limit(limit))
        return list(result.all())

    async def create(self, permission: Permission) -> Permission:
        self.session.add(permission)
        await self.session.flush()
        await self.session.refresh(permission)
        return permission

    async def delete(self, permission_id: str) -> bool:
        perm = await self.get_by_id(permission_id)
        if perm is None:
            return False
        await self.session.delete(perm)
        await self.session.flush()
        return True

    async def get_permissions_by_role(self, role_id: str) -> list[Permission]:
        result = await self.session.exec(
            select(Permission)
            .join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id)
            .where(RolePermissionLink.role_id == role_id)
        )
        return list(result.all())

    async def get_user_permissions(self, user_id: str) -> list[Permission]:
        result = await self.session.exec(
            select(Permission)
            .join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermissionLink.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        return list(result.all())
