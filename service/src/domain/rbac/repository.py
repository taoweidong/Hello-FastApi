"""RBAC 领域 - 仓库接口。"""

from abc import ABC, abstractmethod

from src.infrastructure.database.models import Permission, Role


class RoleRepositoryInterface(ABC):
    """角色的抽象仓库接口。"""

    @abstractmethod
    async def get_by_id(self, role_id: str) -> Role | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Role | None: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Role | None: ...

    @abstractmethod
    async def get_all(self, page_num: int = 1, page_size: int = 10, role_name: str = None, status: int = None) -> list[Role]: ...

    @abstractmethod
    async def count(self, role_name: str = None, status: int = None) -> int: ...

    @abstractmethod
    async def create(self, role: Role) -> Role: ...

    @abstractmethod
    async def update(self, role: Role) -> Role: ...

    @abstractmethod
    async def delete(self, role_id: str) -> bool: ...

    @abstractmethod
    async def assign_permissions_to_role(self, role_id: str, permission_ids: list[str]) -> bool: ...

    @abstractmethod
    async def get_role_permissions(self, role_id: str) -> list[Permission]: ...

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
    async def get_by_code(self, code: str) -> Permission | None: ...

    @abstractmethod
    async def get_all(self, page_num: int = 1, page_size: int = 10, permission_name: str = None) -> list[Permission]: ...

    @abstractmethod
    async def count(self, permission_name: str = None) -> int: ...

    @abstractmethod
    async def create(self, permission: Permission) -> Permission: ...

    @abstractmethod
    async def delete(self, permission_id: str) -> bool: ...

    @abstractmethod
    async def get_permissions_by_role(self, role_id: str) -> list[Permission]: ...

    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> list[Permission]: ...
