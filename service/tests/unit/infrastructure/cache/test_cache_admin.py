"""CacheAdminPort 实现（CacheService 缓存清单与清理）单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.cache.cache_service import CacheService


def make_redis(groups: dict[str, list[str]]):
    """构造模拟 Redis 客户端：groups 为 前缀 -> 键列表。"""
    client = MagicMock()
    all_keys = {k for keys in groups.values() for k in keys}

    def scan_iter(match=None):
        prefix = (match or "*").rstrip("*")
        keys = [k for k in sorted(all_keys) if k.startswith(prefix)]

        async def gen():
            for k in keys:
                yield k

        return gen()

    client.scan_iter = scan_iter
    client.delete = AsyncMock(side_effect=lambda *keys: sum(1 for k in keys if k in all_keys))
    return client


@pytest.mark.unit
class TestGetCacheGroups:
    async def test_returns_all_groups_with_counts(self):
        redis = make_redis(
            {
                "user:info:": ["user:info:u1", "user:info:u2"],
                "user:perms:": ["user:perms:u1"],
                "dict:": [],
                "token:blacklist:": ["token:blacklist:abc"],
            }
        )
        svc = CacheService(redis_client=redis)

        groups = await svc.get_cache_groups()

        by_key = {g["key"]: g for g in groups}
        assert len(groups) == 6
        assert by_key["user_info"]["count"] == 2
        assert by_key["user_perms"]["count"] == 1
        assert by_key["user_info"]["clearable"] is True
        # 安全红线：令牌黑名单只读不清理
        assert by_key["token_blacklist"]["clearable"] is False
        assert by_key["token_blacklist"]["count"] == 1

    async def test_degrades_to_none_without_redis(self):
        svc = CacheService(redis_client=None)
        assert await svc.get_cache_groups() is None


@pytest.mark.unit
class TestClearCacheGroup:
    async def test_clears_matching_keys_and_returns_count(self):
        redis = make_redis({"user:info:": ["user:info:u1", "user:info:u2"]})
        svc = CacheService(redis_client=redis)

        deleted = await svc.clear_cache_group("user_info")

        assert deleted == 2
        redis.delete.assert_awaited_once()

    async def test_unknown_group_raises(self):
        svc = CacheService(redis_client=make_redis({}))
        with pytest.raises(ValueError, match="未知的缓存分组"):
            await svc.clear_cache_group("nope")

    async def test_blacklist_group_is_untouchable(self):
        """安全红线：令牌黑名单组禁止清理（清理会使已登出令牌复活）。"""
        svc = CacheService(redis_client=make_redis({"token:blacklist:": ["token:blacklist:abc"]}))
        with pytest.raises(ValueError, match="不允许清理"):
            await svc.clear_cache_group("token_blacklist")

    async def test_degrades_to_none_without_redis(self):
        svc = CacheService(redis_client=None)
        assert await svc.clear_cache_group("user_info") is None


@pytest.mark.unit
class TestClearAllBusinessCache:
    async def test_sums_clearable_groups_and_skips_blacklist(self):
        redis = make_redis(
            {
                "user:info:": ["user:info:u1"],
                "user:perms:": ["user:perms:u1", "user:perms:u2"],
                "menu:all": ["menu:all"],
                "dict:": ["dict:sys"],
                "ip:rules": ["ip:rules"],
                "token:blacklist:": ["token:blacklist:abc", "token:blacklist:def"],
            }
        )
        svc = CacheService(redis_client=redis)

        deleted = await svc.clear_all_business_cache()

        # 1+2+1+1+1 = 6；黑名单 2 个键必须保留（不在可清理集合内）
        assert deleted == 6

    async def test_degrades_to_none_without_redis(self):
        svc = CacheService(redis_client=None)
        assert await svc.clear_all_business_cache() is None
