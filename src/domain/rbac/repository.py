"""RBAC 领域 - 仓库接口。"""

from abc import ABC, abstractmethod

from src.domain.rbac.entities import Permission, Role


class RoleRepositoryInterface(ABC):
    """角色的抽象仓库接口。"""

    @abstractmethod
    async def get_by_id(self, role_id: str) -> Role | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Role | None: ...

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Role]: ...

    @abstractmethod
    async def create(self, role: Role) -> Role: ...

    @abstractmethod
    async def update(self, role: Role) -> Role: ...

    @abstractmethod
    async def delete(self, role_id: str) -> bool: ...

    @abstractmethod
    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool: ...

    @abstractmethod
    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool: ...

    @abstractmethod
    async def get_user_roles(self, user_id: str) -> list[Role]: ...


class PermissionRepositoryInterface(ABC):
    """权限的抽象仓库接口。"""

    @abstractmethod
    async def get_by_id(self, permission_id: str) -> Permission | None: ...

    @abstractmethod
    async def get_by_codename(self, codename: str) -> Permission | None: ...

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Permission]: ...

    @abstractmethod
    async def create(self, permission: Permission) -> Permission: ...

    @abstractmethod
    async def delete(self, permission_id: str) -> bool: ...

    @abstractmethod
    async def get_permissions_by_role(self, role_id: str) -> list[Permission]: ...

    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> list[Permission]: ...
