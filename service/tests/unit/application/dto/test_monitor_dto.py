"""MonitorDTO 单元测试。

重点回归：OnlineLogsQueryDTO 分页字段必须接受前端 camelCase（pageNum/pageSize）。
历史上误用 snake_case，pydantic 静默丢弃未知字段导致在线用户分页失效。
"""

import pytest
from pydantic import ValidationError

from src.application.dto.monitor_dto import OnlineLogsQueryDTO


@pytest.mark.unit
class TestOnlineLogsQueryDTO:
    """在线用户查询 DTO 测试。"""

    def test_accepts_camel_case_pagination(self):
        """前端传参 camelCase（pageNum/pageSize）必须被解析，而非静默丢弃。"""
        dto = OnlineLogsQueryDTO.model_validate({"pageNum": 3, "pageSize": 20})
        assert dto.pageNum == 3
        assert dto.pageSize == 20

    def test_accepts_username_filter(self):
        dto = OnlineLogsQueryDTO.model_validate({"username": "admin", "pageNum": 2, "pageSize": 5})
        assert dto.username == "admin"
        assert dto.pageNum == 2

    def test_empty_username_becomes_none(self):
        """空字符串过滤条件应转为 None（不过滤）。"""
        dto = OnlineLogsQueryDTO.model_validate({"username": ""})
        assert dto.username is None

    def test_defaults(self):
        dto = OnlineLogsQueryDTO()
        assert dto.pageNum == 1
        assert dto.pageSize == 10
        assert dto.username is None

    def test_rejects_non_positive_page_num(self):
        with pytest.raises(ValidationError):
            OnlineLogsQueryDTO.model_validate({"pageNum": 0})

    def test_rejects_page_size_over_100(self):
        with pytest.raises(ValidationError):
            OnlineLogsQueryDTO.model_validate({"pageSize": 101})
