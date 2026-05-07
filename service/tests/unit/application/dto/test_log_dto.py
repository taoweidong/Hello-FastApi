"""日志 DTO 的单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.application.dto.log_dto import (
    BatchDeleteLogDTO,
    LoginLogListQueryDTO,
    LoginLogResponseDTO,
    OperationLogListQueryDTO,
    OperationLogResponseDTO,
    SystemLogListQueryDTO,
)


@pytest.mark.unit
class TestLoginLogListQueryDTO:
    """LoginLogListQueryDTO 验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        dto = LoginLogListQueryDTO()
        assert dto.pageNum == 1
        assert dto.pageSize == 10
        assert dto.status is None
        assert dto.loginType is None
        assert dto.createdTime is None

    def test_custom_values(self):
        """测试自定义值。"""
        dto = LoginLogListQueryDTO(pageNum=2, pageSize=20, status="1", loginType="password", createdTime="2024-01-01")
        assert dto.pageNum == 2
        assert dto.pageSize == 20
        assert dto.status == "1"
        assert dto.loginType == "password"
        assert dto.createdTime == "2024-01-01"

    def test_page_size_ge_limit(self):
        """测试 pageSize 最小值为 1。"""
        with pytest.raises(ValidationError):
            LoginLogListQueryDTO(pageSize=0)

    def test_page_size_le_limit(self):
        """测试 pageSize 最大值为 100。"""
        with pytest.raises(ValidationError):
            LoginLogListQueryDTO(pageSize=101)

    def test_page_num_ge_limit(self):
        """测试 pageNum 最小值为 1。"""
        with pytest.raises(ValidationError):
            LoginLogListQueryDTO(pageNum=0)

    def test_created_time_as_list(self):
        """测试 createdTime 为时间范围数组。"""
        dto = LoginLogListQueryDTO(createdTime=["2024-01-01", "2024-01-31"])
        assert dto.createdTime == ["2024-01-01", "2024-01-31"]


@pytest.mark.unit
class TestLoginLogResponseDTO:
    """LoginLogResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的登录日志响应数据。"""
        dto = LoginLogResponseDTO(id="1")
        assert dto.id == "1"
        assert dto.status == 1
        assert dto.ipaddress is None
        assert dto.loginType == 0

    def test_with_all_fields(self):
        """测试所有字段。"""
        now = datetime.now()
        dto = LoginLogResponseDTO(
            id="1",
            status=0,
            ipaddress="127.0.0.1",
            browser="Chrome",
            system="Windows",
            agent="Mozilla/5.0",
            loginType=1,
            creatorId="u1",
            createdTime=now,
            updatedTime=now,
        )
        assert dto.status == 0
        assert dto.ipaddress == "127.0.0.1"
        assert dto.loginType == 1

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            LoginLogResponseDTO()


@pytest.mark.unit
class TestOperationLogListQueryDTO:
    """OperationLogListQueryDTO 验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        dto = OperationLogListQueryDTO()
        assert dto.pageNum == 1
        assert dto.pageSize == 10
        assert dto.module is None
        assert dto.status is None
        assert dto.createdTime is None

    def test_custom_values(self):
        """测试自定义值。"""
        dto = OperationLogListQueryDTO(pageNum=2, pageSize=20, module="user", status="1", createdTime="2024-01-01")
        assert dto.module == "user"

    def test_created_time_as_list(self):
        """测试 createdTime 为时间范围数组。"""
        dto = OperationLogListQueryDTO(createdTime=["2024-01-01", "2024-01-31"])
        assert dto.createdTime == ["2024-01-01", "2024-01-31"]


@pytest.mark.unit
class TestOperationLogResponseDTO:
    """OperationLogResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的操作日志响应数据。"""
        dto = OperationLogResponseDTO(id="1")
        assert dto.id == "1"
        assert dto.module is None
        assert dto.path is None

    def test_with_all_fields(self):
        """测试所有字段。"""
        now = datetime.now()
        dto = OperationLogResponseDTO(
            id="1",
            module="user",
            path="/api/user",
            body='{"key": "val"}',
            method="POST",
            ipaddress="127.0.0.1",
            browser="Chrome",
            system="Windows",
            responseCode=200,
            responseResult="success",
            statusCode=0,
            creatorId="u1",
            createdTime=now,
            updatedTime=now,
        )
        assert dto.module == "user"
        assert dto.method == "POST"
        assert dto.responseCode == 200

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            OperationLogResponseDTO()


@pytest.mark.unit
class TestSystemLogListQueryDTO:
    """SystemLogListQueryDTO 验证测试。"""

    def test_default_values(self):
        """测试默认值。"""
        dto = SystemLogListQueryDTO()
        assert dto.pageNum == 1
        assert dto.pageSize == 10
        assert dto.module is None
        assert dto.status is None
        assert dto.createdTime is None

    def test_custom_values(self):
        """测试自定义值。"""
        dto = SystemLogListQueryDTO(pageNum=2, pageSize=20, module="system", status="1", createdTime="2024-01-01")
        assert dto.module == "system"


@pytest.mark.unit
class TestBatchDeleteLogDTO:
    """BatchDeleteLogDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的批量删除数据。"""
        dto = BatchDeleteLogDTO(ids=["1", "2", "3"])
        assert dto.ids == ["1", "2", "3"]

    def test_empty_ids(self):
        """测试空 ID 列表。"""
        dto = BatchDeleteLogDTO(ids=[])
        assert dto.ids == []

    def test_missing_ids(self):
        """测试缺少 ID 列表。"""
        with pytest.raises(ValidationError):
            BatchDeleteLogDTO()
