"""使用 SQLModel 原生 API 实现的岗位仓库。"""

from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import func as sa_func
from sqlalchemy import update as sa_update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.post import PostEntity
from src.domain.repositories.post_repository import PostRepositoryInterface
from src.infrastructure.database.models import Post
from src.infrastructure.database.models.user_post_link import UserPostLink
from src.infrastructure.repositories.base import GenericRepository


class PostRepository(GenericRepository[Post, PostEntity], PostRepositoryInterface):
    """岗位仓储的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[Post]:
        return Post

    def _to_domain(self, model: Post) -> PostEntity:
        return model.to_domain()

    def _from_domain(self, entity: PostEntity) -> Post:
        return Post.from_domain(entity)

    def _apply_post_filters(
        self, stmt: Any, post_code: str | None = None, post_name: str | None = None, is_active: int | None = None
    ) -> Any:
        """组装岗位筛选条件（编码/名称模糊匹配，状态等值匹配）。"""
        if post_code:
            stmt = stmt.where(Post.post_code.contains(post_code))
        if post_name:
            stmt = stmt.where(Post.post_name.contains(post_name))
        if is_active is not None:
            stmt = stmt.where(Post.is_active == is_active)
        return stmt

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        post_code: str | None = None,
        post_name: str | None = None,
        is_active: int | None = None,
    ) -> list[PostEntity]:
        """获取岗位列表（分页和筛选）。"""
        stmt = select(Post)
        stmt = self._apply_post_filters(stmt, post_code, post_name, is_active)
        stmt = stmt.order_by(Post.post_sort)
        offset = (page_num - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return [self._to_domain(m) for m in items]

    async def count(
        self, post_code: str | None = None, post_name: str | None = None, is_active: int | None = None
    ) -> int:
        """统计岗位数量（支持筛选）。"""
        stmt = select(sa_func.count()).select_from(Post)
        stmt = self._apply_post_filters(stmt, post_code, post_name, is_active)
        result = await self.session.exec(stmt)
        return result.one()

    async def get_all_active(self) -> list[PostEntity]:
        """获取全部启用岗位（按排序升序）。"""
        stmt = select(Post).where(Post.is_active == 1).order_by(Post.post_sort)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return [self._to_domain(m) for m in items]

    async def get_by_code(self, post_code: str) -> PostEntity | None:
        """根据岗位编码获取岗位。"""
        stmt = select(Post).where(Post.post_code == post_code)
        result = await self.session.exec(stmt)
        model = result.first()
        return model.to_domain() if model else None

    async def create(self, post: PostEntity) -> PostEntity:
        """创建岗位。"""
        model = Post.from_domain(post)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        loaded = await self.get_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update(self, post: PostEntity) -> PostEntity:
        """更新岗位。"""
        stmt = sa_update(Post).where(Post.id == post.id).values(**self._build_update_values(post))
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(post.id)
        return updated  # type: ignore[return-value]

    async def delete(self, post_id: str) -> bool:
        """删除岗位（同时清理用户关联）。"""
        link_stmt = sa_delete(UserPostLink).where(UserPostLink.post_id == post_id)
        await self.session.exec(link_stmt)  # type: ignore[arg-type]
        stmt = sa_delete(Post).where(Post.id == post_id)
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def batch_delete(self, ids: list[str]) -> int:
        """批量删除岗位（同时清理用户关联）。"""
        if not ids:
            return 0
        link_stmt = sa_delete(UserPostLink).where(UserPostLink.post_id.in_(ids))
        await self.session.exec(link_stmt)  # type: ignore[arg-type]
        return await super().batch_delete(ids)

    # ---- 用户-岗位关联 ----

    async def get_post_ids_by_user(self, user_id: str) -> list[str]:
        """获取用户关联的岗位 ID 列表。"""
        stmt = select(UserPostLink.post_id).where(UserPostLink.user_id == user_id)
        result = await self.session.exec(stmt)
        try:
            return list(result.scalars().all())
        except AttributeError:
            return list(result.all())

    async def assign_posts_to_user(self, user_id: str, post_ids: list[str]) -> bool:
        """为用户分配岗位（先清空旧关联再写入新关联）。"""
        stmt = sa_delete(UserPostLink).where(UserPostLink.user_id == user_id)
        await self.session.exec(stmt)  # type: ignore[arg-type]
        for post_id in post_ids:
            self.session.add(UserPostLink(user_id=user_id, post_id=post_id))
        await self.session.flush()
        return True
