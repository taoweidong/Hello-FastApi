"""日志仓储接口的单元测试。

测试 LogRepositoryInterface 抽象基类的方法签名和返回类型。
"""

from datetime import datetime

import pytest

from src.domain.entities.log import LoginLogEntity, OperationLogEntity
from src.domain.repositories.log_repository import LogRepositoryInterface


class ConcreteLogRepository(LogRepositoryInterface):
    """用于测试的 LogRepositoryInterface 最小化具体实现。"""

    def __init__(self, session=None):
        self.session = session

    async def get_login_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        status: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[LoginLogEntity], int]:
        return ([], 0)

    async def create_login_log(self, log: LoginLogEntity) -> LoginLogEntity:
        return log

    async def delete_login_logs(self, log_ids: list[str]) -> int:
        return len(log_ids)

    async def clear_login_logs(self) -> int:
        return 0

    async def get_operation_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        status_code: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        return ([], 0)

    async def create_operation_log(self, log: OperationLogEntity) -> OperationLogEntity:
        return log

    async def get_operation_log_detail(self, log_id: str) -> OperationLogEntity | None:
        return None

    async def delete_operation_logs(self, log_ids: list[str]) -> int:
        return len(log_ids)

    async def clear_operation_logs(self) -> int:
        return 0

    async def get_system_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        status_code: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        return ([], 0)

    async def get_system_log_detail(self, log_id: str) -> OperationLogEntity | None:
        return None


@pytest.mark.unit
class TestLogRepositoryInterface:
    """LogRepositoryInterface 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            LogRepositoryInterface(session=None)  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        repo = ConcreteLogRepository()
        assert repo is not None
        assert isinstance(repo, LogRepositoryInterface)

    # ---- 登录日志 ----

    @pytest.mark.asyncio
    async def test_get_login_logs_returns_tuple(self):
        """测试 get_login_logs 返回元组。"""
        repo = ConcreteLogRepository()
        result = await repo.get_login_logs()
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_login_logs_with_all_params(self):
        """测试 get_login_logs 接受所有可选参数。"""
        repo = ConcreteLogRepository()
        result = await repo.get_login_logs(
            page_num=1,
            page_size=20,
            status=1,
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 12, 31),
        )
        assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_create_login_log_returns_entity(self):
        """测试 create_login_log 返回登录日志实体。"""
        repo = ConcreteLogRepository()
        entity = LoginLogEntity(id="log-1", status=1, ipaddress="127.0.0.1")
        result = await repo.create_login_log(entity)
        assert isinstance(result, LoginLogEntity)

    @pytest.mark.asyncio
    async def test_delete_login_logs_returns_int(self):
        """测试 delete_login_logs 返回整数。"""
        repo = ConcreteLogRepository()
        result = await repo.delete_login_logs(["log-1", "log-2"])
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_clear_login_logs_returns_int(self):
        """测试 clear_login_logs 返回整数。"""
        repo = ConcreteLogRepository()
        result = await repo.clear_login_logs()
        assert isinstance(result, int)

    # ---- 操作日志 ----

    @pytest.mark.asyncio
    async def test_get_operation_logs_returns_tuple(self):
        """测试 get_operation_logs 返回元组。"""
        repo = ConcreteLogRepository()
        result = await repo.get_operation_logs()
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_operation_logs_with_all_params(self):
        """测试 get_operation_logs 接受所有可选参数。"""
        repo = ConcreteLogRepository()
        result = await repo.get_operation_logs(
            page_num=1,
            page_size=20,
            module="user",
            status_code=200,
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 12, 31),
        )
        assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_create_operation_log_returns_entity(self):
        """测试 create_operation_log 返回操作日志实体。"""
        repo = ConcreteLogRepository()
        entity = OperationLogEntity(id="log-1", module="user")
        result = await repo.create_operation_log(entity)
        assert isinstance(result, OperationLogEntity)

    @pytest.mark.asyncio
    async def test_get_operation_log_detail_returns_entity_or_none(self):
        """测试 get_operation_log_detail 返回实体或 None。"""
        repo = ConcreteLogRepository()
        result = await repo.get_operation_log_detail("log-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_operation_logs_returns_int(self):
        """测试 delete_operation_logs 返回整数。"""
        repo = ConcreteLogRepository()
        result = await repo.delete_operation_logs(["log-1"])
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_clear_operation_logs_returns_int(self):
        """测试 clear_operation_logs 返回整数。"""
        repo = ConcreteLogRepository()
        result = await repo.clear_operation_logs()
        assert isinstance(result, int)

    # ---- 系统日志 ----

    @pytest.mark.asyncio
    async def test_get_system_logs_returns_tuple(self):
        """测试 get_system_logs 返回元组。"""
        repo = ConcreteLogRepository()
        result = await repo.get_system_logs()
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_system_logs_with_all_params(self):
        """测试 get_system_logs 接受所有可选参数。"""
        repo = ConcreteLogRepository()
        result = await repo.get_system_logs(
            page_num=1,
            page_size=20,
            module="system",
            status_code=500,
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 12, 31),
        )
        assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_get_system_log_detail_returns_entity_or_none(self):
        """测试 get_system_log_detail 返回实体或 None。"""
        repo = ConcreteLogRepository()
        result = await repo.get_system_log_detail("log-1")
        assert result is None
