"""字典应用服务工厂测试。"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestGetDictionaryService:
    """get_dictionary_service 函数测试。"""

    async def test_returns_dictionary_service(self):
        """应返回配置好的 DictionaryService，字典仓储取自请求级仓储束、缓存端口原样透传。"""
        from src.api.dependencies.dictionary_service import get_dictionary_service
        from src.api.dependencies.repositories import RepoBundle
        from src.application.services.dictionary_service import DictionaryService

        repos = RepoBundle(MagicMock())
        mock_cache = MagicMock()
        service = await get_dictionary_service(repos=repos, cache_service=mock_cache)

        assert isinstance(service, DictionaryService)
        assert service.dict_repo is repos.dictionary
        assert service.cache_service is mock_cache
