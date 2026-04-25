"""CacheService 的单元测试。

测试 Token 黑名单、用户权限缓存、用户信息缓存、菜单缓存、IP 规则缓存的
所有操作，包括正常路径、降级路径（Redis 不可用）、异常路径等。
"""

import json
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.cache.cache_service import CacheService


@pytest.mark.unit
class TestCacheServiceInit:
    """CacheService 初始化测试。"""

    def test_init_without_redis(self):
        """测试不带 Redis 客户端初始化。"""
        svc = CacheService()
        assert svc._redis is None

    def test_init_with_redis(self):
        """测试带 Redis 客户端初始化。"""
        mock_redis = MagicMock()
        svc = CacheService(redis_client=mock_redis)
        assert svc._redis is mock_redis

    def test_class_constants(self):
        """测试类常量定义正确。"""
        assert CacheService.PERMS_CACHE_TTL == 300
        assert CacheService.USER_INFO_CACHE_TTL == 300
        assert CacheService.MENU_ALL_CACHE_TTL == 600


@pytest.mark.unit
class TestTokenBlacklist:
    """Token 黑名单操作测试。"""

    # ── add_token_to_blacklist ──

    @pytest.mark.asyncio
    async def test_add_token_to_blacklist_success(self):
        """测试成功将 Token 加入黑名单。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        svc = CacheService(redis_client=mock_redis)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        result = await svc.add_token_to_blacklist("test-token", expires_at)
        assert result is True
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_token_to_blacklist_no_redis(self):
        """测试 Redis 不可用时加入黑名单（降级放行）。"""
        svc = CacheService()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        result = await svc.add_token_to_blacklist("test-token", expires_at)
        assert result is True

    @pytest.mark.asyncio
    async def test_add_token_already_expired(self):
        """测试已过期的 Token 无需加入黑名单。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        svc = CacheService(redis_client=mock_redis)
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        result = await svc.add_token_to_blacklist("test-token", expires_at)
        assert result is True
        mock_redis.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_token_to_blacklist_redis_error(self):
        """测试 Redis 写入异常时降级处理。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        result = await svc.add_token_to_blacklist("test-token", expires_at)
        assert result is False

    @pytest.mark.asyncio
    async def test_add_token_with_naive_datetime(self):
        """测试使用不带时区的 datetime 入参。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        svc = CacheService(redis_client=mock_redis)
        expires_at = datetime.now() + timedelta(hours=1)  # naive datetime

        result = await svc.add_token_to_blacklist("test-token", expires_at)
        assert result is True
        mock_redis.set.assert_called_once()

    # ── is_token_blacklisted ──

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_true(self):
        """测试 Token 在黑名单中。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="1")
        svc = CacheService(redis_client=mock_redis)

        result = await svc.is_token_blacklisted("test-token")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_false(self):
        """测试 Token 不在黑名单中。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        svc = CacheService(redis_client=mock_redis)

        result = await svc.is_token_blacklisted("test-token")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_no_redis(self):
        """测试 Redis 不可用时降级放行。"""
        svc = CacheService()

        result = await svc.is_token_blacklisted("test-token")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_redis_error(self):
        """测试 Redis 查询异常时降级放行。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.is_token_blacklisted("test-token")
        assert result is False

    @pytest.mark.asyncio
    async def test_same_token_same_blacklist_key(self):
        """测试相同 Token 产生相同的黑名单 Key。"""
        svc = CacheService()
        key1 = svc._blacklist_key("test-token")
        key2 = svc._blacklist_key("test-token")
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_different_tokens_different_keys(self):
        """测试不同 Token 产生不同的黑名单 Key。"""
        svc = CacheService()
        key1 = svc._blacklist_key("token-a")
        key2 = svc._blacklist_key("token-b")
        assert key1 != key2


@pytest.mark.unit
class TestUserPermissionsCache:
    """用户权限缓存操作测试。"""

    # ── get_user_permissions ──

    @pytest.mark.asyncio
    async def test_get_user_permissions_hit(self):
        """测试缓存命中时返回权限列表。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=json.dumps([{"role": "admin"}]))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_user_permissions("user-1")
        assert result == [{"role": "admin"}]

    @pytest.mark.asyncio
    async def test_get_user_permissions_miss(self):
        """测试缓存未命中时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_user_permissions("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_permissions_no_redis(self):
        """测试 Redis 不可用时返回 None。"""
        svc = CacheService()

        result = await svc.get_user_permissions("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_permissions_redis_error(self):
        """测试 Redis 读取异常时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_user_permissions("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_permissions_json_error(self):
        """测试缓存数据损坏（JSON 解析失败）时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="bad json {{{")
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_user_permissions("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_empty_permissions_list(self):
        """测试缓存命中但权限列表为空。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=json.dumps([]))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_user_permissions("user-1")
        assert result == []

    # ── set_user_permissions ──

    @pytest.mark.asyncio
    async def test_set_user_permissions_success(self):
        """测试成功写入用户权限缓存。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        result = await svc.set_user_permissions("user-1", [{"role": "admin"}])
        assert result is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "admin" in call_args[0][1]  # JSON value contains role

    @pytest.mark.asyncio
    async def test_set_user_permissions_no_redis(self):
        """测试 Redis 不可用时写入缓存。"""
        svc = CacheService()

        result = await svc.set_user_permissions("user-1", [{"role": "admin"}])
        assert result is False

    @pytest.mark.asyncio
    async def test_set_user_permissions_redis_error(self):
        """测试 Redis 写入异常时返回 False。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.set_user_permissions("user-1", [{"role": "admin"}])
        assert result is False

    @pytest.mark.asyncio
    async def test_set_permissions_uses_ttl(self):
        """测试写入权限缓存时使用了 TTL。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        await svc.set_user_permissions("user-1", [{"role": "admin"}])
        _, kwargs = mock_redis.set.call_args
        assert kwargs["ex"] == CacheService.PERMS_CACHE_TTL

    # ── invalidate_user_permissions ──

    @pytest.mark.asyncio
    async def test_invalidate_user_permissions_success(self):
        """测试成功使权限缓存失效。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        result = await svc.invalidate_user_permissions("user-1")
        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_user_permissions_no_redis(self):
        """测试 Redis 不可用时使缓存失效。"""
        svc = CacheService()

        result = await svc.invalidate_user_permissions("user-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_user_permissions_redis_error(self):
        """测试 Redis 删除异常时返回 False。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.invalidate_user_permissions("user-1")
        assert result is False


@pytest.mark.unit
class TestUserInfoCache:
    """用户信息缓存操作测试。"""

    @pytest.mark.asyncio
    async def test_get_user_info_hit(self):
        """测试缓存命中时返回用户信息。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({"name": "张三", "email": "zhangsan@test.com"}))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_user_info("user-1")
        assert result == {"name": "张三", "email": "zhangsan@test.com"}

    @pytest.mark.asyncio
    async def test_get_user_info_miss(self):
        """测试缓存未命中时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_user_info("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_info_no_redis(self):
        """测试 Redis 不可用。"""
        svc = CacheService()
        result = await svc.get_user_info("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_user_info_success(self):
        """测试成功写入用户信息。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        result = await svc.set_user_info("user-1", {"name": "张三"})
        assert result is True
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_user_info_no_redis(self):
        """测试 Redis 不可用时写入用户信息。"""
        svc = CacheService()
        result = await svc.set_user_info("user-1", {"name": "张三"})
        assert result is False

    @pytest.mark.asyncio
    async def test_set_user_info_uses_ttl(self):
        """测试写入用户信息时使用了 TTL。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        await svc.set_user_info("user-1", {"name": "张三"})
        _, kwargs = mock_redis.set.call_args
        assert kwargs["ex"] == CacheService.USER_INFO_CACHE_TTL

    @pytest.mark.asyncio
    async def test_invalidate_user_info_success(self):
        """测试成功使用户信息缓存失效。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        result = await svc.invalidate_user_info("user-1")
        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_user_info_no_redis(self):
        """测试 Redis 不可用时使缓存失效。"""
        svc = CacheService()
        result = await svc.invalidate_user_info("user-1")
        assert result is False


