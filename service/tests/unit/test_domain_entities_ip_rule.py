"""IP规则领域实体的单元测试。

测试 IPRuleEntity 的所有状态查询属性、业务规则方法和工厂方法。
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.ip_rule import IPRuleEntity


@pytest.mark.unit
class TestIPRuleEntity:
    """IPRuleEntity 测试类。"""

    # ---- 类型常量测试 ----

    def test_whitelist_constant(self):
        """测试 WHITELIST 类型常量。"""
        assert IPRuleEntity.WHITELIST == "whitelist"

    def test_blacklist_constant(self):
        """测试 BLACKLIST 类型常量。"""
        assert IPRuleEntity.BLACKLIST == "blacklist"

    # ---- 状态查询属性测试 ----

    def test_is_whitelist_when_whitelist(self):
        """测试 is_whitelist 属性（白名单）。"""
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="whitelist")
        assert rule.is_whitelist is True
        assert rule.is_blacklist is False

    def test_is_blacklist_when_blacklist(self):
        """测试 is_blacklist 属性（黑名单）。"""
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist")
        assert rule.is_blacklist is True
        assert rule.is_whitelist is False

    def test_is_expired_when_no_expiration(self):
        """测试 is_expired 属性（无过期时间）。"""
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist", expires_at=None)
        assert rule.is_expired is False

    def test_is_expired_when_not_expired(self):
        """测试 is_expired 属性（未过期）。"""
        future = datetime.now(timezone.utc) + timedelta(days=1)
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist", expires_at=future)
        assert rule.is_expired is False

    def test_is_expired_when_expired(self):
        """测试 is_expired 属性（已过期）。"""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist", expires_at=past)
        assert rule.is_expired is True

    def test_is_expired_with_naive_datetime(self):
        """测试 is_expired 属性（兼容 naive datetime - 1天前）。"""
        # 使用1天前的 naive datetime，应该已过期
        past = datetime.now() - timedelta(days=1)
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist", expires_at=past)
        # naive datetime 在比较时会添加 UTC tzinfo，然后与当前时间比较
        assert rule.is_expired is True

    def test_is_effective_when_active_and_not_expired(self):
        """测试 is_effective 属性（启用且未过期）。"""
        future = datetime.now(timezone.utc) + timedelta(days=1)
        rule = IPRuleEntity(
            id="rule-1",
            ip_address="192.168.1.1",
            rule_type="blacklist",
            is_active=1,
            expires_at=future,
        )
        assert rule.is_effective is True

    def test_is_effective_when_inactive(self):
        """测试 is_effective 属性（未启用）。"""
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist", is_active=0)
        assert rule.is_effective is False

    def test_is_effective_when_expired(self):
        """测试 is_effective 属性（已过期）。"""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist", is_active=1, expires_at=past)
        assert rule.is_effective is False

    # ---- 状态变更方法测试 ----

    def test_update_info_with_all_fields(self):
        """测试 update_info 方法（更新所有字段）。"""
        future = datetime.now(timezone.utc) + timedelta(days=1)
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist")
        rule.update_info(
            ip_address="10.0.0.1",
            rule_type="whitelist",
            reason="测试原因",
            is_active=1,
            expires_at=future,
            description="描述",
        )
        assert rule.ip_address == "10.0.0.1"
        assert rule.rule_type == "whitelist"
        assert rule.reason == "测试原因"
        assert rule.is_active == 1
        assert rule.expires_at == future
        assert rule.description == "描述"

    def test_update_info_with_partial_fields(self):
        """测试 update_info 方法（部分字段）。"""
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist")
        rule.update_info(ip_address="10.0.0.1", reason="允许访问")
        assert rule.ip_address == "10.0.0.1"
        assert rule.reason == "允许访问"
        assert rule.rule_type == "blacklist"

    def test_update_info_ignore_none_fields(self):
        """测试 update_info 方法（忽略 None 字段）。"""
        rule = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist", reason="原始原因")
        rule.update_info(ip_address=None, reason=None)
        assert rule.ip_address == "192.168.1.1"
        assert rule.reason == "原始原因"

    # ---- 工厂方法测试 ----

    def test_create_new_whitelist(self):
        """测试 create_new 工厂方法（白名单）。"""
        future = datetime.now(timezone.utc) + timedelta(days=1)
        rule = IPRuleEntity.create_new(
            ip_address="192.168.1.0/24",
            rule_type="whitelist",
            reason="内网访问",
            is_active=1,
            expires_at=future,
            description="内网白名单",
        )
        assert rule.id is not None
        assert len(rule.id) == 32
        assert rule.ip_address == "192.168.1.0/24"
        assert rule.rule_type == "whitelist"
        assert rule.reason == "内网访问"
        assert rule.is_active == 1
        assert rule.expires_at == future
        assert rule.description == "内网白名单"

    def test_create_new_blacklist(self):
        """测试 create_new 工厂方法（黑名单）。"""
        rule = IPRuleEntity.create_new(ip_address="192.168.1.1", rule_type="blacklist", reason="禁止访问")
        assert rule.rule_type == "blacklist"
        assert rule.reason == "禁止访问"

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        rule = IPRuleEntity.create_new(ip_address="192.168.1.1")
        assert rule.ip_address == "192.168.1.1"
        assert rule.rule_type == "blacklist"
        assert rule.is_active == 1
        assert rule.reason is None
        assert rule.expires_at is None
