"""SystemConfig 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.system_config import SystemConfig


@pytest.mark.unit
class TestSystemConfigModel:
    """SystemConfig ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_systemconfig。"""
        assert SystemConfig.__tablename__ == "sys_systemconfig"

    def test_is_sqlmodel_table(self):
        """SystemConfig 应继承 SQLModel 并映射为表。"""
        assert issubclass(SystemConfig, SQLModel)
        assert hasattr(SystemConfig, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        config = SystemConfig(key="site_name", value='"MyApp"')
        assert config.id is not None
        assert len(config.id) == 32

    def test_field_defaults(self):
        """测试字段默认值。"""
        config = SystemConfig(key="site_name", value='"MyApp"')
        assert config.is_active == 1
        assert config.access == 0
        assert config.inherit == 0

    def test_optional_fields_default_none(self):
        """可选字段默认应为 None。"""
        config = SystemConfig(key="site_name", value='"MyApp"')
        assert config.creator_id is None
        assert config.modifier_id is None
        assert config.created_time is None
        assert config.updated_time is None
        assert config.description is None

    def test_field_max_length(self):
        """字段应有正确的 max_length 限制。"""
        assert SystemConfig.key.type.length == 255
        assert SystemConfig.creator_id.type.length == 150
        assert SystemConfig.modifier_id.type.length == 150
        assert SystemConfig.description.type.length == 256

    def test_key_is_unique(self):
        """key 字段应标记为 unique。"""
        assert SystemConfig.key.unique is True

    def test_value_uses_text_column(self):
        """value 字段应使用 Text 类型。"""

        config = SystemConfig(key="test", value="value")
        assert isinstance(config.value, str)

    def test_to_domain(self):
        """to_domain 应返回 SystemConfigEntity 实例。"""
        from src.domain.entities.system_config import SystemConfigEntity

        config = SystemConfig(id="cfg-1", key="site_name", value='"MyApp"', is_active=1, access=0, inherit=0)
        entity = config.to_domain()
        assert isinstance(entity, SystemConfigEntity)
        assert entity.id == "cfg-1"
        assert entity.key == "site_name"
        assert entity.value == '"MyApp"'
        assert entity.is_active == 1

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.system_config import SystemConfigEntity

        entity = SystemConfigEntity(id="cfg-2", key="site_logo", value='"/logo.png"', is_active=0, access=1, inherit=1)
        config = SystemConfig.from_domain(entity)
        assert isinstance(config, SystemConfig)
        assert config.id == "cfg-2"
        assert config.key == "site_logo"
        assert config.value == '"/logo.png"'
        assert config.is_active == 0
        assert config.access == 1
        assert config.inherit == 1

    def test_repr(self):
        """__repr__ 应包含 id 和 key。"""
        config = SystemConfig(key="test_key", value='"val"')
        config.id = "cfg-123"
        r = repr(config)
        assert "SystemConfig" in r
        assert "cfg-123" in r
        assert "test_key" in r
