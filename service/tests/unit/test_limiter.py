"""限流模块测试。"""

import sys
from unittest.mock import MagicMock

import pytest
from slowapi import Limiter

from src.infrastructure.http.limiter import get_limiter, get_real_ip


class TestLimiterConfig:
    """限流器配置测试。"""

    def test_limiter_instance_exists(self):
        """测试限流器实例已创建。"""
        limiter = get_limiter()
        assert isinstance(limiter, Limiter)

    def test_limiter_has_default_limits(self):
        """测试限流器有默认限制配置。"""
        limiter = get_limiter()
        assert limiter._default_limits is not None
        assert len(limiter._default_limits) > 0

    def test_get_real_ip_without_proxy(self):
        """测试无代理时获取真实 IP。"""
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        assert get_real_ip(request) == "127.0.0.1"

    def test_get_real_ip_with_x_forwarded_for(self):
        """测试有 X-Forwarded-For 头时获取真实 IP。"""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "203.0.113.50, 70.41.3.18"}
        assert get_real_ip(request) == "203.0.113.50"

    def test_get_real_ip_with_single_forwarded_ip(self):
        """测试单个 X-Forwarded-For IP。"""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "10.0.0.1"}
        assert get_real_ip(request) == "10.0.0.1"


class TestRateLimitStorage:
    """限流存储测试。"""

    def test_storage_uri_returns_memory_when_configured(self):
        """测试配置为 memory 时返回 memory://。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "memory"
            REDIS_URL = "redis://localhost:6379/0"

        limiter_mod = sys.modules["src.infrastructure.http.limiter"]
        original = limiter_mod.settings
        limiter_mod.settings = MockSettings()
        try:
            assert limiter_mod._get_storage_uri() == "memory://"
        finally:
            limiter_mod.settings = original

    def test_storage_uri_returns_redis_when_available(self):
        """测试 Redis 可用时返回 redis URL。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "redis"
            REDIS_URL = "redis://localhost:6379/0"

        limiter_mod = sys.modules["src.infrastructure.http.limiter"]
        original = limiter_mod.settings
        limiter_mod.settings = MockSettings()
        try:
            assert limiter_mod._get_storage_uri() == "redis://localhost:6379/0"
        finally:
            limiter_mod.settings = original

    def test_storage_uri_fallback_to_memory(self):
        """测试 Redis 不可用时降级为 memory。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "redis"
            REDIS_URL = ""

        limiter_mod = sys.modules["src.infrastructure.http.limiter"]
        original = limiter_mod.settings
        limiter_mod.settings = MockSettings()
        try:
            assert limiter_mod._get_storage_uri() == "memory://"
        finally:
            limiter_mod.settings = original
