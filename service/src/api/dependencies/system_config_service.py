"""系统配置应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.system_config_service import SystemConfigService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.system_config_repository import SystemConfigRepository


async def get_system_config_service(db: AsyncSession = Depends(get_db)) -> SystemConfigService:
    """获取系统配置服务实例。"""
    config_repo = SystemConfigRepository(db)
    return SystemConfigService(config_repo=config_repo)
