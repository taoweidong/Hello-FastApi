"""字典 DTO 的单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.application.dto.dictionary_dto import (
    DictionaryCreateDTO,
    DictionaryListQueryDTO,
    DictionaryResponseDTO,
    DictionaryUpdateDTO,
)


@pytest.mark.unit
class TestDictionaryCreateDTO:
    """DictionaryCreateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的字典创建数据。"""
        dto = DictionaryCreateDTO(name="gender")
        assert dto.name == "gender"
        assert dto.label == ""
        assert dto.value == ""
        assert dto.parentId is None
        assert dto.sort is None
        assert dto.isActive == 1
        assert dto.description is None

    def test_valid_input_all_fields(self):
        """测试所有字段。"""
        dto = DictionaryCreateDTO(name="gender", label="性别", value="1", parentId="123", sort=1, isActive=0, description="性别字典")
        assert dto.label == "性别"
        assert dto.value == "1"
        assert dto.sort == 1
        assert dto.isActive == 0

    def test_empty_parent_id_converts_to_none(self):
        """测试空字符串 parentId 转换为 None。"""
        dto = DictionaryCreateDTO(name="gender", parentId="")
        assert dto.parentId is None

    def test_zero_parent_id_converts_to_none(self):
        """测试 0 的 parentId 转换为 None。"""
        dto = DictionaryCreateDTO(name="gender", parentId="0")
        assert dto.parentId is None

    def test_empty_description_converts_to_none(self):
        """测试空字符串描述转换为 None。"""
        dto = DictionaryCreateDTO(name="gender", description="")
        assert dto.description is None

    def test_empty_sort_converts_to_none(self):
        """测试空字符串 sort 转换为 None。"""
        dto = DictionaryCreateDTO(name="gender", sort="")
        assert dto.sort is None

    def test_zero_sort_converts_to_none(self):
        """测试 0 的 sort 转换为 None。"""
        dto = DictionaryCreateDTO(name="gender", sort=0)
        assert dto.sort is None

    def test_empty_is_active_converts_to_one(self):
        """测试空字符串 isActive 转换为 1。"""
        dto = DictionaryCreateDTO(name="gender", isActive="")
        assert dto.isActive == 1

    def test_none_is_active_converts_to_one(self):
        """测试 None 的 isActive 转换为 1。"""
        dto = DictionaryCreateDTO(name="gender", isActive=None)
        assert dto.isActive == 1

    def test_name_too_long(self):
        """测试字典名称超长。"""
        with pytest.raises(ValidationError):
            DictionaryCreateDTO(name="a" * 65)


@pytest.mark.unit
class TestDictionaryUpdateDTO:
    """DictionaryUpdateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的字典更新数据。"""
        dto = DictionaryUpdateDTO(name="新字典")
        assert dto.name == "新字典"

    def test_empty_input(self):
        """测试空更新。"""
        dto = DictionaryUpdateDTO()
        assert dto.name is None
        assert dto.label is None
        assert dto.value is None

    def test_empty_name_converts_to_none(self):
        """测试空字符串 name 转换为 None。"""
        dto = DictionaryUpdateDTO(name="")
        assert dto.name is None

    def test_empty_label_converts_to_none(self):
        """测试空字符串 label 转换为 None。"""
        dto = DictionaryUpdateDTO(label="")
        assert dto.label is None

    def test_empty_value_converts_to_none(self):
        """测试空字符串 value 转换为 None。"""
        dto = DictionaryUpdateDTO(value="")
        assert dto.value is None

    def test_empty_parent_id_converts_to_none(self):
        """测试空字符串 parentId 转换为 None。"""
        dto = DictionaryUpdateDTO(parentId="")
        assert dto.parentId is None

    def test_zero_parent_id_converts_to_none(self):
        """测试 0 的 parentId 转换为 None。"""
        dto = DictionaryUpdateDTO(parentId="0")
        assert dto.parentId is None

    def test_empty_sort_converts_to_none(self):
        """测试空字符串 sort 转换为 None。"""
        dto = DictionaryUpdateDTO(sort="")
        assert dto.sort is None

    def test_zero_sort_converts_to_none(self):
        """测试 0 的 sort 转换为 None。"""
        dto = DictionaryUpdateDTO(sort=0)
        assert dto.sort is None

    def test_empty_is_active_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = DictionaryUpdateDTO(isActive="")
        assert dto.isActive is None

    def test_is_active_zero_preserved(self):
        """测试 isActive 为 0 时保留。"""
        dto = DictionaryUpdateDTO(isActive=0)
        assert dto.isActive == 0

    def test_invalid_sort_string(self):
        """测试无效的 sort 字符串。"""
        dto = DictionaryUpdateDTO(sort="abc")
        assert dto.sort is None


@pytest.mark.unit
class TestDictionaryResponseDTO:
    """DictionaryResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的字典响应数据。"""
        dto = DictionaryResponseDTO(id="1", parentId=None, name="gender")
        assert dto.id == "1"
        assert dto.name == "gender"
        assert dto.label == ""
        assert dto.isActive == 1

    def test_with_all_fields(self):
        """测试所有字段。"""
        now = datetime.now()
        dto = DictionaryResponseDTO(id="1", parentId="0", name="gender", label="性别", value="1", sort=1, isActive=1, createdTime=now, updatedTime=now, description="描述")
        assert dto.value == "1"
        assert dto.sort == 1
        assert dto.createdTime == now

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            DictionaryResponseDTO(name="gender")


@pytest.mark.unit
class TestDictionaryListQueryDTO:
    """DictionaryListQueryDTO 验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        dto = DictionaryListQueryDTO()
        assert dto.name is None
        assert dto.isActive is None

    def test_custom_values(self):
        """测试自定义值。"""
        dto = DictionaryListQueryDTO(name="gender", isActive=1)
        assert dto.name == "gender"
        assert dto.isActive == 1

    def test_empty_is_active_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = DictionaryListQueryDTO(isActive="")
        assert dto.isActive is None
