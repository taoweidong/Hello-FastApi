"""应用层 - 系统配置服务。"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.system_config_dto import SystemConfigCreateDTO, SystemConfigListQueryDTO, SystemConfigResponseDTO, SystemConfigUpdateDTO
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories.system_config_repository import SystemConfigRepositoryInterface
from src.infrastructure.database.models import SystemConfig


class SystemConfigService:
    """系统配置操作的应用服务。"""

    def __init__(self, session: AsyncSession, config_repo: SystemConfigRepositoryInterface):
        self.session = session
        self.config_repo = config_repo

    async def create_config(self, dto: SystemConfigCreateDTO) -> SystemConfigResponseDTO:
        """创建系统配置。"""
        # 检查key唯一性
        existing = await self.config_repo.get_by_key(dto.key, session=self.session)
        if existing:
            raise ConflictError(f"配置键 '{dto.key}' 已存在")

        config = SystemConfig(key=dto.key, value=dto.value, is_active=dto.isActive if dto.isActive is not None else 1, access=dto.access if dto.access is not None else 0, inherit=dto.inherit if dto.inherit is not None else 0, description=dto.description)
        config = await self.config_repo.create(config, session=self.session)
        await self.session.flush()
        return self._to_response(config)

    async def get_config(self, config_id: str) -> SystemConfigResponseDTO:
        """根据ID获取配置。"""
        config = await self.config_repo.get_by_id(config_id, session=self.session)
        if config is None:
            raise NotFoundError(f"配置 ID '{config_id}' 不存在")
        return self._to_response(config)

    async def get_configs(self, query: SystemConfigListQueryDTO) -> tuple[list[SystemConfigResponseDTO], int]:
        """获取配置列表。"""
        total = await self.config_repo.count(key=query.key, is_active=query.isActive, session=self.session)
        configs = await self.config_repo.get_all(page_num=query.pageNum, page_size=query.pageSize, key=query.key, is_active=query.isActive, session=self.session)
        return [self._to_response(c) for c in configs], total

    async def update_config(self, config_id: str, dto: SystemConfigUpdateDTO) -> SystemConfigResponseDTO:
        """更新配置。"""
        config = await self.config_repo.get_by_id(config_id, session=self.session)
        if config is None:
            raise NotFoundError(f"配置 ID '{config_id}' 不存在")

        if dto.key is not None:
            existing = await self.config_repo.get_by_key(dto.key, session=self.session)
            if existing and existing.id != config_id:
                raise ConflictError(f"配置键 '{dto.key}' 已存在")
            config.key = dto.key

        if dto.value is not None:
            config.value = dto.value
        if dto.isActive is not None:
            config.is_active = dto.isActive
        if dto.access is not None:
            config.access = dto.access
        if dto.inherit is not None:
            config.inherit = dto.inherit
        if dto.description is not None:
            config.description = dto.description

        config = await self.config_repo.update(config, session=self.session)
        await self.session.flush()
        return self._to_response(config)

    async def delete_config(self, config_id: str) -> bool:
        """删除配置。"""
        if not await self.config_repo.delete(config_id, session=self.session):
            raise NotFoundError(f"配置 ID '{config_id}' 不存在")
        return True

    @staticmethod
    def _to_response(config: SystemConfig) -> SystemConfigResponseDTO:
        """将 SystemConfig 模型转换为响应 DTO。"""
        return SystemConfigResponseDTO(id=config.id, key=config.key, value=config.value, isActive=config.is_active, access=config.access, inherit=config.inherit, creatorId=config.creator_id, modifierId=config.modifier_id, createdTime=config.created_time, updatedTime=config.updated_time, description=config.description)
