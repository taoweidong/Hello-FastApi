"""缓存端口工厂测试。"""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_cache_service_singletons():
    """每个用例前重置模块级单例，避免测试间相互污染。"""
    from src.api.dependencies import cache_service

    cache_service._cache_service = None
    cache_service._session_store = None
    yield
    cache_service._cache_service = None
    cache_service._session_store = None


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


@pytest.mark.unit
class TestGetOnlineSessionStore:
    """get_online_session_store 函数测试。"""

    @patch("src.api.dependencies.cache_service.get_redis")
    async def test_returns_store_with_redis(self, mock_get_redis):
        """Redis 可用时应返回带 Redis 客户端的会话存储。"""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis

        from src.api.dependencies.cache_service import get_online_session_store
        from src.infrastructure.cache.online_session_store import RedisOnlineSessionStore

        store = await get_online_session_store()

        assert isinstance(store, RedisOnlineSessionStore)
        assert store._redis is mock_redis

    @patch("src.api.dependencies.cache_service.get_redis")
    async def test_degrades_to_memory_only_store(self, mock_get_redis):
        """Redis 不可用时降级为仅内存镜像的存储（不抛异常）。"""
        mock_get_redis.side_effect = Exception("Redis unavailable")

        from src.api.dependencies.cache_service import get_online_session_store
        from src.infrastructure.cache.online_session_store import RedisOnlineSessionStore

        store = await get_online_session_store()

        assert isinstance(store, RedisOnlineSessionStore)
        assert store._redis is None

    @patch("src.api.dependencies.cache_service.get_redis")
    async def test_returns_same_singleton_instance(self, mock_get_redis):
        """必须返回同一实例：登录登记与监控查询要读到同一份内存镜像。"""
        mock_get_redis.side_effect = Exception("Redis unavailable")

        from src.api.dependencies.cache_service import get_online_session_store

        assert await get_online_session_store() is await get_online_session_store()
