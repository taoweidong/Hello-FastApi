"""系统配置 DTO 的单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.application.dto.system_config_dto import (
    SystemConfigCreateDTO,
    SystemConfigListQueryDTO,
    SystemConfigResponseDTO,
    SystemConfigUpdateDTO,
)


@pytest.mark.unit
class TestSystemConfigCreateDTO:
    """SystemConfigCreateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的系统配置创建数据。"""
        dto = SystemConfigCreateDTO(key="site_name", value='"Hello-FastApi"')
        assert dto.key == "site_name"
        assert dto.value == '"Hello-FastApi"'
        assert dto.isActive == 1
        assert dto.access == 0
        assert dto.inherit == 0
        assert dto.description is None

    def test_valid_input_all_fields(self):
        """测试所有字段。"""
        dto = SystemConfigCreateDTO(key="site_name", value='"Hello-FastApi"', isActive=0, access=1, inherit=1, description="网站名称")
        assert dto.isActive == 0
        assert dto.access == 1
        assert dto.inherit == 1

    def test_empty_description_converts_to_none(self):
        """测试空字符串描述转换为 None。"""
        dto = SystemConfigCreateDTO(key="site_name", value='"val"', description="")
        assert dto.description is None

    def test_key_too_short(self):
        """测试配置键过短。"""
        with pytest.raises(ValidationError):
            SystemConfigCreateDTO(key="", value='"val"')

    def test_key_too_long(self):
        """测试配置键超长。"""
        with pytest.raises(ValidationError):
            SystemConfigCreateDTO(key="a" * 256, value='"val"')

    def test_missing_key(self):
        """测试缺少配置键。"""
        with pytest.raises(ValidationError):
            SystemConfigCreateDTO(value='"val"')

    def test_missing_value(self):
        """测试缺少配置值。"""
        with pytest.raises(ValidationError):
            SystemConfigCreateDTO(key="site_name")


@pytest.mark.unit
class TestSystemConfigUpdateDTO:
    """SystemConfigUpdateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的系统配置更新数据。"""
        dto = SystemConfigUpdateDTO(key="site_name", value='"new-val"')
        assert dto.key == "site_name"
        assert dto.value == '"new-val"'

    def test_empty_input(self):
        """测试空更新。"""
        dto = SystemConfigUpdateDTO()
        assert dto.key is None
        assert dto.value is None
        assert dto.isActive is None
        assert dto.access is None
        assert dto.inherit is None

    def test_empty_description_converts_to_none(self):
        """测试空字符串描述转换为 None。"""
        dto = SystemConfigUpdateDTO(description="")
        assert dto.description is None

    def test_empty_is_active_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = SystemConfigUpdateDTO(isActive="")
        assert dto.isActive is None

    def test_zero_is_active_converts_to_none(self):
        """测试 0 的 isActive 转换为 None。"""
        dto = SystemConfigUpdateDTO(isActive=0)
        assert dto.isActive is None

    def test_zero_access_converts_to_none(self):
        """测试 0 的 access 转换为 None。"""
        dto = SystemConfigUpdateDTO(access=0)
        assert dto.access is None

    def test_zero_inherit_converts_to_none(self):
        """测试 0 的 inherit 转换为 None。"""
        dto = SystemConfigUpdateDTO(inherit=0)
        assert dto.inherit is None

    def test_is_active_one_preserved(self):
        """测试 isActive 为 1 时保留。"""
        dto = SystemConfigUpdateDTO(isActive=1)
        assert dto.isActive == 1


@pytest.mark.unit
class TestSystemConfigResponseDTO:
    """SystemConfigResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的系统配置响应数据。"""
        dto = SystemConfigResponseDTO(id="1", key="site_name", value='"val"')
        assert dto.id == "1"
        assert dto.key == "site_name"
        assert dto.value == '"val"'
        assert dto.isActive == 1
        assert dto.access == 0
        assert dto.inherit == 0

    def test_with_all_fields(self):
        """测试所有字段。"""
        now = datetime.now()
        dto = SystemConfigResponseDTO(id="1", key="site_name", value='"val"', isActive=0, access=1, inherit=1, creatorId="u1", modifierId="u2", createdTime=now, updatedTime=now, description="描述")
        assert dto.isActive == 0
        assert dto.access == 1
        assert dto.createdTime == now

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            SystemConfigResponseDTO(key="site_name", value='"val"')


@pytest.mark.unit
class TestSystemConfigListQueryDTO:
    """SystemConfigListQueryDTO 验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        dto = SystemConfigListQueryDTO()
        assert dto.pageNum == 1
        assert dto.pageSize == 10
        assert dto.key is None
        assert dto.isActive is None

    def test_custom_values(self):
        """测试自定义值。"""
        dto = SystemConfigListQueryDTO(pageNum=2, pageSize=20, key="site_name", isActive=1)
        assert dto.pageNum == 2
        assert dto.key == "site_name"
        assert dto.isActive == 1

    def test_empty_is_active_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = SystemConfigListQueryDTO(isActive="")
        assert dto.isActive is None
