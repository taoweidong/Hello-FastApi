"""用户领域 - 仓储接口。

定义用户仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.entities.user import UserEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class UserRepositoryInterface(ABC):
    """用户领域的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> UserEntity | None:
        """根据 ID 获取用户。"""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> UserEntity | None:
        """根据用户名获取用户。"""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> UserEntity | None:
        """根据邮箱获取用户。"""
        ...

    @abstractmethod
    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
        scope_dept_ids: list[str] | None = None,
        scope_user_id: str | None = None,
    ) -> list[UserEntity]:
        """获取用户列表（分页与筛选）。

        Args:
            scope_dept_ids: 数据权限部门范围（None 表示不限；空列表表示无可见数据）
            scope_user_id: 仅本人数据权限时限定当前用户ID
        """
        ...

    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity:
        """创建新用户。"""
        ...

    @abstractmethod
    async def update(self, user: UserEntity) -> UserEntity:
        """更新现有用户。"""
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """根据 ID 删除用户。"""
        ...

    @abstractmethod
    async def count(
        self,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
        scope_dept_ids: list[str] | None = None,
        scope_user_id: str | None = None,
    ) -> int:
        """统计用户数（支持筛选与数据权限范围）。"""
        ...

    @abstractmethod
    async def get_usernames_by_ids(self, user_ids: list[str]) -> dict[str, str]:
        """按 ID 批量取用户名（仪表盘 recentLogs 的 creator 映射）。

        单次 IN 查询返回 ``{user_id: username}``，替代逐条 get_by_id 的 N+1。

        Args:
            user_ids: 用户 ID 列表（去重由实现方负责）

        Returns:
            ID → 用户名映射；查不到的 ID 不出现在结果中
        """
        ...

    @abstractmethod
    async def batch_delete(self, user_ids: list[str]) -> int:
        """批量删除用户。"""
        ...
