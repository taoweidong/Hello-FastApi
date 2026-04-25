"""系统配置领域实体的单元测试。

测试 SystemConfigEntity 的状态变更方法和工厂方法。
"""

import pytest

from src.domain.entities.system_config import SystemConfigEntity


@pytest.mark.unit
class TestSystemConfigEntity:
    """SystemConfigEntity 测试类。"""

    # ---- 状态变更方法测试 ----

    def test_update_info_with_all_fields(self):
        """测试 update_info 方法（更新所有字段）。"""
        config = SystemConfigEntity(id="config-1", key="site_title", value="标题")
        config.update_info(
            value="新标题",
            is_active=1,
            access=1,
            key="new_key",
            inherit=1,
            description="描述",
        )
        assert config.value == "新标题"
        assert config.is_active == 1
        assert config.access == 1
        assert config.key == "new_key"
        assert config.inherit == 1
        assert config.description == "描述"

    def test_update_info_with_partial_fields(self):
        """测试 update_info 方法（部分字段）。"""
        config = SystemConfigEntity(id="config-1", key="site_title", value="标题")
        config.update_info(value="新标题", is_active=0)
        assert config.value == "新标题"
        assert config.is_active == 0
        assert config.key == "site_title"

    def test_update_info_ignore_none_fields(self):
        """测试 update_info 方法（忽略 None 字段）。"""
        config = SystemConfigEntity(id="config-1", key="site_title", value="标题")
        config.update_info(value=None, description=None)
        assert config.value == "标题"
        assert config.description is None

    # ---- 工厂方法测试 ----

    def test_create_new(self):
        """测试 create_new 工厂方法。"""
        config = SystemConfigEntity.create_new(
            key="site_title",
            value="我的网站",
            description="网站标题",
        )
        assert config.id is not None
        assert len(config.id) == 32
        assert config.key == "site_title"
        assert config.value == "我的网站"
        assert config.description == "网站标题"
        assert config.is_active == 1
        assert config.access == 0
        assert config.inherit == 0

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        config = SystemConfigEntity.create_new(key="debug_mode")
        assert config.key == "debug_mode"
        assert config.value == ""
        assert config.is_active == 1
        assert config.description is None
