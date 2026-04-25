"""user_formatter 工具函数的单元测试。"""

import pytest
from src.api.common.user_formatter import format_user_list_row


@pytest.mark.unit
class TestFormatUserListRow:
    """format_user_list_row 函数测试。"""

    def test_basic_formatting(self):
        """测试基本格式化应添加 dept 和空字符串占位。"""
        user = {
            "id": 1,
            "username": "admin",
            "dept_id": 10,
        }
        result = format_user_list_row(user)
        assert result["id"] == 1
        assert result["username"] == "admin"
        assert result["dept"] == {"id": 10, "name": ""}
        assert "dept_id" not in result

    def test_missing_dept_id_defaults_to_empty(self):
        """测试缺少 dept_id 时 dept.id 应为空字符串。"""
        user = {"id": 1, "username": "test"}
        result = format_user_list_row(user)
        assert result["dept"] == {"id": "", "name": ""}

    def test_none_dept_id_defaults_to_empty(self):
        """测试 dept_id 为 None 时 dept.id 应为空字符串。"""
        user = {"id": 1, "dept_id": None}
        result = format_user_list_row(user)
        assert result["dept"] == {"id": "", "name": ""}

    def test_none_fields_become_empty_string(self):
        """测试 phone/email/nickname/avatar/description 为 None 时应变为空字符串。"""
        user = {"id": 1, "username": "admin"}
        result = format_user_list_row(user)
        assert result["phone"] == ""
        assert result["email"] == ""
        assert result["nickname"] == ""
        assert result["avatar"] == ""
        assert result["description"] == ""

    def test_none_fields_with_existing_value_kept(self):
        """测试 phone/email/nickname/avatar/description 有值时保持原值。"""
        user = {
            "id": 1,
            "username": "admin",
            "phone": "13800138000",
            "email": "admin@example.com",
            "nickname": "管理员",
            "avatar": "/avatar.png",
            "description": "超级管理员",
        }
        result = format_user_list_row(user)
        assert result["phone"] == "13800138000"
        assert result["email"] == "admin@example.com"
        assert result["nickname"] == "管理员"
        assert result["avatar"] == "/avatar.png"
        assert result["description"] == "超级管理员"

    def test_empty_string_fields_not_overwritten(self):
        """测试已有空字符串的字段不应被覆盖为 None。"""
        user = {"id": 1, "username": "a", "phone": "", "email": ""}
        result = format_user_list_row(user)
        assert result["phone"] == ""
        assert result["email"] == ""

    def test_dept_id_removed_from_output(self):
        """测试 dept_id 应从输出中移除。"""
        user = {"id": 1, "username": "admin", "dept_id": 5}
        result = format_user_list_row(user)
        assert "dept_id" not in result

    def test_original_dict_not_mutated(self):
        """测试原始字典不应被修改。"""
        user = {"id": 1, "username": "admin", "dept_id": 10}
        original = dict(user)
        format_user_list_row(user)
        assert user == original

    def test_empty_dict(self):
        """测试空字典应能正常处理。"""
        result = format_user_list_row({})
        assert result["dept"] == {"id": "", "name": ""}
        assert result["phone"] == ""
        assert result["email"] == ""

    def test_extra_fields_preserved(self):
        """测试未在格式化列表中的额外字段应保留。"""
        user = {"id": 1, "username": "admin", "custom_field": "custom_value"}
        result = format_user_list_row(user)
        assert result["custom_field"] == "custom_value"
