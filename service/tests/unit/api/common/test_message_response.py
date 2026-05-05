"""MessageResponse 模型的单元测试。"""

import pytest

from src.api.common.message_response import MessageResponse


@pytest.mark.unit
class TestMessageResponse:
    """MessageResponse 模型测试。"""

    def test_create_with_message(self):
        """测试创建包含 message 的消息响应。"""
        resp = MessageResponse(message="操作成功")
        assert resp.message == "操作成功"

    def test_create_with_empty_message(self):
        """测试创建包含空 message 的消息响应。"""
        resp = MessageResponse(message="")
        assert resp.message == ""

    def test_model_dump_returns_dict(self):
        """测试 model_dump 返回正确的字典。"""
        resp = MessageResponse(message="已创建")
        data = resp.model_dump()
        assert data == {"message": "已创建"}

    def test_model_dump_json_returns_string(self):
        """测试 model_dump_json 返回 JSON 字符串。"""
        resp = MessageResponse(message="成功")
        json_str = resp.model_dump_json()
        assert '"message":"成功"' in json_str
