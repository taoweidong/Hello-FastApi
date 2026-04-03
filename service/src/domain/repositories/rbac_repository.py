"""RBAC 领域 - 仓储接口。

定义角色和权限仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.database.models import Permission, Role


class RoleRepositoryInterface(ABC):
    """角色的抽象仓储接口。"""

    @abstractmethod
    async def get_by_id(self, role_id: str) -> "Role | None":
        """根据 ID 获取角色。"""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> "Role | None":
        """根据名称获取角色。"""
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> "Role | None":
        """根据编码获取角色。"""
        ...

    @abstractmethod
    async def get_all(self, page_num: int = 1, page_size: int = 10, role_name: str = None, status: int = None) -> list["Role"]:
        """获取所有角色（分页）。

        Args:
            page_num: 页码
            page_size: 每页数量
            role_name: 角色名称过滤
            status: 状态过滤

        Returns:
            角色列表
        """
        ...

    @abstractmethod
    async def count(self, role_name: str = None, status: int = None) -> int:
        """统计角色总数。

        Args:
            role_name: 角色名称过滤
            status: 状态过滤

        Returns:
            角色总数
        """
        ...

    @abstractmethod
    async def create(self, role: "Role") -> "Role":
        """创建角色。

        Args:
            role: 角色对象

        Returns:
            创建后的角色对象
        """
        ...

    @abstractmethod
    async def update(self, role: "Role") -> "Role":
        """更新角色。

        Args:
            role: 角色对象

        Returns:
            更新后的角色对象
        """
        ...

    @abstractmethod
    async def delete(self, role_id: str) -> bool:
        """删除角色。

        Args:
            role_id: 角色ID

        Returns:
            是否删除成功
        """
        ...

    @abstractmethod
    async def assign_permissions_to_role(self, role_id: str, permission_ids: list[str]) -> bool:
        """为角色分配权限。

        Args:
            role_id: 角色ID
            permission_ids: 权限ID列表

        Returns:
            是否分配成功
        """
        ...

    @abstractmethod
    async def get_role_permissions(self, role_id: str) -> list["Permission"]:
        """获取角色的权限列表。

        Args:
            role_id: 角色ID

        Returns:
            权限列表
        """
        ...

    @abstractmethod
    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """为用户分配角色。

        Args:
            user_id: 用户ID
            role_id: 角色ID

        Returns:
            是否分配成功
        """
        ...

    @abstractmethod
    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """移除用户的角色。

        Args:
            user_id: 用户ID
            role_id: 角色ID

        Returns:
            是否移除成功
        """
        ...

    @abstractmethod
    async def get_user_roles(self, user_id: str) -> list["Role"]:
        """获取用户的角色列表。

        Args:
            user_id: 用户ID

        Returns:
            角色列表
        """
        ...


class PermissionRepositoryInterface(ABC):
    """权限的抽象仓储接口。"""

    @abstractmethod
    async def get_by_id(self, permission_id: str) -> "Permission | None":
        """根据 ID 获取权限。"""
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> "Permission | None":
        """根据编码获取权限。"""
        ...

    @abstractmethod
    async def get_all(self, page_num: int = 1, page_size: int = 10, permission_name: str = None) -> list["Permission"]:
        """获取所有权限（分页）。

        Args:
            page_num: 页码
            page_size: 每页数量
            permission_name: 权限名称过滤

        Returns:
            权限列表
        """
        ...

    @abstractmethod
    async def count(self, permission_name: str = None) -> int:
        """统计权限总数。

        Args:
            permission_name: 权限名称过滤

        Returns:
            权限总数
        """
        ...

    @abstractmethod
    async def create(self, permission: "Permission") -> "Permission":
        """创建权限。

        Args:
            permission: 权限对象

        Returns:
            创建后的权限对象
        """
        ...

    @abstractmethod
    async def delete(self, permission_id: str) -> bool:
        """删除权限。

        Args:
            permission_id: 权限ID

        Returns:
            是否删除成功
        """
        ...

    @abstractmethod
    async def get_permissions_by_role(self, role_id: str) -> list["Permission"]:
        """获取角色的权限列表。

        Args:
            role_id: 角色ID

        Returns:
            权限列表
        """
        ...

    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> list["Permission"]:
        """获取用户的所有权限（通过角色）。

        Args:
            user_id: 用户ID

        Returns:
            权限列表
        """
        ...
