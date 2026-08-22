"""缓存服务工厂测试。"""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_cache_service_singleton():
    """每个用例前重置模块级单例，避免测试间相互污染。"""
    from src.api.dependencies import cache_service

    cache_service._cache_service = None
    yield
    cache_service._cache_service = None


@pytest.mark.unit
class TestGetCacheService:
    """get_cache_service 函数测试。"""

    @patch("src.api.dependencies.cache_service.get_redis")
    async def test_returns_cache_service_with_redis(self, mock_get_redis):
        """Redis 可用时应返回带 Redis 客户端的 CacheService。"""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis

        from src.api.dependencies.cache_service import get_cache_service

        service = await get_cache_service()
        from src.infrastructure.cache.cache_service import CacheService

        assert isinstance(service, CacheService)
        assert service._redis == mock_redis

    @patch("src.api.dependencies.cache_service.get_redis")
    async def test_returns_cache_service_without_redis_on_exception(self, mock_get_redis):
        """Redis 不可用时应有降级行为。"""
        mock_get_redis.side_effect = Exception("Redis unavailable")

        from src.api.dependencies.cache_service import get_cache_service

        service = await get_cache_service()
        from src.infrastructure.cache.cache_service import CacheService

        assert isinstance(service, CacheService)
        assert service._redis is None
