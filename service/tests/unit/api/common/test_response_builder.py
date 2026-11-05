"""response_builder 工具函数的单元测试。"""

import pytest

from src.api.common.response_builder import list_response, success_response


@pytest.mark.unit
class TestSuccessResponse:
    """success_response 函数测试。"""

    def test_default_params(self):
        """测试使用默认参数应返回标准成功响应。"""
        result = success_response()
        assert result == {"code": 0, "message": "操作成功", "data": None}

    def test_with_data(self):
        """测试包含 data 时应返回正确数据。"""
        result = success_response(data={"id": 1, "name": "test"})
        assert result["code"] == 0
        assert result["message"] == "操作成功"
        assert result["data"] == {"id": 1, "name": "test"}

    def test_with_none_data(self):
        """测试 data=None 时应返回 data 为 None。"""
        result = success_response(data=None)
        assert result["data"] is None

    def test_custom_message(self):
        """测试自定义 message 应生效。"""
        result = success_response(message="创建成功")
        assert result["message"] == "创建成功"

    def test_custom_code(self):
        """测试自定义 code 应生效。"""
        result = success_response(code=200)
        assert result["code"] == 200

    def test_custom_all_params(self):
        """测试所有自定义参数应同时生效。"""
        result = success_response(data="hello", message="OK", code=200)
        assert result == {"code": 200, "message": "OK", "data": "hello"}

    def test_data_is_list(self):
        """测试 data 为列表时应正常返回。"""
        result = success_response(data=[1, 2, 3])
        assert result["data"] == [1, 2, 3]


@pytest.mark.unit
class TestListResponse:
    """list_response 函数测试。"""

    def test_empty_list(self):
        """测试空列表应返回正确的分页响应。"""
        result = list_response(list_data=[], total=0)
        assert result["code"] == 0
        assert result["message"] == "操作成功"
        assert result["data"]["list"] == []
        assert result["data"]["total"] == 0
        assert result["data"]["pageSize"] == 10
        assert result["data"]["currentPage"] == 1

    def test_with_data_and_total(self):
        """测试包含数据和总数的列表响应。"""
        result = list_response(list_data=[{"id": 1}, {"id": 2}], total=100)
        assert result["data"]["list"] == [{"id": 1}, {"id": 2}]
        assert result["data"]["total"] == 100

    def test_custom_page_params(self):
        """测试自定义分页参数应生效。"""
        result = list_response(list_data=["a", "b", "c"], total=30, page_size=5, current_page=3)
        assert result["data"]["list"] == ["a", "b", "c"]
        assert result["data"]["total"] == 30
        assert result["data"]["pageSize"] == 5
        assert result["data"]["currentPage"] == 3

    def test_zero_page_size(self):
        """测试 page_size=0 时应正常返回。"""
        result = list_response(list_data=[], total=0, page_size=0)
        assert result["data"]["pageSize"] == 0

    def test_current_page_is_integer(self):
        """测试 currentPage 应为整数类型。"""
        result = list_response(list_data=[1], total=1)
        assert isinstance(result["data"]["currentPage"], int)
