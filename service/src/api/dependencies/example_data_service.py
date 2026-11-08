"""示例数据应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.example_data_service import ExampleDataService
from src.domain.services.cache_port import CachePort


async def get_example_data_service(
    repos: RepoBundle = Depends(get_repositories), cache_service: CachePort | None = Depends(get_cache_service)
) -> ExampleDataService:
    """获取示例数据服务实例（仓储来自请求级仓储束，事务约定见 repositories.py）。"""
    return ExampleDataService(repo=repos.example_data, cache_service=cache_service)