@pytest.mark.unit
class TestMenuCache:
    """菜单全表缓存操作测试。"""

    @pytest.mark.asyncio
    async def test_get_all_menus_hit(self):
        """测试缓存命中时返回菜单列表。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=json.dumps([{"id": 1, "name": "首页"}]))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_all_menus()
        assert result == [{"id": 1, "name": "首页"}]

    @pytest.mark.asyncio
    async def test_get_all_menus_miss(self):
        """测试缓存未命中时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_all_menus()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_menus_no_redis(self):
        """测试 Redis 不可用。"""
        svc = CacheService()
        result = await svc.get_all_menus()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_menus_empty_list(self):
        """测试缓存命中但菜单为空列表。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=json.dumps([]))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_all_menus()
        assert result == []

    @pytest.mark.asyncio
    async def test_set_all_menus_success(self):
        """测试成功写入菜单缓存。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        result = await svc.set_all_menus([{"id": 1, "name": "首页"}])
        assert result is True
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_all_menus_no_redis(self):
        """测试 Redis 不可用时写入菜单缓存。"""
        svc = CacheService()
        result = await svc.set_all_menus([{"id": 1}])
        assert result is False

    @pytest.mark.asyncio
    async def test_set_all_menus_uses_ttl(self):
        """测试写入菜单缓存时使用了 TTL。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        await svc.set_all_menus([{"id": 1}])
        _, kwargs = mock_redis.set.call_args
        assert kwargs["ex"] == CacheService.MENU_ALL_CACHE_TTL

    @pytest.mark.asyncio
    async def test_invalidate_all_menus_success(self):
        """测试成功使菜单缓存失效。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        result = await svc.invalidate_all_menus()
        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_all_menus_no_redis(self):
        """测试 Redis 不可用时使菜单缓存失效。"""
        svc = CacheService()
        result = await svc.invalidate_all_menus()
        assert result is False


