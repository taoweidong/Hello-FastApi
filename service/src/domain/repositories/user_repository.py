"""用户领域 - 仓储接口。

定义用户仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.database.models import User


class UserRepositoryInterface(ABC):
    """用户领域的抽象仓储接口。"""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> "User | None":
        """根据 ID 获取用户。

        Args:
            user_id: 用户ID

        Returns:
            用户对象或 None
        """
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> "User | None":
        """根据用户名获取用户。

        Args:
            username: 用户名

        Returns:
            用户对象或 None
        """
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> "User | None":
        """根据邮箱获取用户。

        Args:
            email: 电子邮箱

        Returns:
            用户对象或 None
        """
        ...

    @abstractmethod
    async def get_all(self, page_num: int = 1, page_size: int = 10, username: str | None = None, phone: str | None = None, email: str | None = None, status: int | None = None, dept_id: int | None = None) -> list["User"]:
        """获取用户列表（分页与筛选）。"""
        ...

    @abstractmethod
    async def create(self, user: "User") -> "User":
        """创建新用户。

        Args:
            user: 用户对象

        Returns:
            创建后的用户对象
        """
        ...

    @abstractmethod
    async def update(self, user: "User") -> "User":
        """更新现有用户。

        Args:
            user: 用户对象

        Returns:
            更新后的用户对象
        """
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """根据 ID 删除用户。

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        ...

    @abstractmethod
    async def count(self, username: str | None = None, phone: str | None = None, email: str | None = None, status: int | None = None, dept_id: int | None = None) -> int:
        """统计用户数（支持筛选）。"""
        ...

    @abstractmethod
    async def batch_delete(self, user_ids: list[str]) -> int:
        """批量删除用户。"""
        ...

    @abstractmethod
    async def update_status(self, user_id: str, status: int) -> bool:
        """更新用户状态。"""
        ...

    @abstractmethod
    async def reset_password(self, user_id: str, hashed_password: str) -> bool:
        """重置用户密码（已哈希）。"""
        ...
