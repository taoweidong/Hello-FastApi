"""仓储基类模块。

提供通用的 CRUD 和分页功能，减少仓储层的重复代码。
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """仓储基类，提供通用 CRUD 和分页功能。

    此基类封装了常见的数据库操作，子类可以通过继承来复用这些方法。
    对于有特殊需求的仓储，可以覆盖这些方法。

    使用示例:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(session, User)
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        """初始化仓储。

        Args:
            session: 数据库会话
            model: 模型类
        """
        self.session = session
        self.model = model

    async def get_by_id(self, id: str) -> ModelType | None:
        """根据 ID 获取实体。

        Args:
            id: 实体 ID

        Returns:
            实体对象，如果不存在则返回 None
        """
        return await self.session.get(self.model, id)

    async def get_by_field(self, field_name: str, value: Any) -> ModelType | None:
        """根据指定字段获取单个实体。

        Args:
            field_name: 字段名
            value: 字段值

        Returns:
            实体对象，如果不存在则返回 None
        """
        field = getattr(self.model, field_name)
        result = await self.session.exec(select(self.model).where(field == value))
        return result.one_or_none()

    async def get_all_with_pagination(
        self,
        page_num: int = 1,
        page_size: int = 10,
        order_by: Any = None,
        **filters,
    ) -> list[ModelType]:
        """获取实体列表（支持分页和筛选）。

        Args:
            page_num: 页码，从 1 开始
            page_size: 每页数量
            order_by: 排序字段
            **filters: 筛选条件，支持 contains 模糊查询

        Returns:
            实体列表
        """
        query = select(self.model)

        # 应用筛选条件
        for field_name, value in filters.items():
            if value is None:
                continue
            field = getattr(self.model, field_name, None)
            if field is None:
                continue
            # 字符串类型使用 contains 模糊查询
            if isinstance(value, str):
                query = query.where(field.contains(value))
            else:
                query = query.where(field == value)

        # 排序
        if order_by is not None:
            query = query.order_by(order_by)

        # 分页
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.exec(query)
        return list(result.all())

    async def count(self, **filters) -> int:
        """获取实体总数（支持筛选）。

        Args:
            **filters: 筛选条件

        Returns:
            实体数量
        """
        query = select(sa_func.count()).select_from(self.model)

        # 应用筛选条件
        for field_name, value in filters.items():
            if value is None:
                continue
            field = getattr(self.model, field_name, None)
            if field is None:
                continue
            if isinstance(value, str):
                query = query.where(field.contains(value))
            else:
                query = query.where(field == value)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, entity: ModelType) -> ModelType:
        """创建实体。

        Args:
            entity: 实体对象

        Returns:
            创建后的实体（包含生成的 ID）
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """更新实体。

        Args:
            entity: 实体对象

        Returns:
            更新后的实体
        """
        merged = await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(merged)
        return merged

    async def delete(self, id: str) -> bool:
        """删除实体。

        Args:
            id: 实体 ID

        Returns:
            是否删除成功
        """
        entity = await self.get_by_id(id)
        if entity is None:
            return False
        await self.session.delete(entity)
        await self.session.flush()
        return True

    async def batch_delete(self, ids: list[str]) -> int:
        """批量删除实体。

        Args:
            ids: 实体 ID 列表

        Returns:
            删除的数量
        """
        count = 0
        for id in ids:
            if await self.delete(id):
                count += 1
        return count

    async def exists(self, field_name: str, value: Any, exclude_id: str | None = None) -> bool:
        """检查字段值是否已存在。

        Args:
            field_name: 字段名
            value: 字段值
            exclude_id: 排除的实体 ID（用于更新时排除自身）

        Returns:
            是否存在
        """
        field = getattr(self.model, field_name)
        query = select(self.model).where(field == value)

        if exclude_id:
            id_field = self.model.id
            query = query.where(id_field != exclude_id)

        result = await self.session.exec(query)
        return result.one_or_none() is not None
