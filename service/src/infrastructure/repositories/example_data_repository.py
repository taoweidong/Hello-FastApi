"""使用 SQLModel 原生 API 实现的示例数据仓储。

单表 CRUD 示例模块。update 采用 sa_update + 重读模式（规避基类 merge 丢字段）。
"""

from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import func as sa_func
from sqlalchemy import update as sa_update
from sqlmodel import select

from src.domain.entities.example_data import ExampleDataEntity
from src.domain.repositories.example_data_repository import ExampleDataRepositoryInterface
from src.infrastructure.database.models import ExampleData
from src.infrastructure.repositories.base import GenericRepository


class ExampleDataRepository(GenericRepository[ExampleData, ExampleDataEntity], ExampleDataRepositoryInterface):
    """ExampleDataRepositoryInterface 的 SQLModel 原生实现。"""

    @property
    def _model_class(self) -> type[ExampleData]:
        return ExampleData

    def _to_domain(self, model: ExampleData) -> ExampleDataEntity:
        return model.to_domain()

    def _from_domain(self, entity: ExampleDataEntity) -> ExampleData:
        return ExampleData.from_domain(entity)

    def _build_filters(self, name: str | None, category: str | None, is_active: int | None) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if name:
            filters["name"] = name
        if category:
            filters["category"] = category
        if is_active is not None:
            filters["is_active"] = is_active
        return filters

    async def get_by_id(self, row_id: str) -> ExampleDataEntity | None:
        model = await self.session.get(ExampleData, row_id)
        return self._to_domain(model) if model else None

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        name: str | None = None,
        category: str | None = None,
        is_active: int | None = None,
    ) -> list[ExampleDataEntity]:
        filters = self._build_filters(name, category, is_active)
        stmt = select(ExampleData)
        stmt = self._apply_filters(stmt, filters)
        offset = (page_num - 1) * page_size
        result = await self.session.exec(stmt.offset(offset).limit(page_size))
        return [self._to_domain(m) for m in result.all()]

    async def count(self, name: str | None = None, category: str | None = None, is_active: int | None = None) -> int:
        filters = self._build_filters(name, category, is_active)
        stmt = select(sa_func.count()).select_from(ExampleData)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.exec(stmt)
        return result.one()

    async def create(self, entity: ExampleDataEntity) -> ExampleDataEntity:
        model = ExampleData.from_domain(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def update(self, entity: ExampleDataEntity) -> ExampleDataEntity:
        stmt = (
            sa_update(ExampleData)
            .where(ExampleData.id == entity.id)
            .values(
                name=entity.name,
                category=entity.category,
                quantity=entity.quantity,
                price=entity.price,
                record_date=entity.record_date,
                note=entity.note,
                is_active=entity.is_active,
                modifier_id=entity.modifier_id,
            )
        )
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.session.get(ExampleData, entity.id)
        return updated.to_domain()  # type: ignore[union-attr]

    async def delete(self, row_id: str) -> bool:
        stmt = sa_delete(ExampleData).where(ExampleData.id == row_id)
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return (result.rowcount or 0) > 0

    async def batch_delete(self, row_ids: list[str]) -> int:
        if not row_ids:
            return 0
        stmt = sa_delete(ExampleData).where(ExampleData.id.in_(row_ids))
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount or 0
