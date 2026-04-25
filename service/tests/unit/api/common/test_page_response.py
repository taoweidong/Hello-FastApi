"""PageResponse 模型的单元测试。"""

import pytest
from src.api.common.page_response import PageResponse


@pytest.mark.unit
class TestPageResponse:
    """PageResponse 模型测试。"""

    def test_create_with_all_fields(self):
        """测试创建包含所有字段的分页响应。"""
        resp = PageResponse[int](
            total=100, pageNum=1, pageSize=10, totalPage=10, rows=[1, 2, 3]
        )
        assert resp.total == 100
        assert resp.pageNum == 1
        assert resp.pageSize == 10
        assert resp.totalPage == 10
        assert resp.rows == [1, 2, 3]

    def test_create_with_empty_rows(self):
        """测试创建包含空 rows 的分页响应。"""
        resp = PageResponse[str](
            total=0, pageNum=1, pageSize=10, totalPage=0, rows=[]
        )
        assert resp.total == 0
        assert resp.rows == []

    def test_create_with_zero_values(self):
        """测试创建包含零值的分页响应。"""
        resp = PageResponse[int](
            total=0, pageNum=0, pageSize=0, totalPage=0, rows=[]
        )
        assert resp.total == 0
        assert resp.pageNum == 0
        assert resp.pageSize == 0
        assert resp.totalPage == 0

    def test_model_dump_returns_dict(self):
        """测试 model_dump 返回正确的字典。"""
        resp = PageResponse[int](
            total=50, pageNum=2, pageSize=10, totalPage=5, rows=[10, 20]
        )
        data = resp.model_dump()
        assert data["total"] == 50
        assert data["pageNum"] == 2
        assert data["pageSize"] == 10
        assert data["totalPage"] == 5
        assert data["rows"] == [10, 20]

    def test_model_dump_json_returns_string(self):
        """测试 model_dump_json 返回 JSON 字符串。"""
        resp = PageResponse[str](
            total=10, pageNum=1, pageSize=5, totalPage=2, rows=["a", "b"]
        )
        json_str = resp.model_dump_json()
        assert '"total":10' in json_str
        assert '"pageNum":1' in json_str
        assert '"rows":["a","b"]' in json_str

    def test_rows_with_dict_items(self):
        """测试 rows 包含字典类型元素。"""
        resp = PageResponse[dict](
            total=1, pageNum=1, pageSize=10, totalPage=1, rows=[{"id": 1}]
        )
        assert resp.rows == [{"id": 1}]
