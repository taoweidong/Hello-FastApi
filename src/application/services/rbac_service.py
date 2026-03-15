"""应用层 - RBAC 服务。"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.rbac_dto import (
    PermissionCreateDTO,
    PermissionResponseDTO,
    RoleCreateDTO,
    RoleResponseDTO,
    RoleUpdateDTO,
)
from src.core.exceptions import ConflictError, NotFoundError
from src.infrastructure.database.models import Permission, Role
from src.infrastructure.repositories.rbac_repository import PermissionRepository, RoleRepository


class RBACService:
    """RBAC 操作的应用服务。"""

    def __init__(self, session: AsyncSession):
        self.role_repo = RoleRepository(session)
        self.perm_repo = PermissionRepository(session)

    # --- 角色操作 ---

    async def create_role(self, dto: RoleCreateDTO) -> RoleResponseDTO:
        """创建新角色。"""
        if await self.role_repo.get_by_name(dto.name):
            raise ConflictError(f"Role '{dto.name}' already exists")

        role = Role(name=dto.name, description=dto.description)
        role = await self.role_repo.create(role)
        return self._role_to_response(role)

    async def get_role(self, role_id: str) -> RoleResponseDTO:
        """根据 ID 获取角色。"""
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"Role with id '{role_id}' not found")
        return self._role_to_response(role)

    async def get_roles(self, skip: int = 0, limit: int = 100) -> list[RoleResponseDTO]:
        """获取所有角色。"""
        roles = await self.role_repo.get_all(skip=skip, limit=limit)
        return [self._role_to_response(r) for r in roles]

    async def update_role(self, role_id: str, dto: RoleUpdateDTO) -> RoleResponseDTO:
        """更新角色。"""
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"Role with id '{role_id}' not found")

        if dto.name is not None:
            existing = await self.role_repo.get_by_name(dto.name)
            if existing and existing.id != role_id:
                raise ConflictError(f"Role '{dto.name}' already exists")
            role.name = dto.name
        if dto.description is not None:
            role.description = dto.description

        role = await self.role_repo.update(role)
        return self._role_to_response(role)

    async def delete_role(self, role_id: str) -> bool:
        """删除角色。"""
        if not await self.role_repo.delete(role_id):
            raise NotFoundError(f"Role with id '{role_id}' not found")
        return True

    # --- 权限操作 ---

    async def create_permission(self, dto: PermissionCreateDTO) -> PermissionResponseDTO:
        """创建新权限。"""
        if await self.perm_repo.get_by_codename(dto.codename):
            raise ConflictError(f"Permission '{dto.codename}' already exists")

        permission = Permission(
            name=dto.name, codename=dto.codename, description=dto.description, resource=dto.resource, action=dto.action
        )
        permission = await self.perm_repo.create(permission)
        return self._perm_to_response(permission)

    async def get_permissions(self, skip: int = 0, limit: int = 100) -> list[PermissionResponseDTO]:
        """获取所有权限。"""
        perms = await self.perm_repo.get_all(skip=skip, limit=limit)
        return [self._perm_to_response(p) for p in perms]

    async def delete_permission(self, permission_id: str) -> bool:
        """删除权限。"""
        if not await self.perm_repo.delete(permission_id):
            raise NotFoundError(f"Permission with id '{permission_id}' not found")
        return True

    # --- 分配操作 ---

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """为用户分配角色。"""
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"Role with id '{role_id}' not found")

        if not await self.role_repo.assign_role_to_user(user_id, role_id):
            raise ConflictError("Role already assigned to user")
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """移除用户的角色。"""
        if not await self.role_repo.remove_role_from_user(user_id, role_id):
            raise NotFoundError("Role assignment not found")
        return True

    async def get_user_roles(self, user_id: str) -> list[RoleResponseDTO]:
        """获取用户的所有角色。"""
        roles = await self.role_repo.get_user_roles(user_id)
        return [self._role_to_response(r) for r in roles]

    async def get_user_permissions(self, user_id: str) -> list[PermissionResponseDTO]:
        """获取用户的所有权限（通过其角色）。"""
        perms = await self.perm_repo.get_user_permissions(user_id)
        return [self._perm_to_response(p) for p in perms]

    async def check_permission(self, user_id: str, codename: str) -> bool:
        """检查用户是否具有特定权限。"""
        perms = await self.perm_repo.get_user_permissions(user_id)
        return any(p.codename == codename for p in perms)

    # --- 辅助方法 ---

    @staticmethod
    def _role_to_response(role: Role) -> RoleResponseDTO:
        perms = [p.codename for p in role.permissions] if role.permissions else []
        return RoleResponseDTO(
            id=role.id, name=role.name, description=role.description, permissions=perms, created_at=role.created_at
        )

    @staticmethod
    def _perm_to_response(perm: Permission) -> PermissionResponseDTO:
        return PermissionResponseDTO(
            id=perm.id,
            name=perm.name,
            codename=perm.codename,
            description=perm.description,
            resource=perm.resource,
            action=perm.action,
            created_at=perm.created_at,
        )
