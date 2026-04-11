"""权限仓储实现。

使用 SQLModel 和 FastCRUD 实现权限仓储。
"""

from fastcrud import FastCRUD
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.permission_repository import PermissionRepositoryInterface
from src.infrastructure.database.models import Permission, RolePermissionLink, UserRole


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
        return await self._crud.get(self.session, id=permission_id, schema_to_select=Permission, return_as_model=True)

    async def get_by_code(self, code: str) -> Permission | None:
        """根据编码获取权限。

        Args:
            code: 权限编码

        Returns:
            权限对象或 None
        """
        return await self._crud.get(self.session, code=code, schema_to_select=Permission, return_as_model=True)

    async def get_all(self, page_num: int = 1, page_size: int = 10, permission_name: str | None = None) -> list[Permission]:
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

        result = await self._crud.get_multi(self.session, offset=(page_num - 1) * page_size, limit=page_size, schema_to_select=Permission, return_as_model=True, **filters)
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
        result = await self.session.exec(select(Permission).join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id).where(RolePermissionLink.role_id == role_id))
        return list(result.all())

    async def get_user_permissions(self, user_id: str) -> list[Permission]:
        """获取用户的所有权限（通过其角色）。

        Args:
            user_id: 用户ID

        Returns:
            权限列表
        """
        result = await self.session.exec(select(Permission).join(RolePermissionLink, RolePermissionLink.permission_id == Permission.id).join(UserRole, UserRole.role_id == RolePermissionLink.role_id).where(UserRole.user_id == user_id).distinct())
        return list(result.all())
