"""使用 SQLModel 和 FastCRUD 实现的字典仓库。"""

from fastcrud import FastCRUD
from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.dictionary import DictionaryEntity
from src.domain.repositories.dictionary_repository import DictionaryRepositoryInterface
from src.infrastructure.database.models import Dictionary


class DictionaryRepository(DictionaryRepositoryInterface):
    """字典仓储的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(Dictionary)

    async def get_all(self) -> list[DictionaryEntity]:
        """获取所有字典，按排序号升序排列。"""
        result = await self._crud.get_multi(self.session, schema_to_select=Dictionary, return_as_model=True, return_total_count=False)
        dictionaries = result.get("data", [])
        return sorted([d.to_domain() for d in dictionaries], key=lambda d: d.sort)

    async def get_by_id(self, dict_id: str) -> DictionaryEntity | None:
        """根据 ID 获取字典。"""
        model = await self._crud.get(self.session, id=dict_id, schema_to_select=Dictionary, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_name(self, name: str) -> DictionaryEntity | None:
        """根据名称获取字典。"""
        model = await self._crud.get(self.session, name=name, schema_to_select=Dictionary, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_parent_id(self, parent_id: str | None) -> list[DictionaryEntity]:
        """根据父字典 ID 获取子字典，按排序号升序排列。"""
        result = await self._crud.get_multi(self.session, parent_id=parent_id, schema_to_select=Dictionary, return_as_model=True, return_total_count=False)
        dictionaries = result.get("data", [])
        return sorted([d.to_domain() for d in dictionaries], key=lambda d: d.sort)

    async def get_max_sort(self, parent_id: str | None) -> int:
        """获取同级最大排序值。"""
        stmt = select(func.coalesce(func.max(Dictionary.sort), 0)).where(Dictionary.parent_id == parent_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def create(self, dictionary: DictionaryEntity) -> DictionaryEntity:
        """创建新字典。"""
        model = Dictionary.from_domain(dictionary)
        self.session.add(model)
        await self.session.flush()
        # 读回以获取自动生成的字段
        loaded = await self.get_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update(self, dictionary: DictionaryEntity) -> DictionaryEntity:
        """更新现有字典。"""
        from sqlalchemy import update as sa_update

        stmt = sa_update(Dictionary).where(Dictionary.id == dictionary.id).values(name=dictionary.name, label=dictionary.label, value=dictionary.value, sort=dictionary.sort, is_active=dictionary.is_active, parent_id=dictionary.parent_id, description=dictionary.description)
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(dictionary.id)
        return updated  # type: ignore[return-value]

    async def delete(self, dict_id: str) -> bool:
        """根据 ID 删除字典。"""
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(Dictionary).where(Dictionary.id == dict_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
