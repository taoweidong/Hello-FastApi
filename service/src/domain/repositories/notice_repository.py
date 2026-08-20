"""通知公告仓储接口。

定义通知公告仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.entities.notice import NoticeEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class NoticeRepositoryInterface(ABC):
    """通知公告的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    @abstractmethod
    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        title: str | None = None,
        notice_type: int | None = None,
        is_active: int | None = None,
    ) -> list[NoticeEntity]:
        """获取公告列表（支持分页和筛选，标题模糊匹配）。"""
        ...

    @abstractmethod
    async def count(
        self, title: str | None = None, notice_type: int | None = None, is_active: int | None = None
    ) -> int:
        """统计公告数量（支持筛选）。"""
        ...

    @abstractmethod
    async def get_by_id(self, notice_id: str) -> NoticeEntity | None:
        """根据 ID 获取公告。"""
        ...

    @abstractmethod
    async def create(self, notice: NoticeEntity) -> NoticeEntity:
        """创建公告。"""
        ...

    @abstractmethod
    async def update(self, notice: NoticeEntity) -> NoticeEntity:
        """更新公告。"""
        ...

    @abstractmethod
    async def delete(self, notice_id: str) -> bool:
        """删除公告。"""
        ...

    @abstractmethod
    async def batch_delete(self, ids: list[str]) -> int:
        """批量删除公告，返回删除数量。"""
        ...
