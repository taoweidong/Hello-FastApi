"""字典应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.dictionary_service import DictionaryService
from src.domain.services.cache_port import DictCachePort


async def get_dictionary_service(
    repos: RepoBundle = Depends(get_repositories), cache_service: DictCachePort = Depends(get_cache_service)
) -> DictionaryService:
    """获取字典服务实例。

    注入字典仓储与缓存端口依赖（缓存端口用于字典取数接口的读写与失效）。
    """
    return DictionaryService(dict_repo=repos.dictionary, cache_service=cache_service)
