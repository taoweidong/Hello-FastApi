"""使用 SQLModel 原生 API 实现的系统配置仓库。"""

from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.system_config import SystemConfigEntity
from src.domain.repositories.system_config_repository import SystemConfigRepositoryInterface
from src.infrastructure.database.models import SystemConfig
from src.infrastructure.repositories.base import GenericRepository


class SystemConfigRepository(GenericRepository[SystemConfig, SystemConfigEntity], SystemConfigRepositoryInterface):
    """系统配置仓储的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[SystemConfig]:
        return SystemConfig

    def _to_domain(self, model: SystemConfig) -> SystemConfigEntity:
        return model.to_domain()

    def _from_domain(self, entity: SystemConfigEntity) -> SystemConfig:
        return SystemConfig.from_domain(entity)

    async def get_all(
        self, page_num: int = 1, page_size: int = 10, key: str | None = None, is_active: int | None = None
    ) -> list[SystemConfigEntity]:
        """获取配置列表（分页和筛选）。"""
        filters: dict[str, Any] = {}
        if key:
            filters["key"] = key
        if is_active is not None:
            filters["is_active"] = is_active
        return await super().get_all(page_num, page_size, **filters)

    async def count(self, key: str | None = None, is_active: int | None = None) -> int:
        """统计配置数量（支持筛选）。"""
        filters: dict[str, Any] = {}
        if key:
            filters["key"] = key
        if is_active is not None:
            filters["is_active"] = is_active
        return await super().count(**filters)

    async def get_by_key(self, key: str) -> SystemConfigEntity | None:
        """根据 key 获取配置。"""
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await self.session.exec(stmt)
        model = result.first()
        return model.to_domain() if model else None

    async def create(self, config: SystemConfigEntity) -> SystemConfigEntity:
        """创建配置。"""
        model = SystemConfig.from_domain(config)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        loaded = await self.get_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update(self, config: SystemConfigEntity) -> SystemConfigEntity:
        """更新配置。"""
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
        stmt = sa_delete(SystemConfig).where(SystemConfig.id == config_id)
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
