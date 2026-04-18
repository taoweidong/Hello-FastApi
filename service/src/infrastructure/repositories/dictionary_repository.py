"""使用 SQLModel 和 FastCRUD 实现的字典仓库。"""

from fastcrud import FastCRUD
from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.dictionary_repository import DictionaryRepositoryInterface
from src.infrastructure.database.models import Dictionary


class DictionaryRepository(DictionaryRepositoryInterface):
    """字典仓储的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(Dictionary)

    async def get_all(self, session: AsyncSession) -> list[Dictionary]:
        """获取所有字典，按排序号升序排列。"""
        result = await self._crud.get_multi(session, schema_to_select=Dictionary, return_as_model=True, return_total_count=False)
        dictionaries = result.get("data", [])
        return sorted(dictionaries, key=lambda d: d.sort)

    async def get_by_id(self, dict_id: str, session: AsyncSession) -> Dictionary | None:
        """根据 ID 获取字典。"""
        return await self._crud.get(session, id=dict_id, schema_to_select=Dictionary, return_as_model=True)

    async def get_by_name(self, name: str, session: AsyncSession) -> Dictionary | None:
        """根据名称获取字典。"""
        return await self._crud.get(session, name=name, schema_to_select=Dictionary, return_as_model=True)

    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list[Dictionary]:
        """根据父字典 ID 获取子字典，按排序号升序排列。"""
        result = await self._crud.get_multi(session, parent_id=parent_id, schema_to_select=Dictionary, return_as_model=True, return_total_count=False)
        dictionaries = result.get("data", [])
        return sorted(dictionaries, key=lambda d: d.sort)

    async def get_max_sort(self, parent_id: str | None, session: AsyncSession) -> int:
        """获取同级最大排序值。"""
        stmt = select(func.coalesce(func.max(Dictionary.sort), 0)).where(Dictionary.parent_id == parent_id)
        result = await session.execute(stmt)
        return result.scalar() or 0

    async def create(self, dictionary: Dictionary, session: AsyncSession) -> Dictionary:
        """创建新字典。"""
        return await self._crud.create(session, dictionary)

    async def update(self, dictionary: Dictionary, session: AsyncSession) -> Dictionary:
        """更新现有字典。"""
        from sqlalchemy import update as sa_update

        stmt = sa_update(Dictionary).where(Dictionary.id == dictionary.id).values(name=dictionary.name, label=dictionary.label, value=dictionary.value, sort=dictionary.sort, is_active=dictionary.is_active, parent_id=dictionary.parent_id, description=dictionary.description)
        await session.exec(stmt)  # type: ignore[arg-type]
        await session.flush()
        updated = await self.get_by_id(dictionary.id, session)
        return updated  # type: ignore[return-value]

    async def delete(self, dict_id: str, session: AsyncSession) -> bool:
        """根据 ID 删除字典。"""
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(Dictionary).where(Dictionary.id == dict_id)
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
