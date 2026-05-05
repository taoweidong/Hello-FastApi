"""UnifiedResponse 模型的单元测试。"""

import pytest

from src.api.common.unified_response import UnifiedResponse


@pytest.mark.unit
class TestUnifiedResponse:
    """UnifiedResponse 模型测试。"""

    def test_create_with_defaults(self):
        """测试使用默认值创建应返回标准响应。"""
        resp = UnifiedResponse[int]()
        assert resp.code == 0
        assert resp.message == "操作成功"
        assert resp.data is None

    def test_create_with_data(self):
        """测试包含 data 时应返回正确数据。"""
        resp = UnifiedResponse[int](data=42)
        assert resp.data == 42

    def test_create_with_custom_message(self):
        """测试自定义 message 应生效。"""
        resp = UnifiedResponse[str](message="查询成功")
        assert resp.message == "查询成功"

    def test_create_with_custom_code(self):
        """测试自定义 code 应生效。"""
        resp = UnifiedResponse[dict](code=200)
        assert resp.code == 200

    def test_create_with_all_fields(self):
        """测试所有字段同时自定义时应生效。"""
        resp = UnifiedResponse[list](code=200, message="OK", data=[1, 2])
        assert resp.code == 200
        assert resp.message == "OK"
        assert resp.data == [1, 2]

    def test_data_none_by_default(self):
        """测试未传入 data 时 data 应为 None。"""
        resp = UnifiedResponse[str]()
        assert resp.data is None

    def test_model_dump_returns_dict(self):
        """测试 model_dump 返回正确的字典。"""
        resp = UnifiedResponse[int](code=0, message="成功", data=100)
        data = resp.model_dump()
        assert data == {"code": 0, "message": "成功", "data": 100}

    def test_model_dump_json_returns_string(self):
        """测试 model_dump_json 返回 JSON 字符串。"""
        resp = UnifiedResponse[str](code=0, message="ok", data="test")
        json_str = resp.model_dump_json()
        assert '"code":0' in json_str
        assert '"message":"ok"' in json_str
        assert '"data":"test"' in json_str

    def test_generic_with_dict_type(self):
        """测试泛型参数为 dict 时能正常工作。"""
        resp = UnifiedResponse[dict](data={"key": "value"})
        assert resp.data == {"key": "value"}

    def test_generic_with_list_type(self):
        """测试泛型参数为 list 时能正常工作。"""
        resp = UnifiedResponse[list](data=[1, 2, 3])
        assert resp.data == [1, 2, 3]

    def test_code_zero_means_success(self):
        """测试 code=0 表示成功（Pure Admin 前端标准）。"""
        resp = UnifiedResponse[None](code=0)
        assert resp.code == 0
        assert resp.data is None
