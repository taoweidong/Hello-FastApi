"""权限仓储接口。

定义权限仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.database.models import Permission


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
    async def get_all(
        self, page_num: int = 1, page_size: int = 10, permission_name: str = None
    ) -> list["Permission"]:
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
