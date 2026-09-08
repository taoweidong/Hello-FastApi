"""岗位仓储接口。

定义岗位仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.entities.post import PostEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class PostRepositoryInterface(ABC):
    """岗位的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    @abstractmethod
    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        post_code: str | None = None,
        post_name: str | None = None,
        is_active: int | None = None,
    ) -> list[PostEntity]:
        """获取岗位列表（支持分页和筛选，编码/名称模糊匹配）。"""
        ...

    @abstractmethod
    async def count(
        self, post_code: str | None = None, post_name: str | None = None, is_active: int | None = None
    ) -> int:
        """统计岗位数量（支持筛选）。"""
        ...

    @abstractmethod
    async def get_all_active(self) -> list[PostEntity]:
        """获取全部启用岗位（按排序升序，供下拉选项使用）。"""
        ...

    @abstractmethod
    async def get_by_id(self, post_id: str) -> PostEntity | None:
        """根据 ID 获取岗位。"""
        ...

    @abstractmethod
    async def get_by_code(self, post_code: str) -> PostEntity | None:
        """根据岗位编码获取岗位。"""
        ...

    @abstractmethod
    async def create(self, post: PostEntity) -> PostEntity:
        """创建岗位。"""
        ...

    @abstractmethod
    async def update(self, post: PostEntity) -> PostEntity:
        """更新岗位。"""
        ...

    @abstractmethod
    async def delete(self, post_id: str) -> bool:
        """删除岗位。"""
        ...

    @abstractmethod
    async def batch_delete(self, ids: list[str]) -> int:
        """批量删除岗位，返回删除数量。"""
        ...

    # ---- 用户-岗位关联 ----

    @abstractmethod
    async def get_post_ids_by_user(self, user_id: str) -> list[str]:
        """获取用户关联的岗位 ID 列表。"""
        ...

    @abstractmethod
    async def assign_posts_to_user(self, user_id: str, post_ids: list[str]) -> bool:
        """为用户分配岗位（先清空旧关联再写入新关联）。"""
        ...
