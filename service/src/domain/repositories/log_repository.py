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
        username: str | None = None,
    ) -> tuple[list[LoginLogEntity], int]:
        """获取登录日志列表（可按用户名精确过滤，供个人安全日志按登录名查询）。"""
        ...

    @abstractmethod
    async def create_login_log(self, log: LoginLogEntity) -> LoginLogEntity:
        """创建登录日志。"""
        ...

    @abstractmethod
    async def list_login_log_times(self, start_time: datetime, status: int | None = None) -> list[datetime]:
        """列出起始时间之后的登录日志 created_time（仅时间列，供仪表盘按日分桶）。

        Args:
            start_time: 起始时间（含边界，created_time >= start_time）
            status: 登录状态过滤（None 表示不过滤；1 为成功，语义见 LoginLogEntity）

        Returns:
            登录发生时间列表（created_time 为空的行跳过）
        """
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
        before_time: datetime | None = None,
        before_id: str | None = None,
        total: int | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        """获取操作日志列表。

        分页语义：
        - before_time/before_id 同时提供时走 keyset 游标分页：
          ``(created_time, id) < (before_time, before_id)`` 行比较 + limit，
          深分页不再 offset 全扫（调用方经 total 参数传入缓存的总数，跳过 COUNT）；
        - 否则走传统 offset 分页（page_num/page_size），完全向后兼容；
        - total 为 None 时仓储内部执行精确 COUNT，否则跳过 COUNT 复用传入值。
        """
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
    async def list_operation_log_stamps(self, start_time: datetime) -> list[tuple[datetime, str | None]]:
        """列出起始时间之后的操作日志 (created_time, module) 轻量行。

        仅取时间与模块两列，供仪表盘"近 7 天操作分布"在 Python 侧做
        跨方言分桶聚合（避免 GROUP BY 日期函数的 SQLite/PG 方言差异）。

        Args:
            start_time: 起始时间（含边界，created_time >= start_time）

        Returns:
            (created_time, module) 元组列表（created_time 为空的行跳过）
        """
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
        before_time: datetime | None = None,
        before_id: str | None = None,
        total: int | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        """获取系统日志列表（分页/游标语义与 get_operation_logs 一致）。"""
        ...

    @abstractmethod
    async def get_system_log_detail(self, log_id: str) -> OperationLogEntity | None:
        """获取系统日志详情。"""
        ...
