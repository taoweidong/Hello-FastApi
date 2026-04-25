"""IPRule 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.ip_rule import IPRule


@pytest.mark.unit
class TestIPRuleModel:
    """IPRule ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_ip_rules。"""
        assert IPRule.__tablename__ == "sys_ip_rules"

    def test_is_sqlmodel_table(self):
        """IPRule 应继承 SQLModel 并映射为表。"""
        assert issubclass(IPRule, SQLModel)
        assert hasattr(IPRule, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        rule = IPRule(ip_address="192.168.1.1", rule_type="whitelist")
        assert rule.id is not None
        assert len(rule.id) == 32

    def test_field_defaults(self):
        """测试字段默认值。"""
        rule = IPRule(ip_address="192.168.1.1", rule_type="blacklist")
        assert rule.is_active == 1

    def test_optional_fields_default_none(self):
        """可选字段默认应为 None。"""
        rule = IPRule(ip_address="10.0.0.1", rule_type="whitelist")
        assert rule.reason is None
        assert rule.creator_id is None
        assert rule.modifier_id is None
        assert rule.created_time is None
        assert rule.updated_time is None
        assert rule.expires_at is None
        assert rule.description is None

    def test_field_max_length(self):
        """字段应有正确的 max_length 限制。"""
        assert IPRule.ip_address.type.length == 45
        assert IPRule.rule_type.type.length == 10
        assert IPRule.reason.type.length == 255
        assert IPRule.creator_id.type.length == 150
        assert IPRule.modifier_id.type.length == 150
        assert IPRule.description.type.length == 256

    def test_ip_address_has_index(self):
        """ip_address 字段应建立索引。"""
        assert IPRule.ip_address.index is True

    def test_to_domain(self):
        """to_domain 应返回 IPRuleEntity 实例。"""
        from src.domain.entities.ip_rule import IPRuleEntity

        rule = IPRule(id="rule-1", ip_address="192.168.1.1", rule_type="whitelist", reason="公司内网", is_active=1)
        entity = rule.to_domain()
        assert isinstance(entity, IPRuleEntity)
        assert entity.id == "rule-1"
        assert entity.ip_address == "192.168.1.1"
        assert entity.rule_type == "whitelist"
        assert entity.reason == "公司内网"
        assert entity.is_active == 1

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.ip_rule import IPRuleEntity

        entity = IPRuleEntity(id="rule-2", ip_address="10.0.0.1", rule_type="blacklist", reason="恶意IP", is_active=0)
        rule = IPRule.from_domain(entity)
        assert isinstance(rule, IPRule)
        assert rule.id == "rule-2"
        assert rule.ip_address == "10.0.0.1"
        assert rule.rule_type == "blacklist"
        assert rule.reason == "恶意IP"
        assert rule.is_active == 0

    def test_repr(self):
        """__repr__ 应包含 ip 和 type。"""
        rule = IPRule(ip_address="1.2.3.4", rule_type="whitelist")
        rule.id = "rule-123"
        r = repr(rule)
        assert "IPRule" in r
        assert "1.2.3.4" in r
        assert "whitelist" in r
