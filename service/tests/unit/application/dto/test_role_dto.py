"""角色 DTO 的单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.application.dto.role_dto import (
    AssignMenusDTO,
    AssignRoleDTO,
    RoleCreateDTO,
    RoleListQueryDTO,
    RoleResponseDTO,
    RoleUpdateDTO,
)


@pytest.mark.unit
class TestRoleCreateDTO:
    """RoleCreateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的角色创建数据。"""
        dto = RoleCreateDTO(name="管理员", code="admin")
        assert dto.name == "管理员"
        assert dto.code == "admin"
        assert dto.isActive == 1
        assert dto.description is None
        assert dto.menuIds == []

    def test_valid_input_all_fields(self):
        """测试所有字段。"""
        dto = RoleCreateDTO(name="管理员", code="admin", isActive=0, description="管理员角色", menuIds=["1", "2"])
        assert dto.isActive == 0
        assert dto.description == "管理员角色"
        assert dto.menuIds == ["1", "2"]

    def test_empty_description_converts_to_none(self):
        """测试空字符串描述转换为 None。"""
        dto = RoleCreateDTO(name="管理员", code="admin", description="")
        assert dto.description is None

    def test_name_too_short(self):
        """测试角色名称过短。"""
        with pytest.raises(ValidationError):
            RoleCreateDTO(name="a", code="admin")

    def test_name_too_long(self):
        """测试角色名称超长。"""
        with pytest.raises(ValidationError):
            RoleCreateDTO(name="a" * 65, code="admin")

    def test_code_too_short(self):
        """测试角色编码过短。"""
        with pytest.raises(ValidationError):
            RoleCreateDTO(name="管理员", code="a")

    def test_missing_name(self):
        """测试缺少角色名称。"""
        with pytest.raises(ValidationError):
            RoleCreateDTO(code="admin")


@pytest.mark.unit
class TestRoleUpdateDTO:
    """RoleUpdateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的角色更新数据。"""
        dto = RoleUpdateDTO(name="新角色", code="new_role")
        assert dto.name == "新角色"
        assert dto.code == "new_role"

    def test_empty_input(self):
        """测试空更新。"""
        dto = RoleUpdateDTO()
        assert dto.name is None
        assert dto.code is None
        assert dto.isActive is None
        assert dto.menuIds is None

    def test_empty_name_converts_to_none(self):
        """测试空字符串 name 转换为 None。"""
        dto = RoleUpdateDTO(name="")
        assert dto.name is None

    def test_empty_code_converts_to_none(self):
        """测试空字符串 code 转换为 None。"""
        dto = RoleUpdateDTO(code="")
        assert dto.code is None

    def test_empty_description_converts_to_none(self):
        """测试空字符串描述转换为 None。"""
        dto = RoleUpdateDTO(description="")
        assert dto.description is None

    def test_is_active_zero_preserved(self):
        """测试 isActive 为 0 时保留。"""
        dto = RoleUpdateDTO(isActive=0)
        assert dto.isActive == 0

    def test_is_active_empty_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = RoleUpdateDTO(isActive="")
        assert dto.isActive is None

    def test_invalid_is_active_string(self):
        """测试无效的 isActive 字符串。"""
        dto = RoleUpdateDTO(isActive="abc")
        assert dto.isActive is None

    def test_menu_ids_empty_list(self):
        """测试清空菜单 ID。"""
        dto = RoleUpdateDTO(menuIds=[])
        assert dto.menuIds == []


@pytest.mark.unit
class TestRoleResponseDTO:
    """RoleResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的角色响应数据。"""
        dto = RoleResponseDTO(id="1", name="管理员", code="admin")
        assert dto.id == "1"
        assert dto.name == "管理员"
        assert dto.code == "admin"
        assert dto.isActive == 1
        assert dto.menus == []
        assert dto.description is None

    def test_with_all_fields(self):
        """测试所有字段。"""
        now = datetime.now()
        dto = RoleResponseDTO(
            id="1",
            name="管理员",
            code="admin",
            isActive=0,
            menus=[{"id": "m1", "name": "用户管理"}],
            creatorId="u1",
            modifierId="u2",
            createdTime=now,
            updatedTime=now,
            description="描述",
        )
        assert dto.isActive == 0
        assert len(dto.menus) == 1
        assert dto.createdTime == now

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            RoleResponseDTO(name="管理员", code="admin")


@pytest.mark.unit
class TestRoleListQueryDTO:
    """RoleListQueryDTO 验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        dto = RoleListQueryDTO()
        assert dto.pageNum == 1
        assert dto.pageSize == 10
        assert dto.name is None
        assert dto.code is None
        assert dto.isActive is None

    def test_custom_values(self):
        """测试自定义值。"""
        dto = RoleListQueryDTO(pageNum=2, pageSize=20, name="管理员", code="admin", isActive=1)
        assert dto.pageNum == 2
        assert dto.name == "管理员"
        assert dto.isActive == 1

    def test_page_size_out_of_range(self):
        """测试 pageSize 超出范围。"""
        with pytest.raises(ValidationError):
            RoleListQueryDTO(pageSize=101)

    def test_empty_is_active_converts_to_none(self):
        """测试空字符串 isActive 转换为 None。"""
        dto = RoleListQueryDTO(isActive="")
        assert dto.isActive is None


@pytest.mark.unit
class TestAssignMenusDTO:
    """AssignMenusDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的分配菜单数据。"""
        dto = AssignMenusDTO(menuIds=["1", "2", "3"])
        assert dto.menuIds == ["1", "2", "3"]

    def test_empty_menu_ids(self):
        """测试空菜单 ID 列表。"""
        dto = AssignMenusDTO(menuIds=[])
        assert dto.menuIds == []

    def test_missing_menu_ids(self):
        """测试缺少菜单 ID。"""
        with pytest.raises(ValidationError):
            AssignMenusDTO()


@pytest.mark.unit
class TestAssignRoleDTO:
    """AssignRoleDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的分配角色数据。"""
        dto = AssignRoleDTO(userId="u1", roleId="r1")
        assert dto.userId == "u1"
        assert dto.roleId == "r1"

    def test_valid_input_by_alias(self):
        """测试通过别名 userId/roleId 访问。"""
        dto = AssignRoleDTO(**{"userId": "u1", "roleId": "r1"})
        assert dto.userId == "u1"
        assert dto.roleId == "r1"

    def test_missing_user_id(self):
        """测试缺少用户 ID。"""
        with pytest.raises(ValidationError):
            AssignRoleDTO(roleId="r1")
