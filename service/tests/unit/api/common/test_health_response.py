"""HealthResponse 模型的单元测试。"""

import pytest
from src.api.common.health_response import HealthResponse


@pytest.mark.unit
class TestHealthResponse:
    """HealthResponse 模型测试。"""

    def test_create_with_status_and_version(self):
        """测试创建包含 status 和 version 的健康检查响应。"""
        resp = HealthResponse(status="ok", version="1.0.0")
        assert resp.status == "ok"
        assert resp.version == "1.0.0"

    def test_create_with_empty_strings(self):
        """测试创建包含空字符串的健康检查响应。"""
        resp = HealthResponse(status="", version="")
        assert resp.status == ""
        assert resp.version == ""

    def test_model_dump_returns_dict(self):
        """测试 model_dump 返回正确的字典。"""
        resp = HealthResponse(status="healthy", version="2.0.0")
        data = resp.model_dump()
        assert data == {"status": "healthy", "version": "2.0.0"}

    def test_model_dump_json_returns_string(self):
        """测试 model_dump_json 返回 JSON 字符串。"""
        resp = HealthResponse(status="ok", version="1.0")
        json_str = resp.model_dump_json()
        assert '"status":"ok"' in json_str
        assert '"version":"1.0"' in json_str
