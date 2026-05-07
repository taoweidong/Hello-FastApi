"""部门 DTO 的单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.application.dto.department_dto import (
    DepartmentCreateDTO,
    DepartmentListQueryDTO,
    DepartmentResponseDTO,
    DepartmentUpdateDTO,
)


@pytest.mark.unit
class TestDepartmentCreateDTO:
    """DepartmentCreateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的部门创建数据。"""
        dto = DepartmentCreateDTO(name="技术部")
        assert dto.name == "技术部"
        assert dto.parentId is None
        assert dto.modeType == 0
        assert dto.code == ""
        assert dto.rank == 0
        assert dto.autoBind == 0
        assert dto.isActive == 1
        assert dto.description is None

    def test_valid_input_all_fields(self):
        """测试所有字段。"""
        dto = DepartmentCreateDTO(
            name="技术部",
            parentId="123",
            modeType=1,
            code="dept-001",
            rank=1,
            autoBind=1,
            isActive=0,
            description="技术部门",
        )
        assert dto.parentId == "123"
        assert dto.modeType == 1
        assert dto.code == "dept-001"
        assert dto.isActive == 0

    def test_empty_parent_id_converts_to_none(self):
        """测试空字符串 parentId 转换为 None。"""
        dto = DepartmentCreateDTO(name="技术部", parentId="")
        assert dto.parentId is None

    def test_zero_parent_id_converts_to_none(self):
        """测试 0 的 parentId 转换为 None。"""
        dto = DepartmentCreateDTO(name="技术部", parentId="0")
        assert dto.parentId is None

    def test_empty_description_converts_to_none(self):
        """测试空字符串描述转换为 None。"""
        dto = DepartmentCreateDTO(name="技术部", description="")
        assert dto.description is None

    def test_empty_mode_type_converts_to_zero(self):
        """测试空字符串 modeType 转换为 0。"""
        dto = DepartmentCreateDTO(name="技术部", modeType="")
        assert dto.modeType == 0

    def test_none_mode_type_converts_to_zero(self):
        """测试 None 的 modeType 转换为 0。"""
        dto = DepartmentCreateDTO(name="技术部", modeType=None)
        assert dto.modeType == 0

    def test_name_too_long(self):
        """测试部门名称超长。"""
        with pytest.raises(ValidationError):
            DepartmentCreateDTO(name="a" * 65)


@pytest.mark.unit
class TestDepartmentUpdateDTO:
    """DepartmentUpdateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的部门更新数据。"""
        dto = DepartmentUpdateDTO(name="新部门")
        assert dto.name == "新部门"

    def test_empty_input(self):
        """测试空更新。"""
        dto = DepartmentUpdateDTO()
        assert dto.name is None
        assert dto.parentId is None
        assert dto.isActive is None

    def test_empty_name_converts_to_none(self):
        """测试空字符串 name 转换为 None。"""
        dto = DepartmentUpdateDTO(name="")
        assert dto.name is None

    def test_empty_parent_id_converts_to_none(self):
        """测试空字符串 parentId 转换为 None。"""
        dto = DepartmentUpdateDTO(parentId="")
        assert dto.parentId is None

    def test_zero_parent_id_converts_to_none(self):
        """测试 0 的 parentId 转换为 None。"""
        dto = DepartmentUpdateDTO(parentId="0")
        assert dto.parentId is None

    def test_empty_description_converts_to_none(self):
        """测试空字符串描述转换为 None。"""
        dto = DepartmentUpdateDTO(description="")
        assert dto.description is None

    def test_empty_mode_type_converts_to_none(self):
        """测试空字符串 modeType 转换为 None。"""
        dto = DepartmentUpdateDTO(modeType="")
        assert dto.modeType is None

    def test_zero_mode_type_converts_to_none(self):
        """测试 0 的 modeType 转换为 None。"""
        dto = DepartmentUpdateDTO(modeType=0)
        assert dto.modeType is None

    def test_is_active_zero_preserved(self):
        """测试 isActive 为 0 时保留。"""
        dto = DepartmentUpdateDTO(isActive=0)
        assert dto.isActive == 0

    def test_is_active_empty_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = DepartmentUpdateDTO(isActive="")
        assert dto.isActive is None

    def test_name_too_long(self):
        """测试部门名称超长。"""
        with pytest.raises(ValidationError):
            DepartmentUpdateDTO(name="a" * 65)


@pytest.mark.unit
class TestDepartmentResponseDTO:
    """DepartmentResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的部门响应数据。"""
        dto = DepartmentResponseDTO(id="1", parentId=None, name="技术部")
        assert dto.id == "1"
        assert dto.name == "技术部"
        assert dto.modeType == 0
        assert dto.isActive == 1

    def test_with_all_fields(self):
        """测试所有字段。"""
        now = datetime.now()
        dto = DepartmentResponseDTO(
            id="1",
            parentId="0",
            name="技术部",
            modeType=1,
            code="dept-001",
            rank=1,
            autoBind=1,
            isActive=1,
            creatorId="u1",
            modifierId="u2",
            createdTime=now,
            updatedTime=now,
            description="描述",
        )
        assert dto.code == "dept-001"
        assert dto.createdTime == now
        assert dto.creatorId == "u1"

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            DepartmentResponseDTO(name="技术部")


@pytest.mark.unit
class TestDepartmentListQueryDTO:
    """DepartmentListQueryDTO 验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        dto = DepartmentListQueryDTO()
        assert dto.name is None
        assert dto.isActive is None

    def test_custom_values(self):
        """测试自定义值。"""
        dto = DepartmentListQueryDTO(name="技术", isActive=1)
        assert dto.name == "技术"
        assert dto.isActive == 1

    def test_empty_is_active_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = DepartmentListQueryDTO(isActive="")
        assert dto.isActive is None
