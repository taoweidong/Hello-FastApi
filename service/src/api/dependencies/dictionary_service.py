"""字典应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.dictionary_service import DictionaryService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.dictionary_repository import DictionaryRepository


async def get_dictionary_service(db: AsyncSession = Depends(get_db)) -> DictionaryService:
    """获取字典服务实例。

    注入字典仓储依赖。
    """
    dict_repo = DictionaryRepository(db)
    return DictionaryService(dict_repo=dict_repo)
