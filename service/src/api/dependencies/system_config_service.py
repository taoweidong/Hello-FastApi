"""系统配置应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.system_config_service import SystemConfigService


async def get_system_config_service(repos: RepoBundle = Depends(get_repositories)) -> SystemConfigService:
    """获取系统配置服务实例（仓储来自请求级仓储束，事务约定见 repositories.py）。"""
    return SystemConfigService(config_repo=repos.system_config)
