"""ErrorResponse 模型的单元测试。"""

import pytest
from src.api.common.error_response import ErrorResponse


@pytest.mark.unit
class TestErrorResponse:
    """ErrorResponse 模型测试。"""

    def test_create_with_detail(self):
        """测试创建包含 detail 的错误响应。"""
        resp = ErrorResponse(detail="Something went wrong")
        assert resp.detail == "Something went wrong"

    def test_create_with_empty_detail(self):
        """测试创建包含空 detail 的错误响应。"""
        resp = ErrorResponse(detail="")
        assert resp.detail == ""

    def test_model_dump_returns_dict(self):
        """测试 model_dump 返回正确的字典。"""
        resp = ErrorResponse(detail="Not found")
        data = resp.model_dump()
        assert data == {"detail": "Not found"}

    def test_model_dump_json_returns_string(self):
        """测试 model_dump_json 返回 JSON 字符串。"""
        resp = ErrorResponse(detail="Not found")
        json_str = resp.model_dump_json()
        assert '"detail":"Not found"' in json_str
