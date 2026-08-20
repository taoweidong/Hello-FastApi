"""使用 SQLModel 原生 API 实现的通知公告仓库。"""

from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import func as sa_func
from sqlalchemy import update as sa_update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.notice import NoticeEntity
from src.domain.repositories.notice_repository import NoticeRepositoryInterface
from src.infrastructure.database.models import Notice
from src.infrastructure.repositories.base import GenericRepository


class NoticeRepository(GenericRepository[Notice, NoticeEntity], NoticeRepositoryInterface):
    """通知公告仓储的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[Notice]:
        return Notice

    def _to_domain(self, model: Notice) -> NoticeEntity:
        return model.to_domain()

    def _from_domain(self, entity: NoticeEntity) -> Notice:
        return Notice.from_domain(entity)

    def _apply_notice_filters(
        self, stmt: Any, title: str | None = None, notice_type: int | None = None, is_active: int | None = None
    ) -> Any:
        """组装公告筛选条件（标题模糊匹配，类型/状态等值匹配）。"""
        if title:
            stmt = stmt.where(Notice.title.contains(title))
        if notice_type is not None:
            stmt = stmt.where(Notice.notice_type == notice_type)
        if is_active is not None:
            stmt = stmt.where(Notice.is_active == is_active)
        return stmt

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        title: str | None = None,
        notice_type: int | None = None,
        is_active: int | None = None,
    ) -> list[NoticeEntity]:
        """获取公告列表（分页和筛选）。"""
        stmt = select(Notice)
        stmt = self._apply_notice_filters(stmt, title, notice_type, is_active)
        stmt = stmt.order_by(Notice.created_time.desc())  # 最新发布在前
        offset = (page_num - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return [self._to_domain(m) for m in items]

    async def count(
        self, title: str | None = None, notice_type: int | None = None, is_active: int | None = None
    ) -> int:
        """统计公告数量（支持筛选）。"""
        stmt = select(sa_func.count()).select_from(Notice)
        stmt = self._apply_notice_filters(stmt, title, notice_type, is_active)
        result = await self.session.exec(stmt)
        return result.one()

    async def create(self, notice: NoticeEntity) -> NoticeEntity:
        """创建公告。"""
        model = Notice.from_domain(notice)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        loaded = await self.get_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update(self, notice: NoticeEntity) -> NoticeEntity:
        """更新公告。"""
        stmt = sa_update(Notice).where(Notice.id == notice.id).values(**self._build_update_values(notice))
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(notice.id)
        return updated  # type: ignore[return-value]

    async def delete(self, notice_id: str) -> bool:
        """删除公告。"""
        stmt = sa_delete(Notice).where(Notice.id == notice_id)
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
