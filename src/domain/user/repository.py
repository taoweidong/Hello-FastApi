"""用户领域 - 仓库接口。"""

from abc import ABC, abstractmethod

from src.domain.user.entities import User


class UserRepositoryInterface(ABC):
    """用户领域的抽象仓库接口。"""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        """根据 ID 获取用户。"""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """根据用户名获取用户。"""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """根据邮箱获取用户。"""
        ...

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """获取所有用户（分页）。"""
        ...

    @abstractmethod
    async def create(self, user: User) -> User:
        """创建新用户。"""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """更新现有用户。"""
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """根据 ID 删除用户。"""
        ...

    @abstractmethod
    async def count(self) -> int:
        """统计用户总数。"""
        ...
