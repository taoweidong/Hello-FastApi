"""LogRepository 单元测试。"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.log import LoginLogEntity, OperationLogEntity
from src.infrastructure.repositories.log_repository import LogRepository


@pytest.mark.unit
class TestLogRepository:
    """LogRepository 测试类。"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return LogRepository(mock_session)

    def test_init(self, repo, mock_session):
        """测试初始化设置 session 和两个 crud。"""
        assert repo.session is mock_session
        assert repo._login_log_crud is not None
        assert repo._system_log_crud is not None

    # ============ 登录日志 ============

    @pytest.mark.asyncio
    async def test_get_login_logs(self, repo, mock_session):
        """测试 get_login_logs 返回分页登录日志。"""
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.to_domain.return_value = LoginLogEntity(id="1", status=1)
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_login_logs(page_num=1, page_size=10, status=1)
        assert len(logs) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_login_logs_with_date_filters(self, repo, mock_session):
        """测试 get_login_logs 带时间筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_login_logs(start_time=datetime(2024, 1, 1), end_time=datetime(2024, 12, 31))
        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_create_login_log(self, repo, mock_session):
        """测试 create_login_log 创建登录日志。"""
        entity = LoginLogEntity(id="1", status=1)
        mock_model = MagicMock()
        mock_model.id = "1"
        mock_model.to_domain.return_value = entity

        with patch("src.infrastructure.repositories.log_repository.LoginLog.from_domain", return_value=mock_model):
            mock_session.get = AsyncMock(return_value=mock_model)
            result = await repo.create_login_log(entity)

        assert result is not None
        assert result.id == "1"

    @pytest.mark.asyncio
    async def test_delete_login_logs(self, repo, mock_session):
        """测试 delete_login_logs 批量删除。"""
        mock_result = MagicMock()
        mock_result.rowcount = 2
        mock_session.execute.return_value = mock_result

        count = await repo.delete_login_logs(["1", "2"])
        assert count == 2

    @pytest.mark.asyncio
    async def test_delete_login_logs_empty(self, repo):
        """测试 delete_login_logs 空列表返回 0。"""
        count = await repo.delete_login_logs([])
        assert count == 0

    @pytest.mark.asyncio
    async def test_clear_login_logs(self, repo, mock_session):
        """测试 clear_login_logs 清空所有登录日志。"""
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 10
        mock_session.execute.return_value = mock_count

        total = await repo.clear_login_logs()
        assert total == 10

    # ============ 操作日志 ============

    @pytest.mark.asyncio
    async def test_get_operation_logs(self, repo, mock_session):
        """测试 get_operation_logs 返回操作日志。"""
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.to_domain.return_value = OperationLogEntity(id="1", module="user", method="POST")
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_operation_logs(module="user", status_code=200)
        assert len(logs) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_create_operation_log(self, repo, mock_session):
        """测试 create_operation_log 创建操作日志。"""
        entity = OperationLogEntity(id="1", module="user", method="POST")
        mock_model = MagicMock()
        mock_model.id = "1"
        mock_model.to_domain.return_value = entity

        with patch("src.infrastructure.repositories.log_repository.SystemLog.from_domain", return_value=mock_model):
            mock_session.get = AsyncMock(return_value=mock_model)
            result = await repo.create_operation_log(entity)

        assert result is not None
        assert result.id == "1"

    @pytest.mark.asyncio
    async def test_get_operation_log_detail_found(self, repo):
        """测试 get_operation_log_detail 找到日志。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = OperationLogEntity(id="1", module="user")
        repo._system_log_crud.get = AsyncMock(return_value=mock_model)

        result = await repo.get_operation_log_detail("1")
        assert result is not None
        assert result.id == "1"

    @pytest.mark.asyncio
    async def test_get_operation_log_detail_not_found(self, repo):
        """测试 get_operation_log_detail 未找到返回 None。"""
        repo._system_log_crud.get = AsyncMock(return_value=None)

        result = await repo.get_operation_log_detail("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_operation_logs(self, repo, mock_session):
        """测试 delete_operation_logs 批量删除。"""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.execute.return_value = mock_result

        count = await repo.delete_operation_logs(["1", "2", "3"])
        assert count == 3

    @pytest.mark.asyncio
    async def test_delete_operation_logs_empty(self, repo):
        """测试 delete_operation_logs 空列表返回 0。"""
        count = await repo.delete_operation_logs([])
        assert count == 0

    @pytest.mark.asyncio
    async def test_clear_operation_logs(self, repo, mock_session):
        """测试 clear_operation_logs 清空操作日志。"""
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_count

        total = await repo.clear_operation_logs()
        assert total == 5

    # ============ 系统日志 ============

    @pytest.mark.asyncio
    async def test_get_system_logs(self, repo, mock_session):
        """测试 get_system_logs 返回系统日志。"""
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.to_domain.return_value = OperationLogEntity(id="1", module="auth")
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_system_logs(module="auth", status_code=500)
        assert len(logs) == 1

    @pytest.mark.asyncio
    async def test_get_system_log_detail_found(self, repo, mock_session):
        """测试 get_system_log_detail 找到日志。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = OperationLogEntity(id="1", module="auth")
        mock_session.get = AsyncMock(return_value=mock_model)

        result = await repo.get_system_log_detail("1")
        assert result is not None
        assert result.id == "1"

    @pytest.mark.asyncio
    async def test_get_system_log_detail_not_found(self, repo, mock_session):
        """测试 get_system_log_detail 未找到返回 None。"""
        mock_session.get = AsyncMock(return_value=None)

        result = await repo.get_system_log_detail("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_login_logs_no_filters(self, repo, mock_session):
        """测试 get_login_logs 无筛选条件。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_login_logs()

        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_login_logs_status_only(self, repo, mock_session):
        """测试 get_login_logs 仅按状态筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_login_logs(status=1)

        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_operation_logs_no_filters(self, repo, mock_session):
        """测试 get_operation_logs 无筛选条件。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_operation_logs()

        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_operation_logs_module_only(self, repo, mock_session):
        """测试 get_operation_logs 仅按模块筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_operation_logs(module="user")

        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_operation_logs_status_code_only(self, repo, mock_session):
        """测试 get_operation_logs 仅按状态码筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_operation_logs(status_code=200)

        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_system_logs_no_filters(self, repo, mock_session):
        """测试 get_system_logs 无筛选条件。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_system_logs()

        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_operation_logs_start_time(self, repo, mock_session):
        """测试 get_operation_logs 按开始时间筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_operation_logs(start_time=datetime(2024, 1, 1))

        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_operation_logs_end_time(self, repo, mock_session):
        """测试 get_operation_logs 按结束时间筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_operation_logs(end_time=datetime(2024, 12, 31))

        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_system_logs_start_time(self, repo, mock_session):
        """测试 get_system_logs 按开始时间筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_system_logs(start_time=datetime(2024, 1, 1))

        assert logs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_system_logs_end_time(self, repo, mock_session):
        """测试 get_system_logs 按结束时间筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count

        logs, total = await repo.get_system_logs(end_time=datetime(2024, 12, 31))

        assert logs == []
        assert total == 0
