"""用户领域 - 仓储接口。

定义用户仓储的抽象接口，遵循依赖倒置原则。
返回类型使用 Any 作为过渡方案，因为上层代码仍大量使用 ORM 模型属性。
"""

from abc import ABC, abstractmethod
from typing import Any


class UserRepositoryInterface(ABC):
    """用户领域的抽象仓储接口。"""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Any | None:
        """根据 ID 获取用户。

        Args:
            user_id: 用户ID

        Returns:
            用户对象或 None
        """
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> Any | None:
        """根据用户名获取用户。

        Args:
            username: 用户名

        Returns:
            用户对象或 None
        """
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Any | None:
        """根据邮箱获取用户。

        Args:
            email: 电子邮箱

        Returns:
            用户对象或 None
        """
        ...

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Any]:
        """获取所有用户（分页）。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            用户列表
        """
        ...

    @abstractmethod
    async def create(self, user: Any) -> Any:
        """创建新用户。

        Args:
            user: 用户对象

        Returns:
            创建后的用户对象
        """
        ...

    @abstractmethod
    async def update(self, user: Any) -> Any:
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
    async def count(self) -> int:
        """统计用户总数。

        Returns:
            用户总数
        """
        ...
