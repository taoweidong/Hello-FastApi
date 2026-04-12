"""使用 SQLModel 和 FastCRUD 实现的系统配置仓库。"""

from fastcrud import FastCRUD
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.system_config_repository import SystemConfigRepositoryInterface
from src.infrastructure.database.models import SystemConfig


class SystemConfigRepository(SystemConfigRepositoryInterface):
    """系统配置仓储的 SQLModel 实现。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(SystemConfig)

    async def get_all(self, session: AsyncSession) -> list[SystemConfig]:
        """获取所有配置。"""
        result = await self._crud.get_multi(session, schema_to_select=SystemConfig, return_as_model=True, return_total_count=False)
        return list(result.get("data", []))

    async def get_by_id(self, config_id: str, session: AsyncSession) -> SystemConfig | None:
        """根据 ID 获取配置。"""
        return await self._crud.get(session, id=config_id, schema_to_select=SystemConfig, return_as_model=True)

    async def get_by_key(self, key: str, session: AsyncSession) -> SystemConfig | None:
        """根据 key 获取配置。"""
        return await self._crud.get(session, key=key, schema_to_select=SystemConfig, return_as_model=True)

    async def create(self, config: SystemConfig, session: AsyncSession) -> SystemConfig:
        """创建配置。"""
        return await self._crud.create(session, config)

    async def update(self, config: SystemConfig, session: AsyncSession) -> SystemConfig:
        """更新配置。"""
        from sqlalchemy import update as sa_update

        stmt = sa_update(SystemConfig).where(SystemConfig.id == config.id).values(
            value=config.value,
            is_active=config.is_active,
            access=config.access,
            key=config.key,
            inherit=config.inherit,
            creator_id=config.creator_id,
            modifier_id=config.modifier_id,
            description=config.description,
        )
        await session.exec(stmt)  # type: ignore[arg-type]
        await session.flush()
        updated = await self.get_by_id(config.id, session)
        return updated  # type: ignore[return-value]

    async def delete(self, config_id: str, session: AsyncSession) -> bool:
        """删除配置。"""
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(SystemConfig).where(SystemConfig.id == config_id)
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
