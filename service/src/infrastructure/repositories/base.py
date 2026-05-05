"""通用仓储基类。

基于 SQLModel 原生 API，提供单表 CRUD 操作的泛型实现。
子类需指定 ModelT (SQLModel 表模型) 和 EntityT (领域实体)。

设计原则：
- 常用基础功能在仓储层封装（基础 CRUD、简单查询）
- 复杂业务逻辑在服务层处理（验证、事务、多步骤操作）
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import Column
from sqlalchemy import delete as sa_delete
from sqlalchemy import func as sa_func
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelT = TypeVar("ModelT", bound=SQLModel)
EntityT = TypeVar("EntityT")


def _get_column(model_class: type[SQLModel], field_name: str) -> Column:
    """从 SQLModel 类获取列对象。"""
    from sqlalchemy.inspection import inspect as sa_inspect

    mapper = sa_inspect(model_class)
    return mapper.columns[field_name]


class GenericRepository(Generic[ModelT, EntityT]):
    """通用仓储基类，封装 SQLModel 原生的单表 CRUD。

    子类需实现：
    - _model_class: 返回 SQLModel 表模型类
    - _to_domain: 将表模型转为领域实体
    - _from_domain: 将领域实体转为表模型
    - _primary_key: 主键字段名（默认 "id"）

    常用方法：
    - get_by_id: 按主键获取
    - get_all: 分页+筛选列表
    - count: 统计数量
    - create: 创建
    - update: 更新
    - delete: 删除
    - exists: 判断是否存在
    - get_one_by: 按单字段查询
    - batch_delete: 批量删除
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @property
    def _model_class(self) -> type[ModelT]:
        """返回 SQLModel 表模型类。子类必须实现。"""
        raise NotImplementedError

    def _to_domain(self, model: ModelT) -> EntityT:
        """将表模型转为领域实体。子类必须实现。"""
        raise NotImplementedError

    def _from_domain(self, entity: EntityT) -> ModelT:
        """将领域实体转为表模型。子类必须实现。"""
        raise NotImplementedError

    @property
    def _primary_key(self) -> str:
        """主键字段名，默认 id。"""
        return "id"

    def _get_pk_column(self) -> Column:
        """获取主键列。"""
        return _get_column(self._model_class, self._primary_key)

    # ========== 基础 CRUD ==========

    async def get_by_id(self, item_id: str) -> EntityT | None:
        """根据 ID 获取单个实体。"""
        pk_col = self._get_pk_column()
        stmt = select(self._model_class).where(pk_col == item_id)
        result = await self.session.exec(stmt)
        model = result.first()
        return self._to_domain(model) if model else None

    async def get_all(self, page_num: int = 1, page_size: int = 10, **filters: Any) -> list[EntityT]:
        """获取实体列表（分页 + 筛选）。"""
        stmt = select(self._model_class)
        stmt = self._apply_filters(stmt, filters)

        offset = (page_num - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.session.exec(stmt)
        try:
            items = result.scalars().all()
        except AttributeError:
            items = result.all()
        return [self._to_domain(m) for m in items]

    async def create(self, entity: EntityT) -> EntityT:
        """创建新实体。"""
        model = self._from_domain(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def update(self, entity: EntityT) -> EntityT:
        """更新现有实体。"""
        model = self._from_domain(entity)
        merged = await self.session.merge(model)
        await self.session.flush()
        await self.session.refresh(merged)
        return self._to_domain(merged)

    async def delete(self, item_id: str) -> bool:
        """根据 ID 删除实体。"""
        pk_col = self._get_pk_column()
        stmt = sa_delete(self._model_class).where(pk_col == item_id)
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return (result.rowcount or 0) > 0

    async def count(self, **filters: Any) -> int:
        """统计实体数量（支持筛选）。"""
        stmt = select(sa_func.count()).select_from(self._model_class)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.exec(stmt)
        return result.one()

    # ========== 扩展查询方法 ==========

    async def get_one_by(self, field: str, value: Any) -> EntityT | None:
        """根据单字段查询单个实体。

        Args:
            field: 字段名
            value: 字段值

        Returns:
            实体或 None
        """
        try:
            col = _get_column(self._model_class, field)
        except KeyError:
            return None
        stmt = select(self._model_class).where(col == value)
        result = await self.session.exec(stmt)
        model = result.first()
        return self._to_domain(model) if model else None

    async def exists(self, field: str, value: Any) -> bool:
        """判断实体是否存在。

        Args:
            field: 字段名
            value: 字段值

        Returns:
            是否存在
        """
        try:
            col = _get_column(self._model_class, field)
        except KeyError:
            return False
        stmt = select(sa_func.count()).select_from(self._model_class).where(col == value)
        result = await self.session.exec(stmt)
        return result.one() > 0

    async def batch_delete(self, ids: list[str]) -> int:
        """批量删除实体。

        Args:
            ids: ID 列表

        Returns:
            删除数量
        """
        if not ids:
            return 0
        pk_col = self._get_pk_column()
        stmt = sa_delete(self._model_class).where(pk_col.in_(ids))
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount or 0

    # ========== 内部辅助方法 ==========

    def _apply_filters(self, stmt: Any, filters: dict[str, Any]) -> Any:
        """应用筛选条件到查询语句。

        Args:
            stmt: Select 语句
            filters: 筛选条件字典

        Returns:
            添加筛选后的语句
        """
        for field, value in filters.items():
            if value is not None:
                try:
                    col = _get_column(self._model_class, field)
                    stmt = stmt.where(col == value)
                except KeyError:
                    pass  # 忽略不存在的字段
        return stmt
