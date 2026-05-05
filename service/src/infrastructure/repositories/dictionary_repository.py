"""使用 SQLModel 原生 API 实现的字典仓库。"""

from sqlalchemy import delete as sa_delete
from sqlalchemy import func as sa_func
from sqlalchemy import update as sa_update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.dictionary import DictionaryEntity
from src.domain.repositories.dictionary_repository import DictionaryRepositoryInterface
from src.infrastructure.database.models import Dictionary
from src.infrastructure.repositories.base import GenericRepository


class DictionaryRepository(GenericRepository[Dictionary, DictionaryEntity], DictionaryRepositoryInterface):
    """字典仓储的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[Dictionary]:
        return Dictionary

    def _to_domain(self, model: Dictionary) -> DictionaryEntity:
        return model.to_domain()

    def _from_domain(self, entity: DictionaryEntity) -> Dictionary:
        return Dictionary.from_domain(entity)

    async def get_all(self) -> list[DictionaryEntity]:
        """获取所有字典，按排序号升序排列。"""
        stmt = select(Dictionary).order_by(Dictionary.sort)
        result = await self.session.exec(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_name(self, name: str) -> DictionaryEntity | None:
        """根据名称获取字典。"""
        stmt = select(Dictionary).where(Dictionary.name == name)
        result = await self.session.exec(stmt)
        model = result.first()
        return model.to_domain() if model else None

    async def get_by_parent_id(self, parent_id: str | None) -> list[DictionaryEntity]:
        """根据父字典 ID 获取子字典，按排序号升序排列。"""
        stmt = select(Dictionary).where(Dictionary.parent_id == parent_id).order_by(Dictionary.sort)
        result = await self.session.exec(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_max_sort(self, parent_id: str | None) -> int:
        """获取同级最大排序值。"""
        stmt = select(sa_func.coalesce(sa_func.max(Dictionary.sort), 0)).where(Dictionary.parent_id == parent_id)
        result = await self.session.exec(stmt)
        return result.scalar() or 0

    async def create(self, dictionary: DictionaryEntity) -> DictionaryEntity:
        """创建新字典。"""
        model = Dictionary.from_domain(dictionary)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        loaded = await self.get_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update(self, dictionary: DictionaryEntity) -> DictionaryEntity:
        """更新现有字典。"""
        stmt = (
            sa_update(Dictionary)
            .where(Dictionary.id == dictionary.id)
            .values(
                name=dictionary.name,
                label=dictionary.label,
                value=dictionary.value,
                sort=dictionary.sort,
                is_active=dictionary.is_active,
                parent_id=dictionary.parent_id,
                description=dictionary.description,
            )
        )
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(dictionary.id)
        return updated  # type: ignore[return-value]

    async def delete(self, dict_id: str) -> bool:
        """根据 ID 删除字典。"""
        stmt = sa_delete(Dictionary).where(Dictionary.id == dict_id)
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def get_filtered(self, name: str | None = None, is_active: int | None = None) -> list[DictionaryEntity]:
        """获取过滤后的字典列表，按排序号升序排列。"""
        stmt = select(Dictionary)
        if name:
            stmt = stmt.where(Dictionary.name.contains(name))
        if is_active is not None:
            stmt = stmt.where(Dictionary.is_active == is_active)
        stmt = stmt.order_by(Dictionary.sort)

        result = await self.session.exec(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]
