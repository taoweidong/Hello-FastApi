"""应用层 - 系统配置服务。"""

from src.application.dto.system_config_dto import (
    SystemConfigCreateDTO,
    SystemConfigListQueryDTO,
    SystemConfigResponseDTO,
    SystemConfigUpdateDTO,
)
from src.domain.entities.system_config import SystemConfigEntity
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories.system_config_repository import SystemConfigRepositoryInterface


class SystemConfigService:
    """系统配置操作的应用服务。"""

    def __init__(self, config_repo: SystemConfigRepositoryInterface):
        self.config_repo = config_repo

    async def create_config(self, dto: SystemConfigCreateDTO) -> SystemConfigResponseDTO:
        """创建系统配置。"""
        # 检查key唯一性
        existing = await self.config_repo.get_by_key(dto.key)
        if existing:
            raise ConflictError(f"配置键 '{dto.key}' 已存在")

        config_entity = SystemConfigEntity.create_new(key=dto.key, value=dto.value, description=dto.description)
        if dto.isActive is not None:
            config_entity.is_active = dto.isActive
        if dto.access is not None:
            config_entity.access = dto.access
        if dto.inherit is not None:
            config_entity.inherit = dto.inherit

        created = await self.config_repo.create(config_entity)
        return self._to_response(created)

    async def get_config(self, config_id: str) -> SystemConfigResponseDTO:
        """根据ID获取配置。"""
        config = await self.config_repo.get_by_id(config_id)
        if config is None:
            raise NotFoundError(f"配置 ID '{config_id}' 不存在")
        return self._to_response(config)

    async def get_configs(self, query: SystemConfigListQueryDTO) -> tuple[list[SystemConfigResponseDTO], int]:
        """获取配置列表。"""
        total = await self.config_repo.count(key=query.key, is_active=query.isActive)
        configs = await self.config_repo.get_all(
            page_num=query.pageNum, page_size=query.pageSize, key=query.key, is_active=query.isActive
        )
        return [self._to_response(c) for c in configs], total

    async def update_config(self, config_id: str, dto: SystemConfigUpdateDTO) -> SystemConfigResponseDTO:
        """更新配置。"""
        config = await self.config_repo.get_by_id(config_id)
        if config is None:
            raise NotFoundError(f"配置 ID '{config_id}' 不存在")

        if dto.key is not None:
            existing = await self.config_repo.get_by_key(dto.key)
            if existing and existing.id != config_id:
                raise ConflictError(f"配置键 '{dto.key}' 已存在")

        config.update_info(
            value=dto.value,
            is_active=dto.isActive,
            access=dto.access,
            key=dto.key,
            inherit=dto.inherit,
            description=dto.description,
        )
        updated = await self.config_repo.update(config)
        return self._to_response(updated)

    async def delete_config(self, config_id: str) -> bool:
        """删除配置。"""
        if not await self.config_repo.delete(config_id):
            raise NotFoundError(f"配置 ID '{config_id}' 不存在")
        return True

    @staticmethod
    def _to_response(config: SystemConfigEntity) -> SystemConfigResponseDTO:
        """将系统配置实体转换为响应 DTO。"""
        return SystemConfigResponseDTO(
            id=config.id,
            key=config.key,
            value=config.value,
            isActive=config.is_active,
            access=config.access,
            inherit=config.inherit,
            creatorId=config.creator_id,
            modifierId=config.modifier_id,
            createdTime=config.created_time,
            updatedTime=config.updated_time,
            description=config.description,
        )
