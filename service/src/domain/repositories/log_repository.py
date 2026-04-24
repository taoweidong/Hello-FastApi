"""日志领域 - 仓储接口。

定义日志仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from src.domain.entities.log import LoginLogEntity, OperationLogEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class LogRepositoryInterface(ABC):
    """日志的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    # 登录日志
    @abstractmethod
    async def get_login_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        status: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[LoginLogEntity], int]:
        """获取登录日志列表。"""
        ...

    @abstractmethod
    async def create_login_log(self, log: LoginLogEntity) -> LoginLogEntity:
        """创建登录日志。"""
        ...

    @abstractmethod
    async def delete_login_logs(self, log_ids: list[str]) -> int:
        """删除登录日志。"""
        ...

    @abstractmethod
    async def clear_login_logs(self) -> int:
        """清空登录日志。"""
        ...

    # 统一操作日志(sys_logs)
    @abstractmethod
    async def get_operation_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        status_code: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        """获取操作日志列表。"""
        ...

    @abstractmethod
    async def create_operation_log(self, log: OperationLogEntity) -> OperationLogEntity:
        """创建操作日志。"""
        ...

    @abstractmethod
    async def get_operation_log_detail(self, log_id: str) -> OperationLogEntity | None:
        """获取操作日志详情。"""
        ...

    @abstractmethod
    async def delete_operation_logs(self, log_ids: list[str]) -> int:
        """删除操作日志。"""
        ...

    @abstractmethod
    async def clear_operation_logs(self) -> int:
        """清空操作日志。"""
        ...

    # 系统日志(与操作日志共享 sys_logs 表，仅查询)
    @abstractmethod
    async def get_system_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        status_code: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        """获取系统日志列表。"""
        ...

    @abstractmethod
    async def get_system_log_detail(self, log_id: str) -> OperationLogEntity | None:
        """获取系统日志详情。"""
        ...
