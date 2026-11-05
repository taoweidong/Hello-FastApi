"""RedisOnlineSessionStore 的单元测试。

覆盖在线会话登记/查询/删除的 Redis 主存储路径，以及 Redis 不可用、写入或遍历异常时
的内存镜像降级路径（登录登记与监控查询必须读到同一镜像）。
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.cache.online_session_store import RedisOnlineSessionStore


def _async_iter(items):
    """构造异步迭代器（模拟 redis scan_iter 的 async generator）。"""

    async def gen():
        for item in items:
            yield item

    return gen()


@pytest.mark.unit
class TestOnlineUsers:
    """在线用户会话操作测试。"""

    _expires = datetime.now(timezone.utc) + timedelta(hours=1)

    # ── set_online_user ──

    @pytest.mark.asyncio
    async def test_set_online_user_success(self):
        """成功登记在线用户会话，Key 使用 online:user: 前缀。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        store = RedisOnlineSessionStore(redis_client=mock_redis)
        info = {"userId": "u1", "username": "admin", "system": "Windows", "browser": "Chrome"}

        result = await store.set_online_user("abc123", info, self._expires)
        assert result is True
        key, value = mock_redis.set.await_args.args[0], mock_redis.set.await_args.args[1]
        assert key == f"{RedisOnlineSessionStore._ONLINE_USER_PREFIX}abc123"
        assert json.loads(value) == info
        assert mock_redis.set.await_args.kwargs["ex"] > 0

    @pytest.mark.asyncio
    async def test_set_online_user_no_redis(self):
        """Redis 不可用时登记会话（写入内存镜像）。"""
        store = RedisOnlineSessionStore()
        result = await store.set_online_user("abc123", {"username": "admin"}, self._expires)
        assert result is True
        assert (await store.get_online_user("abc123")) == {"username": "admin"}

    @pytest.mark.asyncio
    async def test_set_online_user_redis_error(self):
        """Redis 写入异常时降级为内存存储（返回 True 且会话可读）。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(side_effect=Exception("连接失败"))
        store = RedisOnlineSessionStore(redis_client=mock_redis)
        info = {"username": "admin"}

        result = await store.set_online_user("abc123", info, self._expires)
        assert result is True
        # 降级后内存镜像仍可读取该会话
        assert store._memory["abc123"]["info"] == info

    @pytest.mark.asyncio
    async def test_set_online_user_expired_is_skipped(self):
        """已过期的会话不登记，并清理镜像中的同 Key 条目。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        store = RedisOnlineSessionStore(redis_client=mock_redis)
        await store.set_online_user("abc123", {"username": "admin"}, self._expires)

        result = await store.set_online_user("abc123", {"username": "admin"}, datetime.now(timezone.utc))
        assert result is True
        assert store._memory == {}

    # ── get_online_user ──

    @pytest.mark.asyncio
    async def test_get_online_user_hit(self):
        """命中时返回会话信息字典。"""
        mock_redis = MagicMock()
        info = {"userId": "u1", "username": "admin"}
        mock_redis.get = AsyncMock(return_value=json.dumps(info))
        store = RedisOnlineSessionStore(redis_client=mock_redis)

        result = await store.get_online_user("abc123")
        assert result == info
        mock_redis.get.assert_called_once_with(f"{RedisOnlineSessionStore._ONLINE_USER_PREFIX}abc123")

    @pytest.mark.asyncio
    async def test_get_online_user_miss(self):
        """未命中时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        store = RedisOnlineSessionStore(redis_client=mock_redis)

        assert await store.get_online_user("abc123") is None

    @pytest.mark.asyncio
    async def test_get_online_user_no_redis(self):
        """Redis 不可用且镜像为空时返回 None。"""
        assert await RedisOnlineSessionStore().get_online_user("abc123") is None

    @pytest.mark.asyncio
    async def test_get_online_user_falls_back_to_memory_on_redis_error(self):
        """Redis 读取异常时降级读取内存镜像。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("连接失败"))
        store = RedisOnlineSessionStore(redis_client=mock_redis)
        await store.set_online_user("abc123", {"username": "admin"}, self._expires)

        assert await store.get_online_user("abc123") == {"username": "admin"}

    @pytest.mark.asyncio
    async def test_get_online_user_skips_expired_memory_entry(self):
        """内存镜像中已过期的条目读取时被惰性清理。"""
        store = RedisOnlineSessionStore()
        store._memory["abc123"] = {
            "info": {"username": "admin"},
            "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
        }

        assert await store.get_online_user("abc123") is None
        assert store._memory == {}

    # ── get_online_users ──

    @pytest.mark.asyncio
    async def test_get_online_users_returns_sessions_with_id(self):
        """遍历 Redis 前缀返回会话列表，并追加 id=session_key。"""
        mock_redis = MagicMock()
        info = {"username": "admin", "system": "Windows"}
        mock_redis.scan_iter = lambda match, count: _async_iter(
            [
                f"{RedisOnlineSessionStore._ONLINE_USER_PREFIX}hash1",
                f"{RedisOnlineSessionStore._ONLINE_USER_PREFIX}hash2",
            ]
        )
        mock_redis.get = AsyncMock(side_effect=[json.dumps(info), None])
        store = RedisOnlineSessionStore(redis_client=mock_redis)

        result = await store.get_online_users()
        assert len(result) == 1
        assert result[0]["id"] == "hash1"
        assert result[0]["username"] == "admin"

    @pytest.mark.asyncio
    async def test_get_online_users_no_redis(self):
        """Redis 不可用时返回镜像中的会话。"""
        store = RedisOnlineSessionStore()
        await store.set_online_user("abc123", {"username": "admin"}, self._expires)

        assert await store.get_online_users() == [{"username": "admin", "id": "abc123"}]

    @pytest.mark.asyncio
    async def test_get_online_users_redis_error(self):
        """遍历异常时降级读取内存镜像。"""
        mock_redis = MagicMock()

        def boom(match, count):
            raise Exception("连接失败")

        mock_redis.scan_iter = boom
        mock_redis.set = AsyncMock()
        store = RedisOnlineSessionStore(redis_client=mock_redis)
        await store.set_online_user("abc123", {"username": "admin"}, self._expires)

        assert await store.get_online_users() == [{"username": "admin", "id": "abc123"}]

    # ── delete_online_user ──

    @pytest.mark.asyncio
    async def test_delete_online_user_success(self):
        """强制下线删除会话，Key 使用 online:user: 前缀。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock()
        store = RedisOnlineSessionStore(redis_client=mock_redis)

        result = await store.delete_online_user("abc123")
        assert result is True
        mock_redis.delete.assert_called_once_with(f"{RedisOnlineSessionStore._ONLINE_USER_PREFIX}abc123")

    @pytest.mark.asyncio
    async def test_delete_online_user_no_redis(self):
        """Redis 不可用时删除会话（同步清理镜像）。"""
        store = RedisOnlineSessionStore()
        await store.set_online_user("abc123", {"username": "admin"}, self._expires)

        assert await store.delete_online_user("abc123") is True
        assert await store.get_online_user("abc123") is None

    @pytest.mark.asyncio
    async def test_delete_online_user_redis_error(self):
        """Redis 删除异常时返回 False，但镜像条目已清理。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("连接失败"))
        store = RedisOnlineSessionStore(redis_client=mock_redis)

        assert await store.delete_online_user("abc123") is False
        assert "abc123" not in store._memory
