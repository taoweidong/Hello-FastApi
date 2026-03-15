"""使用 SQLAlchemy 实现的 RBAC 仓库。"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.rbac.repository import PermissionRepositoryInterface, RoleRepositoryInterface
from src.infrastructure.database.models import Permission, Role, UserRole, role_permissions


class RoleRepository(RoleRepositoryInterface):
    """RoleRepositoryInterface 的 SQLAlchemy 实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, role_id: str) -> Role | None:
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Role]:
        stmt = select(Role).options(selectinload(Role.permissions)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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
        stmt = select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return False

        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.session.add(user_role)
        await self.session.flush()
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        stmt = delete(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_user_roles(self, user_id: str) -> list[Role]:
        stmt = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .options(selectinload(Role.permissions))
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PermissionRepository(PermissionRepositoryInterface):
    """PermissionRepositoryInterface 的 SQLAlchemy 实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, permission_id: str) -> Permission | None:
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codename(self, codename: str) -> Permission | None:
        stmt = select(Permission).where(Permission.codename == codename)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Permission]:
        stmt = select(Permission).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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
        stmt = (
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == role_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_permissions(self, user_id: str) -> list[Permission]:
        stmt = (
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == role_permissions.c.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
