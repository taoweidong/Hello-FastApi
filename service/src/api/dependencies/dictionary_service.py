"""字典应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.cache_service import get_cache_service
from src.application.services.dictionary_service import DictionaryService
from src.domain.services.cache_port import CachePort
from src.infrastructure.database import get_db
from src.infrastructure.repositories.dictionary_repository import DictionaryRepository


async def get_dictionary_service(
    db: AsyncSession = Depends(get_db), cache_service: CachePort = Depends(get_cache_service)
) -> DictionaryService:
    """获取字典服务实例。

    注入字典仓储与缓存服务依赖（缓存服务用于字典取数接口的读写与失效）。
    """
    dict_repo = DictionaryRepository(db)
    return DictionaryService(dict_repo=dict_repo, cache_service=cache_service)
