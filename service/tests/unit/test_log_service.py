"""日志服务的单元测试。"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.application.services.log_service import LogService, _parse_log_time_bound
from src.domain.entities.log import LoginLogEntity, OperationLogEntity


@pytest.mark.unit
class TestParseLogTimeBound:
    """_parse_log_time_bound 辅助函数测试。"""

    def test_none(self):
        assert _parse_log_time_bound(None) is None

    def test_datetime_value(self):
        now = datetime.now()
        assert _parse_log_time_bound(now) == now

    def test_iso_string(self):
        result = _parse_log_time_bound("2024-06-15T14:30:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 6

    def test_z_suffix(self):
        result = _parse_log_time_bound("2024-06-15T14:30:00Z")
        assert result is not None

    def test_empty_string(self):
        assert _parse_log_time_bound("") is None

    def test_whitespace_string(self):
        assert _parse_log_time_bound("   ") is None

    def test_invalid_string(self):
        assert _parse_log_time_bound("not-a-date") is None

    def test_other_type(self):
        assert _parse_log_time_bound(12345) is None


@pytest.mark.unit
class TestLogService:
    """LogService 测试类。"""

    @pytest.fixture
    def mock_log_repo(self):
        """创建模拟日志仓储。"""
        repo = AsyncMock()
        repo.get_login_logs = AsyncMock(return_value=([], 0))
        repo.delete_login_logs = AsyncMock(return_value=0)
        repo.clear_login_logs = AsyncMock(return_value=0)
        repo.get_operation_logs = AsyncMock(return_value=([], 0))
        repo.delete_operation_logs = AsyncMock(return_value=0)
        repo.clear_operation_logs = AsyncMock(return_value=0)
        repo.get_system_logs = AsyncMock(return_value=([], 0))
        repo.get_system_log_detail = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def log_service(self, mock_log_repo):
        """创建日志服务实例。"""
        return LogService(log_repo=mock_log_repo)

    @pytest.mark.asyncio
    async def test_get_login_logs(self, log_service, mock_log_repo):
        """测试获取登录日志。"""
        log = LoginLogEntity(id="1", status=1, ipaddress="127.0.0.1")
        mock_log_repo.get_login_logs = AsyncMock(return_value=([log], 1))

        query = type("Query", (), {"createdTime": None, "status": None, "pageNum": 1, "pageSize": 10})()
        logs, total = await log_service.get_login_logs(query)
        assert total == 1
        assert len(logs) == 1

    @pytest.mark.asyncio
    async def test_get_login_logs_with_status(self, log_service, mock_log_repo):
        """测试带状态筛选获取登录日志。"""
        mock_log_repo.get_login_logs = AsyncMock(return_value=([], 0))

        query = type("Query", (), {"createdTime": None, "status": "1", "pageNum": 1, "pageSize": 10})()
        await log_service.get_login_logs(query)
        call_kwargs = mock_log_repo.get_login_logs.call_args[1]
        assert call_kwargs["status"] == 1

    @pytest.mark.asyncio
    async def test_get_login_logs_with_time_range(self, log_service, mock_log_repo):
        """测试带时间范围获取登录日志。"""
        mock_log_repo.get_login_logs = AsyncMock(return_value=([], 0))

        query = type("Query", (), {"createdTime": ["2024-01-01T00:00:00", "2024-12-31T23:59:59"], "status": None, "pageNum": 1, "pageSize": 10})()
        await log_service.get_login_logs(query)
        call_kwargs = mock_log_repo.get_login_logs.call_args[1]
        assert call_kwargs["start_time"] is not None
        assert call_kwargs["end_time"] is not None

    @pytest.mark.asyncio
    async def test_delete_login_logs(self, log_service, mock_log_repo):
        """测试批量删除登录日志。"""
        mock_log_repo.delete_login_logs = AsyncMock(return_value=3)
        dto = type("DTO", (), {"ids": ["1", "2", "3"]})()
        result = await log_service.delete_login_logs(dto)
        assert result == 3

    @pytest.mark.asyncio
    async def test_clear_login_logs(self, log_service, mock_log_repo):
        """测试清空登录日志。"""
        mock_log_repo.clear_login_logs = AsyncMock(return_value=10)
        result = await log_service.clear_login_logs()
        assert result == 10

    @pytest.mark.asyncio
    async def test_get_operation_logs(self, log_service, mock_log_repo):
        """测试获取操作日志。"""
        log = OperationLogEntity(id="1", module="用户管理", method="POST")
        mock_log_repo.get_operation_logs = AsyncMock(return_value=([log], 1))

        query = type("Query", (), {"createdTime": None, "status": None, "module": None, "pageNum": 1, "pageSize": 10})()
        logs, total = await log_service.get_operation_logs(query)
        assert total == 1

    @pytest.mark.asyncio
    async def test_delete_operation_logs(self, log_service, mock_log_repo):
        """测试批量删除操作日志。"""
        mock_log_repo.delete_operation_logs = AsyncMock(return_value=2)
        dto = type("DTO", (), {"ids": ["1", "2"]})()
        result = await log_service.delete_operation_logs(dto)
        assert result == 2

    @pytest.mark.asyncio
    async def test_clear_operation_logs(self, log_service, mock_log_repo):
        """测试清空操作日志。"""
        mock_log_repo.clear_operation_logs = AsyncMock(return_value=5)
        result = await log_service.clear_operation_logs()
        assert result == 5

    @pytest.mark.asyncio
    async def test_get_system_logs(self, log_service, mock_log_repo):
        """测试获取系统日志。"""
        mock_log_repo.get_system_logs = AsyncMock(return_value=([], 0))

        query = type("Query", (), {"createdTime": None, "status": None, "module": None, "pageNum": 1, "pageSize": 10})()
        logs, total = await log_service.get_system_logs(query)
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_system_log_detail(self, log_service, mock_log_repo):
        """测试获取系统日志详情。"""
        log = OperationLogEntity(id="1", module="系统")
        mock_log_repo.get_system_log_detail = AsyncMock(return_value=log)

        result = await log_service.get_system_log_detail("1")
        assert result.module == "系统"

    @pytest.mark.asyncio
    async def test_get_system_log_detail_not_found(self, log_service, mock_log_repo):
        """测试获取不存在的系统日志详情。"""
        mock_log_repo.get_system_log_detail = AsyncMock(return_value=None)
        result = await log_service.get_system_log_detail("non-existent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_login_logs_with_time_range(self, log_service, mock_log_repo):
        """测试带时间范围获取登录日志。"""
        mock_log_repo.get_login_logs = AsyncMock(return_value=([], 0))
        query = type("Query", (), {"createdTime": ["2024-01-01T00:00:00", "2024-12-31T23:59:59"], "status": None, "pageNum": 1, "pageSize": 10})()
        await log_service.get_login_logs(query)
        call_kwargs = mock_log_repo.get_login_logs.call_args[1]
        assert call_kwargs["start_time"] is not None
        assert call_kwargs["end_time"] is not None

    @pytest.mark.asyncio
    async def test_get_operation_logs_with_status_and_module(self, log_service, mock_log_repo):
        """测试带状态和模块筛选获取操作日志。"""
        mock_log_repo.get_operation_logs = AsyncMock(return_value=([], 0))
        query = type("Query", (), {"createdTime": None, "status": "200", "module": "用户管理", "pageNum": 1, "pageSize": 10})()
        await log_service.get_operation_logs(query)
        call_kwargs = mock_log_repo.get_operation_logs.call_args[1]
        assert call_kwargs["status_code"] == 200
        assert call_kwargs["module"] == "用户管理"

    @pytest.mark.asyncio
    async def test_get_operation_logs_with_time_range(self, log_service, mock_log_repo):
        """测试带时间范围获取操作日志。"""
        mock_log_repo.get_operation_logs = AsyncMock(return_value=([], 0))
        query = type("Query", (), {"createdTime": ["2024-01-01T00:00:00", "2024-12-31T23:59:59"], "status": None, "module": None, "pageNum": 1, "pageSize": 10})()
        await log_service.get_operation_logs(query)
        call_kwargs = mock_log_repo.get_operation_logs.call_args[1]
        assert call_kwargs["start_time"] is not None
        assert call_kwargs["end_time"] is not None

    @pytest.mark.asyncio
    async def test_get_system_logs_with_status_and_module(self, log_service, mock_log_repo):
        """测试带状态和模块筛选获取系统日志。"""
        mock_log_repo.get_system_logs = AsyncMock(return_value=([], 0))
        query = type("Query", (), {"createdTime": None, "status": "500", "module": "系统", "pageNum": 1, "pageSize": 10})()
        await log_service.get_system_logs(query)
        call_kwargs = mock_log_repo.get_system_logs.call_args[1]
        assert call_kwargs["status_code"] == 500
        assert call_kwargs["module"] == "系统"

    @pytest.mark.asyncio
    async def test_get_system_logs_with_time_range(self, log_service, mock_log_repo):
        """测试带时间范围获取系统日志。"""
        mock_log_repo.get_system_logs = AsyncMock(return_value=([], 0))
        query = type("Query", (), {"createdTime": ["2024-01-01T00:00:00", "2024-12-31T23:59:59"], "status": None, "module": None, "pageNum": 1, "pageSize": 10})()
        await log_service.get_system_logs(query)
        call_kwargs = mock_log_repo.get_system_logs.call_args[1]
        assert call_kwargs["start_time"] is not None
        assert call_kwargs["end_time"] is not None

    @pytest.mark.asyncio
    async def test_each_log_type_returns_data(self, log_service, mock_log_repo):
        """测试各类日志查询返回数据。"""
        login_log = LoginLogEntity(id="1", status=1, ipaddress="127.0.0.1")
        op_log = OperationLogEntity(id="1", module="用户管理", method="POST")
        mock_log_repo.get_login_logs = AsyncMock(return_value=([login_log], 1))
        mock_log_repo.get_operation_logs = AsyncMock(return_value=([op_log], 1))
        mock_log_repo.get_system_logs = AsyncMock(return_value=([op_log], 1))

        q = type("Query", (), {"createdTime": None, "status": None, "module": None, "pageNum": 1, "pageSize": 10})()

        ll, lt = await log_service.get_login_logs(q)
        assert lt == 1

        ol, ot = await log_service.get_operation_logs(q)
        assert ot == 1

        sl, st = await log_service.get_system_logs(q)
        assert st == 1

    @pytest.mark.asyncio
    async def test_delete_operation_logs_return_count(self, log_service, mock_log_repo):
        """测试批量删除操作日志返回计数。"""
        mock_log_repo.delete_operation_logs = AsyncMock(return_value=5)
        dto = type("DTO", (), {"ids": ["1", "2", "3", "4", "5"]})()
        result = await log_service.delete_operation_logs(dto)
        assert result == 5
