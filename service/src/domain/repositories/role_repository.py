"""角色仓储接口。

定义角色仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.entities.menu import MenuEntity
from src.domain.entities.role import RoleEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class RoleRepositoryInterface(ABC):
    """角色的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    @abstractmethod
    async def get_by_id(self, role_id: str) -> RoleEntity | None:
        """根据 ID 获取角色。"""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> RoleEntity | None:
        """根据名称获取角色。"""
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> RoleEntity | None:
        """根据编码获取角色。"""
        ...

    @abstractmethod
    async def get_all(self, page_num: int = 1, page_size: int = 10, role_name: str | None = None, is_active: int | None = None) -> list[RoleEntity]:
        """获取所有角色（分页）。"""
        ...

    @abstractmethod
    async def count(self, role_name: str | None = None, is_active: int | None = None) -> int:
        """统计角色总数。"""
        ...

    @abstractmethod
    async def create(self, role: RoleEntity) -> RoleEntity:
        """创建角色。"""
        ...

    @abstractmethod
    async def update(self, role: RoleEntity) -> RoleEntity:
        """更新角色。"""
        ...

    @abstractmethod
    async def delete(self, role_id: str) -> bool:
        """删除角色。"""
        ...

    @abstractmethod
    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """为用户分配角色。"""
        ...

    @abstractmethod
    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """移除用户的角色。"""
        ...

    @abstractmethod
    async def get_user_roles(self, user_id: str) -> list[RoleEntity]:
        """获取用户的角色列表。"""
        ...

    @abstractmethod
    async def assign_roles_to_user(self, user_id: str, role_ids: list[str]) -> bool:
        """为用户批量分配角色（先清除旧角色再分配新的）。"""
        ...

    @abstractmethod
    async def assign_menus_to_role(self, role_id: str, menu_ids: list[str]) -> bool:
        """为角色分配菜单权限（先清除旧菜单再分配新的）。"""
        ...

    @abstractmethod
    async def get_role_menus(self, role_id: str) -> list[MenuEntity]:
        """获取角色的菜单列表。"""
        ...

    @abstractmethod
    async def get_role_menu_ids(self, role_id: str) -> list[str]:
        """获取角色的菜单ID列表。"""
        ...

    @abstractmethod
    async def get_user_all_menus(self, user_id: str) -> list[MenuEntity]:
        """一次查询获取用户所有角色关联的菜单（去重）。

        通过三表 JOIN 替代逐角色查询，消除 N+1 问题。
        """
        ...

    @abstractmethod
    async def get_users_roles_batch(self, user_ids: list[str]) -> dict[str, list[RoleEntity]]:
        """批量获取多个用户的角色列表。

        Args:
            user_ids: 用户 ID 列表

        Returns:
            字典: user_id -> list[RoleEntity]
        """
        ...

    @abstractmethod
    async def get_roles_menu_ids_batch(self, role_ids: list[str]) -> dict[str, list[str]]:
        """批量获取多个角色的菜单ID列表。

        Args:
            role_ids: 角色 ID 列表

        Returns:
            字典: role_id -> list[menu_id]
        """
        ...
