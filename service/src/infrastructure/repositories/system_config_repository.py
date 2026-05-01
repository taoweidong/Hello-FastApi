"""使用 SQLModel 和 FastCRUD 实现的系统配置仓库。"""

from fastcrud import FastCRUD
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.system_config import SystemConfigEntity
from src.domain.repositories.system_config_repository import SystemConfigRepositoryInterface
from src.infrastructure.database.models import SystemConfig


class SystemConfigRepository(SystemConfigRepositoryInterface):
    """系统配置仓储的 SQLModel 实现。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(SystemConfig)

    async def get_all(
        self, page_num: int = 1, page_size: int = 10, key: str | None = None, is_active: int | None = None
    ) -> list[SystemConfigEntity]:
        """获取配置列表（支持分页和筛选）。"""
        offset = (page_num - 1) * page_size
        query = select(SystemConfig)

        if key:
            query = query.where(SystemConfig.key.contains(key))
        if is_active is not None:
            query = query.where(SystemConfig.is_active == is_active)

        query = query.offset(offset).limit(page_size)
        result = await self.session.exec(query)
        return [m.to_domain() for m in result.all()]

    async def count(self, key: str | None = None, is_active: int | None = None) -> int:
        """统计配置数量（支持筛选）。"""
        count_query = select(sa_func.count()).select_from(SystemConfig)

        if key:
            count_query = count_query.where(SystemConfig.key.contains(key))
        if is_active is not None:
            count_query = count_query.where(SystemConfig.is_active == is_active)

        result = await self.session.exec(count_query)
        return result.one()

    async def get_by_id(self, config_id: str) -> SystemConfigEntity | None:
        """根据 ID 获取配置。"""
        model = await self._crud.get(self.session, id=config_id, schema_to_select=SystemConfig, return_as_model=True)
        return model.to_domain() if model else None

    async def get_by_key(self, key: str) -> SystemConfigEntity | None:
        """根据 key 获取配置。"""
        model = await self._crud.get(self.session, key=key, schema_to_select=SystemConfig, return_as_model=True)
        return model.to_domain() if model else None

    async def create(self, config: SystemConfigEntity) -> SystemConfigEntity:
        """创建配置。"""
        model = SystemConfig.from_domain(config)
        self.session.add(model)
        await self.session.flush()
        # 读回以获取自动生成的字段
        loaded = await self.get_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update(self, config: SystemConfigEntity) -> SystemConfigEntity:
        """更新配置。"""
        from sqlalchemy import update as sa_update

        stmt = (
            sa_update(SystemConfig)
            .where(SystemConfig.id == config.id)
            .values(
                value=config.value,
                is_active=config.is_active,
                access=config.access,
                key=config.key,
                inherit=config.inherit,
                creator_id=config.creator_id,
                modifier_id=config.modifier_id,
                description=config.description,
            )
        )
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(config.id)
        return updated  # type: ignore[return-value]

    async def delete(self, config_id: str) -> bool:
        """删除配置。"""
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(SystemConfig).where(SystemConfig.id == config_id)
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
