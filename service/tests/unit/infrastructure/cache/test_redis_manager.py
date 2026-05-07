"""RedisManager 单元测试。

测试 Redis 客户端生命周期的管理功能，包括客户端创建、获取、关闭，
以及模块级单例函数和兼容接口函数。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.cache.redis_manager import RedisManager, _get_redis_manager, close_redis, get_redis


@pytest.mark.unit
class TestRedisManagerInit:
    """RedisManager 初始化测试。"""

    def test_init_with_custom_url(self):
        """测试指定 URL 初始化。"""
        mgr = RedisManager(redis_url="redis://custom:6379/1")
        assert mgr._url == "redis://custom:6379/1"
        assert mgr._client is None

    def test_init_with_default_url(self):
        """测试未指定 URL 时使用 settings 默认值。"""
        mgr = RedisManager()
        assert mgr._url is not None
        assert mgr._client is None

    def test_init_with_custom_encoding(self):
        """测试指定编码参数。"""
        mgr = RedisManager(encoding="gbk")
        assert mgr._encoding == "gbk"

    def test_init_without_decode_responses(self):
        """测试 decode_responses 默认为 True。"""
        mgr = RedisManager()
        assert mgr._decode_responses is True

    def test_init_with_false_decode_responses(self):
        """测试指定 decode_responses 为 False。"""
        mgr = RedisManager(decode_responses=False)
        assert mgr._decode_responses is False


@pytest.mark.unit
class TestRedisManagerGetClient:
    """RedisManager.get_client 测试。"""

    @pytest.mark.asyncio
    async def test_get_client_creates_new_client(self):
        """测试首次调用时创建新客户端。"""
        mgr = RedisManager(redis_url="redis://localhost:6379/0")
        assert mgr._client is None

        with patch("src.infrastructure.cache.redis_manager.redis.from_url") as mock_from_url:
            mock_from_url.return_value = MagicMock()
            client = await mgr.get_client()

        assert client is mgr._client
        mock_from_url.assert_called_once_with(
            "redis://localhost:6379/0", encoding="utf-8", decode_responses=True
        )

    @pytest.mark.asyncio
    async def test_get_client_returns_existing(self):
        """测试重复调用返回同一客户端。"""
        mgr = RedisManager(redis_url="redis://localhost:6379/0")
        existing = MagicMock()
        mgr._client = existing

        with patch("src.infrastructure.cache.redis_manager.redis.from_url") as mock_from_url:
            client = await mgr.get_client()

        assert client is existing
        mock_from_url.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_client_uses_custom_encoding(self):
        """测试自定义编码参数传递。"""
        mgr = RedisManager(redis_url="redis://localhost:6379/0", encoding="gbk", decode_responses=False)

        with patch("src.infrastructure.cache.redis_manager.redis.from_url") as mock_from_url:
            mock_from_url.return_value = MagicMock()
            await mgr.get_client()

        mock_from_url.assert_called_once_with(
            "redis://localhost:6379/0", encoding="gbk", decode_responses=False
        )


@pytest.mark.unit
class TestRedisManagerClose:
    """RedisManager.close 测试。"""

    @pytest.mark.asyncio
    async def test_close_with_client(self):
        """测试有关联客户端时关闭连接。"""
        mgr = RedisManager()
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        mgr._client = mock_client

        await mgr.close()

        mock_client.aclose.assert_called_once()
        assert mgr._client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """测试无客户端时 close 不报错。"""
        mgr = RedisManager()
        assert mgr._client is None

        await mgr.close()  # should not raise

    @pytest.mark.asyncio
    async def test_close_idempotent(self):
        """测试 close 多次调用幂等。"""
        mgr = RedisManager()
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        mgr._client = mock_client

        await mgr.close()
        await mgr.close()

        mock_client.aclose.assert_called_once()
        assert mgr._client is None


@pytest.mark.unit
class TestRedisManagerModuleFunctions:
    """模块级单例与兼容函数测试。"""

    def setup_method(self):
        self.global_patch = patch(
            "src.infrastructure.cache.redis_manager._redis_manager", None
        )
        self.global_patch.start()

    def teardown_method(self):
        self.global_patch.stop()

    def test_get_redis_manager_returns_singleton(self):
        """测试 _get_redis_manager 返回单例。"""
        mgr1 = _get_redis_manager()
        mgr2 = _get_redis_manager()
        assert mgr1 is mgr2

    def test_get_redis_manager_creates_on_first_call(self):
        """测试首次调用 _get_redis_manager 创建实例。"""
        from src.infrastructure.cache.redis_manager import _redis_manager

        assert _redis_manager is None
        mgr = _get_redis_manager()
        assert mgr is not None

    @pytest.mark.asyncio
    async def test_get_redis_returns_client(self):
        """测试 get_redis 兼容函数返回客户端。"""
        with patch.object(RedisManager, "get_client", AsyncMock(return_value="fake-client")):
            client = await get_redis()
        assert client == "fake-client"

    @pytest.mark.asyncio
    async def test_close_redis_with_manager(self):
        """测试 close_redis 关闭管理器并置空。"""
        import src.infrastructure.cache.redis_manager as rm_mod

        mgr = RedisManager()
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        mgr._client = mock_client
        rm_mod._redis_manager = mgr

        await close_redis()
        assert rm_mod._redis_manager is None

    @pytest.mark.asyncio
    async def test_close_redis_without_manager(self):
        """测试无管理器时 close_redis 不报错。"""
        await close_redis()  # should not raise

    @pytest.mark.asyncio
    async def test_close_redis_with_manager_no_client(self):
        """测试管理器无客户端时 close_redis 不报错。"""
        import src.infrastructure.cache.redis_manager as rm_mod

        mgr = RedisManager()
        rm_mod._redis_manager = mgr
        await close_redis()
        assert rm_mod._redis_manager is None


@pytest.mark.unit
class TestRedisManagerGetClientEdgeCases:
    """RedisManager.get_client 异常路径。"""

    @pytest.mark.asyncio
    async def test_get_client_from_url_error(self):
        """测试 redis.from_url 抛出异常。"""
        mgr = RedisManager(redis_url="redis://invalid:6379/0")
        with (
            patch("src.infrastructure.cache.redis_manager.redis.from_url", side_effect=Exception("连接失败")),
            pytest.raises(Exception),  # noqa: B017
        ):
            await mgr.get_client()


@pytest.mark.unit
class TestRedisManagerCloseEdgeCases:
    """RedisManager.close 异常路径。"""

    @pytest.mark.asyncio
    async def test_close_client_error(self):
        """测试 client.aclose 抛出异常时向上传播。"""
        mgr = RedisManager()
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock(side_effect=Exception("关闭失败"))
        mgr._client = mock_client

        with pytest.raises(Exception, match="关闭失败"):  # noqa: B017
            await mgr.close()
