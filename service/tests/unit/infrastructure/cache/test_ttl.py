"""缓存 TTL 计算助手 remaining_seconds 的单元测试。

重点覆盖 ceil 语义：调用方的 expires_at 通常由「now + 配置秒数」得到，
两次 now() 之间的微小间隔会让 int 截断少 1 秒，向上取整保证条目至少存活到预期时刻。
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.infrastructure.cache.ttl import remaining_seconds


@pytest.mark.unit
class TestRemainingSeconds:
    """剩余秒数计算测试。"""

    def test_future(self):
        """测试计算未来时间的剩余秒数。"""
        expires = datetime.now(timezone.utc) + timedelta(seconds=100)
        # 允许 ±2 秒误差
        assert 98 <= remaining_seconds(expires) <= 100

    def test_past_returns_zero(self):
        """测试计算过去时间的剩余秒数（返回 0）。"""
        expires = datetime.now(timezone.utc) - timedelta(hours=1)
        assert remaining_seconds(expires) == 0

    def test_now_returns_zero(self):
        """测试计算刚好过期的时间（返回 0）。"""
        assert remaining_seconds(datetime.now(timezone.utc)) == 0

    def test_naive_datetime(self):
        """测试 naive datetime 入参（无时区信息）按 UTC 处理。"""
        expires = datetime.now(timezone.utc) + timedelta(seconds=200)
        assert 198 <= remaining_seconds(expires.replace(tzinfo=None)) <= 200

    def test_far_future(self):
        """测试很远的未来时间。"""
        expires = datetime.now(timezone.utc) + timedelta(days=365)
        result = remaining_seconds(expires)
        assert result > 0
        assert isinstance(result, int)

    def test_rounds_up_instead_of_truncating(self):
        """微小时间间隔不得把 TTL 截断少 1 秒。"""
        expires = datetime.now(timezone.utc) + timedelta(seconds=1)
        assert remaining_seconds(expires) == 1
