"""日志领域 - 仓储接口。

定义日志仓储的抽象接口，遵循依赖倒置原则。
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from src.infrastructure.database.models import LoginLog, OperationLog, SystemLog


class LogRepositoryInterface:
    """日志仓储的抽象接口（非强制继承，仅作为类型参考）。"""

    # ============ 登录日志相关 ============

    async def get_login_logs(
        self,
        session: AsyncSession,
        page_num: int = 1,
        page_size: int = 10,
        username: str | None = None,
        status: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list["LoginLog"], int]:
        """获取登录日志列表。

        Args:
            session: 数据库会话
            page_num: 页码
            page_size: 每页数量
            username: 用户名过滤
            status: 状态过滤
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            (日志列表, 总数) 元组
        """
        ...

    async def delete_login_logs(self, session: AsyncSession, log_ids: list[str]) -> int:
        """批量删除登录日志。

        Args:
            session: 数据库会话
            log_ids: 日志ID列表

        Returns:
            删除的记录数
        """
        ...

    async def clear_login_logs(self, session: AsyncSession) -> int:
        """清空所有登录日志。

        Args:
            session: 数据库会话

        Returns:
            删除的记录数
        """
        ...

    # ============ 操作日志相关 ============

    async def get_operation_logs(
        self,
        session: AsyncSession,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        status: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list["OperationLog"], int]:
        """获取操作日志列表。

        Args:
            session: 数据库会话
            page_num: 页码
            page_size: 每页数量
            module: 模块过滤
            status: 状态过滤
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            (日志列表, 总数) 元组
        """
        ...

    async def delete_operation_logs(self, session: AsyncSession, log_ids: list[str]) -> int:
        """批量删除操作日志。

        Args:
            session: 数据库会话
            log_ids: 日志ID列表

        Returns:
            删除的记录数
        """
        ...

    async def clear_operation_logs(self, session: AsyncSession) -> int:
        """清空所有操作日志。

        Args:
            session: 数据库会话

        Returns:
            删除的记录数
        """
        ...

    # ============ 系统日志相关 ============

    async def get_system_logs(
        self,
        session: AsyncSession,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list["SystemLog"], int]:
        """获取系统日志列表。

        Args:
            session: 数据库会话
            page_num: 页码
            page_size: 每页数量
            module: 模块过滤
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            (日志列表, 总数) 元组
        """
        ...

    async def get_system_log_detail(self, session: AsyncSession, log_id: str) -> "SystemLog | None":
        """获取系统日志详情。

        Args:
            session: 数据库会话
            log_id: 日志ID

        Returns:
            日志对象或 None
        """
        ...

    async def delete_system_logs(self, session: AsyncSession, log_ids: list[str]) -> int:
        """批量删除系统日志。

        Args:
            session: 数据库会话
            log_ids: 日志ID列表

        Returns:
            删除的记录数
        """
        ...

    async def clear_system_logs(self, session: AsyncSession) -> int:
        """清空所有系统日志。

        Args:
            session: 数据库会话

        Returns:
            删除的记录数
        """
        ...