@pytest.mark.unit
class TestIPRulesCache:
    """IP 规则缓存操作测试。"""

    @pytest.mark.asyncio
    async def test_set_ip_rules_success(self):
        """测试成功写入 IP 规则。"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.hset = MagicMock()
        mock_pipe.execute = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__ = AsyncMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__aexit__ = AsyncMock(return_value=False)
        svc = CacheService(redis_client=mock_redis)

        result = await svc.set_ip_rules({"192.168.1.1"}, {"10.0.0.1"})
        assert result is True
        assert mock_pipe.hset.call_count == 2

    @pytest.mark.asyncio
    async def test_set_ip_rules_no_redis(self):
        """测试 Redis 不可用时写入 IP 规则。"""
        svc = CacheService()
        result = await svc.set_ip_rules({"192.168.1.1"}, set())
        assert result is False

    @pytest.mark.asyncio
    async def test_set_ip_rules_redis_error(self):
        """测试 Redis 写入异常时返回 False。"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute = AsyncMock(side_effect=Exception("连接失败"))
        mock_redis.pipeline.return_value.__aenter__ = AsyncMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__aexit__ = AsyncMock(return_value=False)
        svc = CacheService(redis_client=mock_redis)

        result = await svc.set_ip_rules({"192.168.1.1"}, set())
        assert result is False

    @pytest.mark.asyncio
    async def test_get_ip_rules_hit(self):
        """测试缓存命中时返回 IP 规则。"""
        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(return_value={
            "blacklist": json.dumps(["192.168.1.1"]),
            "whitelist": json.dumps(["10.0.0.1"]),
        })
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_ip_rules()
        assert result == ({"192.168.1.1"}, {"10.0.0.1"})

    @pytest.mark.asyncio
    async def test_get_ip_rules_miss_empty_dict(self):
        """测试缓存未命中（空字典）时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(return_value={})
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_ip_rules()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ip_rules_miss_none(self):
        """测试 Redis hgetall 返回空（可能为 None 或空对象）。"""
        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(return_value=None)
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_ip_rules()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ip_rules_no_redis(self):
        """测试 Redis 不可用时返回 None。"""
        svc = CacheService()
        result = await svc.get_ip_rules()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ip_rules_redis_error(self):
        """测试 Redis 读取异常时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_ip_rules()
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_ip_rules_success(self):
        """测试成功使 IP 规则缓存失效。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock()
        svc = CacheService(redis_client=mock_redis)

        result = await svc.invalidate_ip_rules()
        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_ip_rules_no_redis(self):
        """测试 Redis 不可用时使缓存失效。"""
        svc = CacheService()
        result = await svc.invalidate_ip_rules()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_ip_rules_preserves_python_types(self):
        """测试返回的 IP 规则为 Python set 类型。"""
        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(return_value={
            "blacklist": json.dumps(["192.168.1.1", "192.168.1.2"]),
            "whitelist": json.dumps(["10.0.0.1"]),
        })
        svc = CacheService(redis_client=mock_redis)

        blacklist, whitelist = await svc.get_ip_rules()
        assert isinstance(blacklist, set)
        assert isinstance(whitelist, set)


@pytest.mark.unit
class TestInternalHelpers:
    """内部辅助方法测试。"""

    def test_blacklist_key_uses_sha256_prefix(self):
        """测试黑名单 Key 使用 SHA-256 哈希前缀。"""
        svc = CacheService()
        key = svc._blacklist_key("my-secret-token")
        expected_hash = hashlib.sha256("my-secret-token".encode()).hexdigest()[:32]
        assert key == f"token:blacklist:{expected_hash}"

    def test_blacklist_key_returns_string(self):
        """测试黑名单 Key 返回字符串。"""
        svc = CacheService()
        key = svc._blacklist_key("any-token")
        assert isinstance(key, str)
        assert key.startswith("token:blacklist:")

    def test_perms_key_format(self):
        """测试权限 Key 格式。"""
        svc = CacheService()
        key = svc._perms_key("user-42")
        assert key == "user:perms:user-42"

    def test_perms_key_matches_prefix(self):
        """测试权限 Key 包含正确的前缀。"""
        svc = CacheService()
        for uid in ["abc", "123", "test-user"]:
            key = svc._perms_key(uid)
            assert key.startswith(CacheService._PERMS_PREFIX)

    # ── _remaining_seconds ──

    def test_remaining_seconds_future(self):
        """测试计算未来时间的剩余秒数。"""
        expires = datetime.now(timezone.utc) + timedelta(seconds=100)
        remaining = CacheService._remaining_seconds(expires)
        # 允许 ±2 秒误差
        assert 98 <= remaining <= 100

    def test_remaining_seconds_past(self):
        """测试计算过去时间的剩余秒数（返回 0）。"""
        expires = datetime.now(timezone.utc) - timedelta(hours=1)
        remaining = CacheService._remaining_seconds(expires)
        assert remaining == 0

    def test_remaining_seconds_now(self):
        """测试计算刚好过期的时间（返回 0）。"""
        expires = datetime.now(timezone.utc)
        remaining = CacheService._remaining_seconds(expires)
        assert remaining == 0

    def test_remaining_seconds_naive_datetime(self):
        """测试 naive datetime 入参（无时区信息）。"""
        expires = datetime.now(timezone.utc) + timedelta(seconds=200)
        remaining = CacheService._remaining_seconds(expires)
        assert 198 <= remaining <= 200

    def test_remaining_seconds_far_future(self):
        """测试很远的未来时间。"""
        expires = datetime.now(timezone.utc) + timedelta(days=365)
        remaining = CacheService._remaining_seconds(expires)
        assert remaining > 0
        assert isinstance(remaining, int)

    def test_user_info_key_format(self):
        """测试用户信息 Key 格式。"""
        svc = CacheService()
        key = svc._user_info_key("user-7")
        assert key == "user:info:user-7"

    def test_user_info_key_prefix(self):
        """测试用户信息 Key 前缀。"""
        svc = CacheService()
        key = svc._user_info_key("any-id")
        assert key.startswith("user:info:")

    def test_blacklist_key_empty_token(self):
        """测试空 Token 的黑名单 Key。"""
        svc = CacheService()
        key = svc._blacklist_key("")
        assert isinstance(key, str)
        assert key.startswith("token:blacklist:")


@pytest.mark.unit
class TestUserInfoCacheEdgeCases:
    """用户信息缓存操作额外路径（异常/JSON解码）。"""

    @pytest.mark.asyncio
    async def test_get_user_info_json_error(self):
        """测试缓存数据损坏（JSON 解析失败）时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="{bad json")
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_user_info("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_info_redis_error(self):
        """测试 Redis 读取异常时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_user_info("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_user_info_redis_error(self):
        """测试 Redis 写入异常时返回 False。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.set_user_info("user-1", {"name": "张三"})
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_user_info_redis_error(self):
        """测试 Redis 删除异常时返回 False。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.invalidate_user_info("user-1")
        assert result is False


@pytest.mark.unit
class TestMenuCacheEdgeCases:
    """菜单缓存操作额外路径（异常/JSON解码）。"""

    @pytest.mark.asyncio
    async def test_get_all_menus_json_error(self):
        """测试缓存数据损坏时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="not json")
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_all_menus()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_menus_redis_error(self):
        """测试 Redis 读取异常时返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.get_all_menus()
        assert result is None

    @pytest.mark.asyncio
    async def test_set_all_menus_redis_error(self):
        """测试 Redis 写入异常时返回 False。"""
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.set_all_menus([{"id": 1}])
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_all_menus_redis_error(self):
        """测试 Redis 删除异常时返回 False。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.invalidate_all_menus()
        assert result is False


@pytest.mark.unit
class TestIPRulesCacheEdgeCases:
    """IP 规则缓存操作额外路径。"""

    @pytest.mark.asyncio
    async def test_invalidate_ip_rules_redis_error(self):
        """测试 Redis 删除异常时返回 False。"""
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("连接失败"))
        svc = CacheService(redis_client=mock_redis)

        result = await svc.invalidate_ip_rules()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_ip_rules_missing_blacklist(self):
        """测试 hgetall 缺少 blacklist 字段时返回空集合。"""
        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(return_value={
            "whitelist": json.dumps(["10.0.0.1"]),
        })
        svc = CacheService(redis_client=mock_redis)

        blacklist, whitelist = await svc.get_ip_rules()
        assert blacklist == set()
        assert whitelist == {"10.0.0.1"}

    @pytest.mark.asyncio
    async def test_get_ip_rules_missing_whitelist(self):
        """测试 hgetall 缺少 whitelist 字段时返回空集合。"""
        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(return_value={
            "blacklist": json.dumps(["192.168.1.1"]),
        })
        svc = CacheService(redis_client=mock_redis)

        blacklist, whitelist = await svc.get_ip_rules()
        assert blacklist == {"192.168.1.1"}
        assert whitelist == set()
